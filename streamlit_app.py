import streamlit as st

st.set_page_config(
    page_title="Assimilation Tracker",  # <- this sets the browser tab title
    page_icon="📋",             # <- optional emoji icon for the tab
    layout="wide",              # <- full width layout
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Assimilation Tracker",  # <- this sets the browser tab title
    page_icon="📋",             # <- optional emoji icon for the tab
    layout="wide",              # <- full width layout
)


# --- Helper to render a pie chart ---
def render_pie_chart(checked_count, total_count, title):
    fig, ax = plt.subplots(figsize=(1.5, 1.5))
    ax.pie(
        [checked_count, total_count - checked_count],
        #labels=["✔", ""],
        colors=["#4CAF50", "#e0e0e0"],
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.4)
    )
    ax.set_title(f"{title}\n{int((checked_count / total_count) * 100)}%", fontsize=10)
    return fig

# --- Load Google Sheet ---
@st.cache_data
def load_data():
    creds_dict = st.secrets["google_service_account"]
    with open("/tmp/creds.json", "w") as f:
        json.dump(dict(creds_dict), f)

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("/tmp/creds.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("COHO Assimilation Tracker").worksheet("Sheet1")
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# --- Load Data ---
df = load_data()
st.title("COHO Assimilation Tracker")
# Load base64 logo (once)
with open("images/logo_base64.txt") as f:
    logo_base64 = f.read()
st.markdown(
    f"""
    <style>
    .logo-container {{
        position: fixed;
        top: 0px;
        right: 0px;
        padding: 20px;
        z-index: 100;
    }}
    </style>
    <div class="logo-container">
        <img src="data:image/png;base64,{logo_base64}" width="150">
    </div>
    """,
    unsafe_allow_html=True
)




if not df.empty and "Name" in df.columns:
    selected_name = st.selectbox("Please select a name", sorted(df["Name"].dropna().unique()))

    if selected_name:
        person_row = df[df["Name"] == selected_name].reset_index(drop=True)

        # --- Section Field Definitions ---
        connect_fields = {
            "J+ call and/or meet for coffee": "J+ has called and/or met them for coffee",
            "Danni or other, initial reach out": "Danni has completed an initial reach-out",
            "Jaime invite to COHO event": "Jaime has invited them to a COHO event",
            "Vesper Group (like Compline) (J+, etc.)": "Vesper Group (like Compline) (J+, etc.)",
            "J+ connect with Vesper Group Leader (VGL)": "J+ has connected them with a Vesper Group Leader (VGL)"
        }

        include_fields = {
            "J+ add to a Church Slack (R=request sent)": "J+ add to a Church Slack (R=request sent)",
            "J+ send Onboarding Survey (OS)": "J+ send Onboarding Survey (OS)",
            "mark if OS complete": "mark if OS complete",
            "add to Parent’s Guild Slack channel (if applicable)": "add to Parent’s Guild Slack channel (if applicable)",
            "place family on a Liturgy Team Rotation (using info from OS)": "place family on a Liturgy Team Rotation (using info from OS)",
            "print nametag": "print nametag",
            "Admin check-in (to keep moving forward)": "Admin check-in (to keep moving forward)"
        }

        commit_fields = {
            "J+ pastoral interview": "J+ pastoral interview",
            "take photo and input in Directory": "take photo and input in Directory",
            "get all info in Directory": "get all info in Directory",
            "Confirmed? (Y/N)": "Confirmed? (Y/N)",
            "Place into confirmation class, if applicable": "Place into confirmation class, if applicable",
            "Transfer Complete": "Transfer Complete"
        }

        # --- Section Rendering ---
        all_states = {}

        for section_name, field_dict in [
            ("Connect", connect_fields),
            ("Include", include_fields),
            ("Commit", commit_fields),
        ]:
            st.subheader(f"{section_name} Details for {selected_name}")
            checkbox_states = {}
            checked_count = 0

            col1, col2 = st.columns([3, 1])
            with col1:
                for col_key, label in field_dict.items():
                    current = person_row.at[0, col_key] if col_key in person_row.columns else ""
                    checked = st.checkbox(label, value=(str(current).strip().upper() == "X"), key=col_key)
                    checkbox_states[col_key] = checked
                    if checked:
                        checked_count += 1
            with col2:
                st.pyplot(render_pie_chart(checked_count, len(field_dict), section_name))

            all_states.update(checkbox_states)

        # --- Update Button ---
        if st.button("Update Google Sheet"):
            try:
                creds = ServiceAccountCredentials.from_json_keyfile_name("/tmp/creds.json", [
                    "https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"
                ])
                client = gspread.authorize(creds)
                sheet = client.open("COHO Assimilation Tracker").worksheet("Sheet1")
                sheet_data = sheet.get_all_values()
                header = sheet_data[0]

                name_col_index = header.index("Name")
                update_row = next((i for i, row in enumerate(sheet_data[1:], start=2) if row[name_col_index] == selected_name), None)

                if update_row:
                    for col_key, checked in all_states.items():
                        if col_key in header:
                            col_index = header.index(col_key)
                            new_value = "X" if checked else ""
                            sheet.update_cell(update_row, col_index + 1, new_value)
                    st.success("Sheet updated successfully!")
                else:
                    st.error("Could not find the matching row to update.")
            except Exception as e:
                st.error(f"Update failed: {e}")
else:
    st.warning("No data loaded or 'Name' column not found.")

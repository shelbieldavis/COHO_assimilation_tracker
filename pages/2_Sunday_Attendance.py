import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
import plotly.graph_objects as go

# --- Load Attendance Sheet ---
@st.cache_data
def load_attendance_data():
    creds_dict = st.secrets["google_service_account"]
    with open("/tmp/creds_attendance.json", "w") as f:
        json.dump(dict(creds_dict), f)

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("/tmp/creds_attendance.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("COHO Sunday Attendance").worksheet("Sheet1")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df

# --- Load and clean data ---
df = load_attendance_data()
df = df.dropna(subset=["Date", "Attendees"])

# Load base64 logo (once)
with open("images/logo_base64.txt") as f:
    logo_base64 = f.read()
col1, col2 = st.columns([6, 1])
with col1:
    st.title("COHO Sunday Attendance")
with col2:
    st.markdown(
        f"""
        <div style="text-align: right; padding-top: 0.5rem;">
            <img src="data:image/png;base64,{logo_base64}" width="120">
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Create plot ---
fig = go.Figure()

# Line with fill
# Add green line trace with fill and markers
fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Attendees"],
    mode="lines+markers+text",  # <- show line, points, and text
    line=dict(color="green"),
    fill="tozeroy",
    fillcolor="rgba(76,175,80,0.3)",
    text=df["Attendees"],            # <- use attendance values as text
    textposition="top center",       # <- position above marker
    marker=dict(size=6),
    name="Attendees"
))

# Markers with value labels
fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["Attendees"],
    mode="markers+text",
    marker=dict(color="green", size=6),
    text=df["Attendees"],
    textposition="top center",
    name="Entry Points",
    showlegend=False
))

# Calculate dynamic y-axis range with padding
y_min = 0
y_max = df["Attendees"].max()
y_padding = (y_max - y_min) * 0.1  # 10% padding

fig.update_layout(
    title=dict(
        text="COHO Sunday Attendance Over Time",
        y=0.99,
        x=0.5,
        xanchor="center",
        yanchor="top"
    ),
    margin=dict(t=80, b=100),  # Add extra bottom margin for slider + labels
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(
            visible=True,
            thickness=0.1
        ),
        type="date"
    ),
    yaxis=dict(
        title="Attendance",
        range=[y_min - y_padding, y_max + y_padding]
    )
)



# Display in Streamlit
st.plotly_chart(fig, use_container_width=True)

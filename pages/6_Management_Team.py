import streamlit as st
import pandas as pd
import numpy as np
import datetime
import openai
import os

st.title("Management Team – Initiative Tracker, KPI Impact & AI Review")

# --- Step 1: Define/load KPI data ---
dates = pd.date_range("2024-07-01", periods=10)
kpi_df = pd.DataFrame({
    "Date": dates,
    "Sales": np.linspace(100, 120, 10),
    "Production": np.linspace(200, 225, 10),
    "Website_Visits": np.linspace(1500, 1750, 10),
    "NPS": np.linspace(55, 65, 10),
    "Churn": np.linspace(8, 6, 10),
    "Margin": np.linspace(17, 20, 10)
})

# --- Step 2: Define base initiatives (add dynamically) ---
if "initiatives" not in st.session_state:
    st.session_state.initiatives = [
        {"Name": "Launch Product A", "KPI": "Sales", "Impact": 6, "Day": "2024-07-06", "Complete": False},
        {"Name": "Cost Program", "KPI": "Margin", "Impact": 1, "Day": "2024-07-08", "Complete": False},
        {"Name": "Website Campaign", "KPI": "Website_Visits", "Impact": 80, "Day": "2024-07-07", "Complete": False}
    ]

st.header("1. Initiative Tracker (add or mark complete)")
init_names = [i["Name"] for i in st.session_state.initiatives]
cols = st.columns(len(st.session_state.initiatives) + 1)
for idx, init in enumerate(st.session_state.initiatives):
    if cols[idx].checkbox(f"{init['Name']} ({init['KPI']})", value=init["Complete"]):
        st.session_state.initiatives[idx]["Complete"] = True
    else:
        st.session_state.initiatives[idx]["Complete"] = False

with cols[-1]:
    with st.form("add_init"):
        st.write("Add new initiative:")
        name = st.text_input("Name")
        kpi_choice = st.selectbox("KPI", ["Sales", "Production", "Website_Visits", "NPS", "Churn", "Margin"], key="kpi_sel")
        impact = st.number_input("Expected Impact (abs value for KPI, negative for Churn)", value=1.0, step=0.1)
        day = st.date_input("Effective Day", value=datetime.date(2024, 7, 10))
        submitted = st.form_submit_button("Add Initiative")
        if submitted and name and kpi_choice:
            st.session_state.initiatives.append({"Name": name, "KPI": kpi_choice, "Impact": impact, "Day": str(day), "Complete": False})

# --- Step 3: Simulate impact of completed initiatives ---
kpi_sim = kpi_df.copy()
today = pd.to_datetime("2024-07-10")
applied = []
for init in st.session_state.initiatives:
    if init["Complete"]:
        day = pd.to_datetime(init["Day"])
        mask = kpi_sim["Date"] >= day
        if init["KPI"] == "Churn":
            kpi_sim.loc[mask, init["KPI"]] = kpi_sim.loc[mask, init["KPI"]] - abs(init["Impact"])
        else:
            kpi_sim.loc[mask, init["KPI"]] = kpi_sim.loc[mask, init["KPI"]] + init["Impact"]
        applied.append(f"{init['Name']} ({init['KPI']} +{init['Impact']}) on {init['Day']}")

# --- Step 4: KPI trend charts with overlays ---
st.header("2. KPI Trends (w/ Initiative Impact)")
kpi_cols = st.multiselect("Show KPIs", ["Sales", "Production", "Website_Visits", "NPS", "Churn", "Margin"], default=["Sales", "Website_Visits"])
chart_data = kpi_sim.set_index("Date")[kpi_cols]
st.line_chart(chart_data)

# Overlay annotation
for event in applied:
    st.info(f"Applied: {event}")

# --- Step 5: Download tracker/dashboard ---
st.header("3. Download KPI/Initiative Tracker")
download_df = kpi_sim.copy()
download_df["Applied Initiatives"] = ", ".join(applied)
st.download_button("Download Tracker (CSV)", data=download_df.to_csv(), file_name="mgmt_kpi_tracker.csv")

# --- Step 6: LLM-powered management review ---
st.header("4. AI Management Review")
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    st.write(f"API Key detected: {api_key[:8]}...")
    client = openai.OpenAI(api_key=api_key)
else:
    st.error("No API key found in environment. Please set OPENAI_API_KEY.")

persona = st.selectbox("AI Persona", ["CEO", "COO", "CRO"], index=0)
if st.button(f"Ask AI {persona} for Management Review"):
    summary = (
        f"KPI trends: {chart_data.iloc[-3:].round(1).to_dict()}\n"
        f"Completed initiatives: {applied}\n"
        f"All initiatives: {[i for i in st.session_state.initiatives]}"
    )
    persona_prompts = {
        "CEO": "You are the CEO, reviewing the initiative tracker and KPI trends for board.",
        "COO": "You are the COO, prioritizing execution and next steps.",
        "CRO": "You are the CRO, focusing on revenue, growth, and pipeline."
    }
    prompt = (
        persona_prompts[persona] + "\n"
        "Given the data and initiatives below, answer:\n"
        "1. What KPIs are tracking/not tracking?\n"
        "2. Which initiatives are driving results?\n"
        "3. Suggest 2-3 next management or board actions.\n"
        f"Summary: {summary}\n"
        "Write in a concise, board-oriented style."
    )
    with st.spinner("AI persona reviewing..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": persona_prompts[persona]},
                    {"role": "user", "content": prompt}
                ]
            )
            llm_narrative = response.choices[0].message.content.strip()
            st.markdown(f"**AI {persona} Review:**\n\n{llm_narrative}")
        except Exception as e:
            st.error(f"OpenAI API error: {e}")

st.markdown("""
---
**How to use:**  
1. Mark initiatives as complete, or add your own.  
2. Review KPI trends with initiative overlays.  
3. Download tracker or get a CEO/COO/CRO AI management review!
""")
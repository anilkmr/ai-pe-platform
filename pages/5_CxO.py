import streamlit as st
import pandas as pd
import numpy as np
import openai
import os

st.title("CxO – KPI Control Tower, Resource Reallocation & AI Review")

# --- Step 1: Baseline KPIs and functions ---
kpi_df = pd.DataFrame({
    "KPI": ["Revenue", "EBITDA", "NPS", "Churn", "Cash Conversion"],
    "Current": [12.5, 3.1, 65, 6.5, 74],
    "Target": [15, 3.8, 72, 5, 82]
}).set_index("KPI")

func_df = pd.DataFrame({
    "Function": ["Sales", "Marketing", "Product", "Ops", "Service"],
    "Current_Budget": [500, 300, 200, 180, 120],
    "Target_Budget": [600, 340, 250, 220, 150],
    "Current_Output": [80, 40, 30, 35, 33],
    "Target_Output": [100, 60, 50, 50, 44]
}).set_index("Function")

total_budget = int(func_df["Current_Budget"].sum())
st.subheader("KPI Progress & Traffic Lights")
cols = st.columns(len(kpi_df))
for i, row in kpi_df.iterrows():
    pct = int((row["Current"] / row["Target"]) * 100)
    color = "green" if pct >= 100 else ("orange" if pct >= 90 else "red")
    cols[list(kpi_df.index).index(i)].metric(i, f"{row['Current']}", f"Target: {row['Target']}", delta_color="inverse" if i=="Churn" else "normal")
    if color == "green":
        cols[list(kpi_df.index).index(i)].success("●")
    elif color == "orange":
        cols[list(kpi_df.index).index(i)].warning("●")
    else:
        cols[list(kpi_df.index).index(i)].error("●")

# --- Step 2: Macro/Persona Toggles ---
st.header("1. Scenario Levers & Behavior")
macro = st.selectbox("Macro/Market Scenario", ["Normal", "Mild Recession", "Severe Recession"], index=0)
cost_control = st.checkbox("Aggressive Cost Control", value=True)
incremental_invest = st.checkbox("Incremental Growth Investment", value=False)

# --- Step 3: Resource Allocation & Forecasts ---
st.header("2. Resource Allocation Simulator")
st.write(f"Total available budget: **{total_budget}**")
alloc = {}
for f in func_df.index:
    alloc[f] = st.slider(f"{f} Budget", min_value=0, max_value=int(total_budget), value=int(func_df.loc[f, "Current_Budget"]), step=10)
if sum(alloc.values()) > total_budget:
    st.error("Allocated budget exceeds available! Reduce some sliders.")

# --- Forecast function output and KPI impact based on allocation ---
sim_out = {}
kpi_impact = kpi_df["Current"].copy()
# Heuristic rules for simulation
for f in func_df.index:
    base = func_df.loc[f, "Current_Output"]
    target = func_df.loc[f, "Target_Output"]
    base_budget = func_df.loc[f, "Current_Budget"]
    new_budget = alloc[f]
    scale = (new_budget / base_budget) if base_budget > 0 else 0
    out = min(base + (target - base) * scale, target * 1.25)
    sim_out[f] = round(out, 1)

# Map functional output to KPI (simple mapping, e.g., Sales/Marketing -> Revenue/NPS, etc.)
kpi_impact["Revenue"] += 0.07 * (sim_out["Sales"] + sim_out["Marketing"] - func_df.loc["Sales", "Current_Output"] - func_df.loc["Marketing", "Current_Output"])
kpi_impact["EBITDA"] += 0.04 * (sim_out["Ops"] - func_df.loc["Ops", "Current_Output"])
kpi_impact["NPS"] += 0.10 * (sim_out["Product"] - func_df.loc["Product", "Current_Output"]) + 0.04 * (sim_out["Service"] - func_df.loc["Service", "Current_Output"])
kpi_impact["Churn"] -= 0.02 * (sim_out["Service"] - func_df.loc["Service", "Current_Output"])
kpi_impact["Cash Conversion"] += 0.03 * (sim_out["Ops"] + sim_out["Product"] - func_df.loc["Ops", "Current_Output"] - func_df.loc["Product", "Current_Output"])

# Macro/behavior effect
if macro == "Mild Recession":
    kpi_impact["Revenue"] *= 0.97
    kpi_impact["EBITDA"] *= 0.97
    kpi_impact["Churn"] += 0.7
if macro == "Severe Recession":
    kpi_impact["Revenue"] *= 0.94
    kpi_impact["EBITDA"] *= 0.93
    kpi_impact["Churn"] += 1.8
if cost_control:
    kpi_impact["EBITDA"] *= 1.03
    kpi_impact["Cash Conversion"] *= 1.01
if incremental_invest:
    kpi_impact["Revenue"] *= 1.03
    kpi_impact["NPS"] += 0.7

kpi_impact = kpi_impact.round(2)
st.header("3. Simulated Outputs")
sim_dashboard = pd.DataFrame({
    "Current": kpi_df["Current"],
    "Target": kpi_df["Target"],
    "Simulated": kpi_impact
})
st.dataframe(sim_dashboard)
sim_func = pd.DataFrame({"Allocated Budget": alloc, "Projected Output": sim_out, "Target Output": func_df["Target_Output"]})
st.dataframe(sim_func)

# --- Step 4: Download CxO dashboard ---
st.header("4. Download Dashboard")
st.download_button("Download Dashboard (CSV)", data=sim_dashboard.to_csv(), file_name="cxo_dashboard.csv")

# --- Step 5: AI persona scenario review ---
st.header("5. AI CxO Scenario Review")
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    st.write(f"API Key detected: {api_key[:8]}...")
    client = openai.OpenAI(api_key=api_key)
else:
    st.error("No API key found in environment. Please set OPENAI_API_KEY.")

persona = st.selectbox("CxO Persona", ["CEO", "CFO", "COO"], index=0)
if st.button(f"Ask AI {persona} for Scenario Review"):
    summary = (
        f"Scenario: Macro: {macro}, Cost Control: {cost_control}, Incremental Invest: {incremental_invest}\n"
        f"Allocated Budgets: {alloc}\n"
        f"Projected functional outputs: {sim_func['Projected Output'].to_dict()}\n"
        f"KPI Impact: {kpi_impact.to_dict()}\n"
        f"Dashboard: {sim_dashboard.round(2).to_dict()}\n"
    )
    persona_prompts = {
        "CEO": "You are the CEO of a portfolio company, reviewing scenario simulation and resource allocation.",
        "CFO": "You are the CFO, prioritizing financial discipline and risk.",
        "COO": "You are the COO, focusing on execution and ops levers."
    }
    prompt = (
        persona_prompts[persona] + "\n"
        "Given the scenario and dashboard below, answer:\n"
        "1. What KPIs are at risk/off-track, and what stands out?\n"
        "2. Suggest 2-3 practical moves for the exec team or board.\n"
        "3. Any risks or additional analyses needed if macro worsens?\n"
        f"Scenario summary: {summary}\n"
        "Be practical, board-oriented, and concise."
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
1. Adjust resource allocation, scenario, and behaviors.  
2. Review traffic light KPIs and projected outputs.  
3. Download dashboard or get CEO/CFO/COO AI persona guidance!
""")
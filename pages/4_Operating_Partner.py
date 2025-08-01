import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import openai
import os

st.title("Operating Partner – KPI Dashboard, Simulation, Monte Carlo & AI Review")

# --- Step 1: Load/define baseline data ---
baseline = pd.DataFrame({
    "KPI": ["Revenue", "EBITDA", "Churn", "NPS", "Cash Conversion"],
    "Current": [120, 24, 7, 60, 72],
    "Target": [140, 31, 5, 70, 80]
}).set_index("KPI")

# --- Step 2: Value lever controls ---
st.header("1. Value Lever Simulation")
st.write("Simulate impact by adjusting value levers below:")
pricing = st.slider("Pricing Initiative (% Revenue Impact)", 0, 15, 0)
cost_takeout = st.slider("Cost Takeout (% EBITDA Impact)", 0, 20, 0)
success = st.slider("Customer Success (% Churn Reduction)", 0, 10, 0)
automation = st.slider("Automation (% EBITDA + NPS)", 0, 10, 0)
wc = st.slider("Working Capital Optimization (% Cash Conversion)", 0, 10, 0)

# Persona/behavior toggles
st.header("2. Persona/Behavior Logic")
mgmt_aggressive = st.checkbox("Mgmt: Aggressive on Cost in Downturn", value=True)
cx_aggressive = st.checkbox("Customer Success Push in High Churn", value=True)
market_shock = st.selectbox("Market Scenario", ["Normal", "Mild Recession", "Severe Recession"], index=0)

# --- Step 3: Simulate new KPIs based on levers/behaviors ---
future = baseline["Current"].copy()
effects = []

# Pricing
future["Revenue"] *= (1 + pricing/100)
if pricing > 5:
    future["Churn"] += 0.5  # Small backlash
    effects.append("Some churn backlash from higher pricing.")

# Cost takeout and automation
future["EBITDA"] *= (1 + (cost_takeout + automation)/100)
if mgmt_aggressive and market_shock != "Normal":
    future["EBITDA"] *= 1.04  # Extra bump if in stress

# Customer Success
future["Churn"] = max(future["Churn"] - success, 3)
if cx_aggressive and future["Churn"] > 8:
    future["Churn"] = max(future["Churn"] - 1.2, 2)
    effects.append("Customer success initiative reduced churn in stress.")

# NPS and cash conversion
future["NPS"] += automation  # Automation also helps NPS
future["Cash Conversion"] *= (1 + wc/100)

# Macro scenarios
if market_shock == "Mild Recession":
    future["Revenue"] *= 0.98
    future["EBITDA"] *= 0.96
    future["Churn"] += 0.5
    effects.append("Revenue/EBITDA drag and churn up in mild recession.")
elif market_shock == "Severe Recession":
    future["Revenue"] *= 0.95
    future["EBITDA"] *= 0.90
    future["Churn"] += 1.2
    effects.append("Severe recession hits revenue/EBITDA, churn spikes.")

# --- Step 4: KPI dashboard ---
st.header("3. KPI Dashboard: Baseline, Target, Simulated")
dashboard = pd.DataFrame({
    "Current": baseline["Current"],
    "Target": baseline["Target"],
    "Simulated": future.round(2)
})
st.dataframe(dashboard)

st.write("Simulated value lever/market scenario effects:")
for e in effects:
    st.info(e)

# --- Step 5: Monte Carlo scenario for next 12 months ---
st.header("4. Monte Carlo: Operating Band Simulation")
kpi_choice = st.selectbox("KPI to simulate", ["Revenue", "EBITDA", "Churn", "NPS", "Cash Conversion"], index=0)
mc_runs = st.number_input("Monte Carlo Simulations", 100, 2000, 500)
run_mc = st.button("Run Monte Carlo")

if run_mc:
    st.session_state.op_mc_done = True
    kpi_val = future[kpi_choice]
    kpi_std = max(0.02 * kpi_val, 0.5)  # Set some minimum noise
    if market_shock == "Severe Recession":
        kpi_std *= 1.7
    elif market_shock == "Mild Recession":
        kpi_std *= 1.3
    mc_results = np.random.normal(kpi_val, kpi_std, int(mc_runs))
    p25, p50, p75 = np.percentile(mc_results, [25, 50, 75])
    st.session_state.mc_results = {
        "mc_results": mc_results, "p25": p25, "p50": p50, "p75": p75, "kpi_choice": kpi_choice, "kpi_val": kpi_val
    }

if st.session_state.get("op_mc_done", False):
    mc_results = st.session_state["mc_results"]["mc_results"]
    p25 = st.session_state["mc_results"]["p25"]
    p50 = st.session_state["mc_results"]["p50"]
    p75 = st.session_state["mc_results"]["p75"]
    kpi_choice = st.session_state["mc_results"]["kpi_choice"]
    kpi_val = st.session_state["mc_results"]["kpi_val"]
    st.write(f"Simulated {kpi_choice}: **P50 {p50:.1f}** | Band: {p25:.1f} – {p75:.1f}")
    fig, ax = plt.subplots()
    ax.hist(mc_results, bins=20, alpha=0.7)
    ax.axvline(p50, color="black", linestyle="--", label="P50")
    ax.axvline(p25, color="orange", linestyle="--", label="P25")
    ax.axvline(p75, color="green", linestyle="--", label="P75")
    ax.set_title(f"{kpi_choice} Distribution (Monte Carlo)")
    ax.set_xlabel(kpi_choice)
    ax.legend()
    st.pyplot(fig)

# --- Step 6: Download KPI dashboard as CSV ---
st.header("5. Download KPI Dashboard")
st.download_button("Download Dashboard (CSV)", data=dashboard.to_csv(), file_name="op_kpi_dashboard.csv")

# --- Step 7: LLM-powered persona review ---
st.header("6. AI Persona Review")
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    st.write(f"API Key detected: {api_key[:8]}...")
    client = openai.OpenAI(api_key=api_key)
else:
    st.error("No API key found in environment. Please set OPENAI_API_KEY.")

persona = st.selectbox("AI Persona", ["Operating Partner", "CFO", "COO"], index=0)
if st.button(f"Ask AI {persona} for OP Review"):
    kpi_msg = f"Simulated {kpi_choice}: P50 {p50:.1f}, Band: {p25:.1f}–{p75:.1f}" if st.session_state.get("op_mc_done", False) else ""
    summary = (
        f"Dashboard:\n{dashboard.round(2).to_dict()}\n"
        f"Market scenario: {market_shock}. Value levers: pricing {pricing}, cost takeout {cost_takeout}, "
        f"customer success {success}, automation {automation}, working capital {wc}\n"
        f"Persona logic: Mgmt aggressive: {mgmt_aggressive}, CX push: {cx_aggressive}\n"
        f"{kpi_msg}\n"
        f"Special effects: {', '.join(effects) if effects else 'None'}"
    )
    persona_prompts = {
        "Operating Partner": "You are a PE operating partner. Review the simulated dashboard, levers, and bands. Recommend 2-3 next moves and flag any risk.",
        "CFO": "You are a portfolio company CFO reviewing OP simulation and recommending actions.",
        "COO": "You are a COO, reviewing dashboard and simulation to prioritize ops actions."
    }
    prompt = (
        persona_prompts[persona] +
        "\nGiven the simulation and dashboard, answer:\n"
        "1. What KPIs are on/off track? What stands out?\n"
        "2. Suggest 2-3 practical operating moves or board recommendations.\n"
        "3. Where are the biggest risks if macro worsens?\n"
        f"Summary:\n{summary}\n"
        "Be clear, board-oriented, and concise."
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
            st.markdown(f"**AI {persona} Response:**\n\n{llm_narrative}")
        except Exception as e:
            st.error(f"OpenAI API error: {e}")

st.markdown("""
---
**How to use:**  
1. Adjust value levers and scenario in the sidebar.  
2. Review the dashboard (current/target/simulated).  
3. Run Monte Carlo for any KPI.  
4. Download dashboard or ask AI persona for operating review.
""")
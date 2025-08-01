import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import openai
import os

st.title("VP – Valuation Model, Scenarios & AI Persona Review")

# --- Dummy comps data (you can load from CSV instead) ---
comps = pd.DataFrame({
    "Company": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Target"],
    "EBITDA_Multiple": [8.5, 9.2, 7.8, 10.1, 8.0, 8.6],
    "Growth": [10, 8, 7, 12, 9, 8],
    "Margin": [18, 20, 15, 22, 19, 19]
}).set_index("Company")

# --- Presets ---
presets = {
    "Base": {"multiple": 8.6, "ebitda": 25, "growth": 8, "macro": "Normal"},
    "Upside": {"multiple": 9.5, "ebitda": 28, "growth": 10, "macro": "Expansion"},
    "Downside": {"multiple": 7.5, "ebitda": 21, "growth": 4, "macro": "Mild Recession"},
    "Custom": None
}

st.sidebar.header("Scenario Selection")
preset = st.sidebar.selectbox("Preset", list(presets.keys()), index=0)

if preset != "Custom":
    params = presets[preset].copy()
else:
    params = {}

multiple = st.sidebar.slider("EBITDA Multiple", 5.0, 12.0, float(params.get("multiple", 8.6)), step=0.1)
ebitda = st.sidebar.slider("Target EBITDA ($M)", 10, 40, int(params.get("ebitda", 25)))
growth = st.sidebar.slider("Growth (%)", 0, 20, int(params.get("growth", 8)))
macro = st.sidebar.selectbox("Macro/Market", ["Normal", "Expansion", "Mild Recession", "Severe Recession"], index=["Normal", "Expansion", "Mild Recession", "Severe Recession"].index(params.get("macro", "Normal")))

# --- Persona toggles for diligence events ---
st.sidebar.header("Diligence/Persona Logic")
include_consultant_growth = st.sidebar.checkbox("Consultant Growth Forecast (+2% growth)", value=True)
include_supplier_lock = st.sidebar.checkbox("Supplier Price Lock (-0.5x multiple)", value=True)
include_churn_risk = st.sidebar.checkbox("Customer Churn Risk (-0.5x multiple)", value=False)

# --- Monte Carlo controls ---
n_runs = st.sidebar.number_input("Monte Carlo Simulations", 100, 2000, 500)
run_mc = st.sidebar.button("Run Monte Carlo")

# --- Apply persona/diligence effects ---
adj_growth = growth + (2 if include_consultant_growth else 0)
adj_multiple = multiple
if include_supplier_lock:
    adj_multiple -= 0.5
if include_churn_risk:
    adj_multiple -= 0.5

# --- Macro/market effect logic ---
if macro == "Expansion":
    adj_multiple += 0.5
    adj_growth += 1
elif macro == "Mild Recession":
    adj_multiple -= 0.7
    adj_growth -= 2
elif macro == "Severe Recession":
    adj_multiple -= 1.0
    adj_growth -= 4

# --- Monte Carlo function ---
def simulate_one():
    # Randomize within reasonable noise
    mult = np.random.normal(adj_multiple, 0.3)
    eb = np.random.normal(ebitda, 2)
    g = np.random.normal(adj_growth, 1.2)
    # Macro effect amplifies uncertainty
    if macro == "Severe Recession":
        mult -= np.abs(np.random.normal(0.3, 0.2))
        g -= abs(np.random.normal(1, 0.5))
    ev = eb * mult
    return ev, mult, eb, g

# --- Monte Carlo run ---
if run_mc:
    st.session_state.vp_mc_done = True
    ev_results, mult_results, eb_results, g_results = [], [], [], []
    for _ in range(int(n_runs)):
        ev, m, eb, g = simulate_one()
        ev_results.append(ev)
        mult_results.append(m)
        eb_results.append(eb)
        g_results.append(g)
    p25, p50, p75 = np.percentile(ev_results, [25, 50, 75])
    st.session_state.vp_results = {
        "ev_results": ev_results, "mult_results": mult_results,
        "eb_results": eb_results, "g_results": g_results,
        "p25": p25, "p50": p50, "p75": p75
    }

# --- Display MC and analytics ---
if st.session_state.get("vp_mc_done", False):
    ev_results = st.session_state["vp_results"]["ev_results"]
    p25 = st.session_state["vp_results"]["p25"]
    p50 = st.session_state["vp_results"]["p50"]
    p75 = st.session_state["vp_results"]["p75"]
    st.metric("Implied Enterprise Value (P50)", f"${p50:,.0f}M")
    st.metric("Bid Range (P25–P75)", f"${p25:,.0f}M – ${p75:,.0f}M")
    st.write(f"Adjusted Multiple: **{adj_multiple:.2f}x**  |  Adjusted Growth: **{adj_growth:.1f}%**")
    # Plot histogram
    fig, ax = plt.subplots()
    ax.hist(ev_results, bins=25, alpha=0.7)
    ax.axvline(p50, color="black", linestyle="--", label="P50")
    ax.axvline(p25, color="orange", linestyle="--", label="P25")
    ax.axvline(p75, color="green", linestyle="--", label="P75")
    ax.set_title("Enterprise Value Distribution (Monte Carlo)")
    ax.set_xlabel("Enterprise Value ($M)")
    ax.legend()
    st.pyplot(fig)

    # Show comps table
    st.subheader("Comps Benchmarking")
    st.dataframe(comps)
    st.bar_chart(comps["EBITDA_Multiple"])

    # List which persona/diligence rules fired
    rule_msgs = []
    if include_consultant_growth: rule_msgs.append("Consultant Growth Forecast (+2% growth)")
    if include_supplier_lock: rule_msgs.append("Supplier Price Lock (-0.5x multiple)")
    if include_churn_risk: rule_msgs.append("Customer Churn Risk (-0.5x multiple)")
    st.info(
        "**Which Persona/Diligence Rules Are On?**\n\n"
        + "\n".join(f"- {rule}" for rule in rule_msgs)
        + f"\n\n- Macro scenario: {macro}"
    )

    # ----- LLM Persona Review -----
    st.subheader("AI VP/CFO/Operating Partner Review")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        st.write(f"API Key detected: {api_key[:8]}...")
        client = openai.OpenAI(api_key=api_key)
    else:
        st.error("No API key found in environment. Please set OPENAI_API_KEY.")

    persona = st.selectbox("Choose AI Persona", ["VP", "CFO", "Operating Partner"], index=0)
    if st.button(f"Ask the AI {persona} for Scenario Review"):
        scenario_summary = (
            f"Preset: {preset}\n"
            f"Base EBITDA: {ebitda}, Adjusted Multiple: {adj_multiple}, Adjusted Growth: {adj_growth}, Macro: {macro}\n"
            f"Persona rules on: {', '.join(rule_msgs) if rule_msgs else 'None'}\n"
            f"Monte Carlo Bid Range: P25–P75 ${p25:,.0f}M–${p75:,.0f}M (P50: ${p50:,.0f}M)"
        )
        persona_prompts = {
            "VP": "You are a private equity VP evaluating a valuation scenario.",
            "CFO": "You are the CFO of a target company, reviewing private equity bid scenarios.",
            "Operating Partner": "You are an operating partner advising on valuation, risk, and upside scenarios."
        }
        prompt = (
            persona_prompts[persona] + "\n"
            "Given the scenario and results below, comment on:\n"
            "1. Main risk/upside drivers.\n"
            "2. 2–3 concrete actions for negotiation, bid, or post-close planning.\n"
            "3. Should the sponsor bid at P50 or take more/less risk?\n"
            f"Scenario summary: {scenario_summary}\n"
            "Write for investment committee context."
        )
        with st.spinner("AI persona reviewing scenario..."):
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

else:
    st.write("Set parameters and run Monte Carlo for valuation analytics and persona review.")

st.markdown("""
---
**How to use:**  
- Adjust EBITDA, multiple, growth, and diligence findings  
- Simulate bid ranges under various macro scenarios  
- Compare to comps, and get VP/CFO/Op Partner AI advice!
""")
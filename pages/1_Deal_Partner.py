import streamlit as st
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt
import openai
import os

st.title("Deal Partner – Monte Carlo, Personas & AI Scenario Review")

# ---- Scenario Presets ----
scenarios = {
    "Base": {"growth": 8, "margin": 18, "multiple": 9, "pricing": 2, "churn": 5, "macro": "None"},
    "Upside": {"growth": 12, "margin": 21, "multiple": 10, "pricing": 4, "churn": 3, "macro": "Expansion"},
    "Downside": {"growth": 3, "margin": 15, "multiple": 7, "pricing": 0, "churn": 8, "macro": "Mild Recession"},
    "Custom": None,
}

st.sidebar.header("Scenario Selection")
preset = st.sidebar.selectbox("Choose a Scenario Preset", list(scenarios.keys()), index=0)

# ---- Value Lever Inputs ----
if preset != "Custom":
    params = scenarios[preset].copy()
else:
    params = {}

growth = st.sidebar.slider("Revenue Growth (%)", 0, 20, params.get("growth", 8))
margin = st.sidebar.slider("EBITDA Margin (%)", 10, 40, params.get("margin", 18))
exit_multiple = st.sidebar.slider("Exit EBITDA Multiple", 5, 20, params.get("multiple", 9))
pricing_power = st.sidebar.slider("Avg. Pricing Power (%)", 0, 10, params.get("pricing", 2))
churn = st.sidebar.slider("Churn Rate (%)", 0, 20, params.get("churn", 5))
macro_shock = st.sidebar.selectbox("Macro Shock", ["None", "Expansion", "Mild Recession", "Severe Recession"], 
                                   index=["None", "Expansion", "Mild Recession", "Severe Recession"].index(params.get("macro", "None")))

# Persona toggles
st.sidebar.header("Persona/Behavioral Logic")
management_response = st.sidebar.checkbox("Enable Management Cost Takeout in Downturn", value=True)
retention_action = st.sidebar.checkbox("Enable Retention Initiative on High Churn", value=True)
pricing_backlash = st.sidebar.checkbox("Enable Customer Backlash to High Pricing", value=True)

n_runs = st.sidebar.number_input("Simulations (Monte Carlo)", 100, 3000, 500)
run_mc = st.sidebar.button("Run Monte Carlo Simulation")

# State variables to preserve results across reruns
if 'mc_done' not in st.session_state:
    st.session_state.mc_done = False

def simulate_one():
    ebitda0 = 25
    revenue0 = 100
    years = 5

    g = np.random.normal(growth, 1.5)
    m = np.random.normal(margin, 1.2)
    mult = np.random.normal(exit_multiple, 0.5)
    p = np.random.normal(pricing_power, 0.5)
    churn_ = np.random.normal(churn, 1)
    macro = macro_shock

    persona_effects = []
    if macro == "Expansion":
        g += np.random.uniform(2, 4)
        m += np.random.uniform(0.5, 1)
        persona_effects.append("Expansion: market tailwind boosts growth and margin.")
    elif macro == "Mild Recession":
        g -= np.random.uniform(3, 5)
        m -= np.random.uniform(1, 2)
        persona_effects.append("Mild Recession: growth and margin hit.")
        if management_response:
            m += 1.0
            persona_effects.append("Mgmt: Cost takeout adds +1 margin in downturn.")
    elif macro == "Severe Recession":
        g -= np.random.uniform(5, 8)
        m -= np.random.uniform(2, 4)
        churn_ += np.random.uniform(2, 4)
        persona_effects.append("Severe Recession: bigger hits to growth/margin, churn rises.")
        if management_response:
            m += 1.5
            persona_effects.append("Mgmt: Aggressive cost cutting in severe downturn.")

    churn_effect = 1 - churn_ / 100
    if churn_ > 10 and retention_action:
        churn_effect += 0.04
        m -= 0.3
        persona_effects.append("Mgmt: Retention initiative deployed, wins back some customers (lower churn), slight margin cost.")

    if p > 5 and pricing_backlash:
        churn_effect -= 0.02
        persona_effects.append("Customers: Backlash to high pricing—churn ticks up.")

    revenue = revenue0
    ebitda = ebitda0
    cashflows = []
    for t in range(years):
        revenue = revenue * (1 + g/100) * (1 + p/100) * churn_effect
        ebitda = revenue * (m/100)
        cashflows.append(ebitda)
    exit_value = ebitda * mult
    purchase_price = 200

    irr = npf.irr([-purchase_price] + cashflows[:-1] + [cashflows[-1] + exit_value]) * 100
    moic = (sum(cashflows) + exit_value) / purchase_price

    return irr, moic, exit_value, persona_effects

if run_mc:
    st.session_state.mc_done = True
    irr_results, moic_results, exit_values = [], [], []
    persona_effects_all = []

    for _ in range(int(n_runs)):
        irr, moic, exit_val, persona_effects = simulate_one()
        if np.isfinite(irr):
            irr_results.append(irr)
            moic_results.append(moic)
            exit_values.append(exit_val)
            persona_effects_all.extend(persona_effects)

    p25, p50, p75 = np.percentile(irr_results, [25, 50, 75])
    moic_p25, moic_p50, moic_p75 = np.percentile(moic_results, [25, 50, 75])
    st.session_state.results = {
        "irr_results": irr_results,
        "moic_results": moic_results,
        "exit_values": exit_values,
        "p25": p25, "p50": p50, "p75": p75,
        "moic_p25": moic_p25, "moic_p50": moic_p50, "moic_p75": moic_p75,
        "persona_effects_all": persona_effects_all
    }

if st.session_state.get("mc_done", False):
    irr_results = st.session_state["results"]["irr_results"]
    moic_results = st.session_state["results"]["moic_results"]
    exit_values = st.session_state["results"]["exit_values"]
    p25 = st.session_state["results"]["p25"]
    p50 = st.session_state["results"]["p50"]
    p75 = st.session_state["results"]["p75"]
    moic_p25 = st.session_state["results"]["moic_p25"]
    moic_p50 = st.session_state["results"]["moic_p50"]
    moic_p75 = st.session_state["results"]["moic_p75"]
    persona_effects_all = st.session_state["results"]["persona_effects_all"]

    st.metric("IRR (P50)", f"{p50:.1f}%")
    st.metric("IRR Range (P25–P75)", f"{p25:.1f}% – {p75:.1f}%")
    st.metric("MOIC (P50)", f"{moic_p50:.2f}x")
    st.metric("MOIC Range (P25–P75)", f"{moic_p25:.2f}x – {moic_p75:.2f}x")
    st.metric("Exit Value Median", f"${np.median(exit_values):,.0f}M")

    fig, ax = plt.subplots()
    ax.hist(irr_results, bins=30, alpha=0.7)
    ax.axvline(p50, color="black", linestyle="--", label="P50")
    ax.axvline(p25, color="orange", linestyle="--", label="P25")
    ax.axvline(p75, color="green", linestyle="--", label="P75")
    ax.set_title("IRR Distribution (Monte Carlo, Persona Logic Enabled)")
    ax.set_xlabel("IRR (%)")
    ax.set_ylabel("Frequency")
    ax.legend()
    st.pyplot(fig)

    st.info(
        "**Which Persona Rules Fired?**\n\n"
        + "\n".join(f"- {rule}" for rule in set(persona_effects_all))
        + f"\n\n- Probability of >20% IRR: {int(100 * sum(i >= 20 for i in irr_results) / len(irr_results))}%"
        "\n- Test different levers or behaviors to see how outcomes change."
    )

    # ----- LLM Persona Review -----
    st.subheader("AI Deal Partner Review")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        st.write(f"API Key detected: {api_key[:8]}...")
        client = openai.OpenAI(api_key=api_key)
    else:
        st.error("No API key found in environment. Please set OPENAI_API_KEY.")

    persona = st.selectbox("Choose AI Persona", ["Deal Partner", "CFO", "Operating Partner"], index=0)
    if st.button(f"Ask the AI {persona} for Scenario Review"):
        st.write("Button clicked - preparing prompt for OpenAI...")

        scenario_summary = (
            f"Scenario preset: {preset}\n"
            f"Growth: {growth}%, Margin: {margin}%, Multiple: {exit_multiple}x, "
            f"Pricing Power: {pricing_power}%, Churn: {churn}%, Macro: {macro_shock}\n"
            f"Behavior rules enabled: "
            f"Cost Takeout: {'Yes' if management_response else 'No'}, "
            f"Retention Initiative: {'Yes' if retention_action else 'No'}, "
            f"Pricing Backlash: {'Yes' if pricing_backlash else 'No'}\n"
            f"Monte Carlo Results: Median IRR: {p50:.1f}%, P25–P75 IRR: {p25:.1f}%–{p75:.1f}%, "
            f"Median MOIC: {moic_p50:.2f}x, Probability of >20% IRR: {int(100 * sum(i >= 20 for i in irr_results) / len(irr_results))}%\n"
            f"Key persona rules that impacted outcomes: {', '.join(set(persona_effects_all)) if len(persona_effects_all) else 'None'}."
        )
        persona_prompts = {
            "Deal Partner": "You are a senior private equity deal partner evaluating a scenario simulation.",
            "CFO": "You are the CFO of a private equity-backed company, reviewing a forward-looking scenario simulation.",
            "Operating Partner": "You are an operating partner advising on post-acquisition value creation and risk management."
        }
        prompt = (
            persona_prompts[persona] + "\n"
            "Given the following scenario and outcomes:\n"
            f"{scenario_summary}\n"
            "1. Identify the main risk and upside drivers.\n"
            "2. Suggest two or three concrete actions for deal structuring or post-close value creation.\n"
            "3. Would you recommend proceeding, and why?\n"
            "Respond in a practical, board-ready style."
        )

        st.write("Prompt prepared, calling OpenAI API...")

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
    st.write("Select scenario and persona options, then click **Run Monte Carlo Simulation**.")

st.markdown("""
---
**What's new:**  
- Persona/behavior logic lets you simulate how management or customers "respond" to shocks.
- Toggle cost takeout, retention, and backlash logic in sidebar.
- After simulation, ask a Deal Partner/CFO/Operating Partner AI persona for a scenario review!
""")
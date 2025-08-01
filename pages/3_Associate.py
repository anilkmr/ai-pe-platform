import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import openai
import os

st.title("Associate – Data Pack, Sensitivity, Monte Carlo & AI Review")

# --- Step 1: Load & Clean Data ---
st.header("1. Fetch & Clean Data")
fin = pd.DataFrame({
    "Company": ["Target", "Alpha", "Beta", "Gamma", "Outlier"],
    "Revenue": [120, 130, 115, 140, 300],
    "EBITDA": [25, 23, 22, 30, 100],
    "Employees": [200, 220, 210, 230, 250]
})

st.write("Raw data:")
st.dataframe(fin)
# Outlier detection (simple: revenue > 250)
clean = fin[fin["Revenue"] < 250]
n_out = fin.shape[0] - clean.shape[0]
st.success(f"AI cleaned data: removed {n_out} outlier(s).")
st.dataframe(clean)
st.session_state['clean_fin'] = clean

# --- Step 2: Select Comps ---
st.header("2. Curate Comps")
comps = pd.DataFrame({
    "Company": ["Alpha", "Beta", "Gamma", "Target"],
    "EBITDA_Multiple": [9, 8, 11, 8.5],
    "RevenueGrowth": [10, 9, 12, 8]
})
select_comps = st.multiselect(
    "Choose which comps to include in analysis (default: all except Target):",
    comps["Company"].tolist(), default=["Alpha", "Beta", "Gamma"])
cur_comps = comps[comps["Company"].isin(select_comps + ["Target"])].set_index("Company")
st.dataframe(cur_comps)
st.bar_chart(cur_comps["EBITDA_Multiple"])

# --- Step 3: Sensitivity Table ---
st.header("3. Sensitivity Analysis")
metric = st.selectbox("Metric for Sensitivity", ["Revenue", "EBITDA", "Employees"])
base_val = clean[clean["Company"] == "Target"][metric].values[0]
st.write(f"Base {metric}: {base_val}")

plus_10 = base_val * 1.10
minus_10 = base_val * 0.90
sens_df = pd.DataFrame({
    "Scenario": ["-10%", "Base", "+10%"],
    metric: [round(minus_10, 1), base_val, round(plus_10, 1)]
})
st.table(sens_df)

# --- Step 4: Monte Carlo on a Selected KPI ---
st.header("4. Monte Carlo Benchmarking")
kpi = st.selectbox("KPI for Monte Carlo", ["EBITDA_Multiple", "RevenueGrowth"])
target_val = cur_comps.loc["Target", kpi]
comps_vals = cur_comps.drop("Target")[kpi]
n_runs = st.number_input("Simulations", 100, 2000, 500)
run_mc = st.button("Run Monte Carlo Scenario")

if run_mc:
    st.session_state.associate_mc_done = True
    # Simulate comps as normal, with Target as comparison
    mc_results = np.random.normal(comps_vals.mean(), comps_vals.std(), int(n_runs))
    p25, p50, p75 = np.percentile(mc_results, [25, 50, 75])
    st.session_state.mc_results = {"mc_results": mc_results, "p25": p25, "p50": p50, "p75": p75, "target": target_val}

if st.session_state.get("associate_mc_done", False):
    mc_results = st.session_state["mc_results"]["mc_results"]
    p25 = st.session_state["mc_results"]["p25"]
    p50 = st.session_state["mc_results"]["p50"]
    p75 = st.session_state["mc_results"]["p75"]
    target_val = st.session_state["mc_results"]["target"]
    st.write(f"Target {kpi}: **{target_val:.2f}**")
    st.write(f"Comps P50: {p50:.2f}  |  Range: {p25:.2f} – {p75:.2f}")
    fig, ax = plt.subplots()
    ax.hist(mc_results, bins=20, alpha=0.7, label="Comps")
    ax.axvline(target_val, color="black", linestyle="--", label="Target")
    ax.axvline(p50, color="blue", linestyle="--", label="P50")
    ax.axvline(p25, color="orange", linestyle="--", label="P25")
    ax.axvline(p75, color="green", linestyle="--", label="P75")
    ax.set_title(f"{kpi} Distribution (Monte Carlo)")
    ax.set_xlabel(kpi)
    ax.legend()
    st.pyplot(fig)

# --- Step 5: Download Analysis Pack ---
st.header("5. Download Pack")
csv_pack = clean.to_csv(index=False)
st.download_button("Download Data Pack (CSV)", data=csv_pack, file_name="analysis_pack.csv")

# --- Step 6: LLM-Powered Pack Commentary ---
st.header("6. AI Pack Commentary")
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    st.write(f"API Key detected: {api_key[:8]}...")
    client = openai.OpenAI(api_key=api_key)
else:
    st.error("No API key found in environment. Please set OPENAI_API_KEY.")

persona = st.selectbox("Choose AI Persona", ["Associate", "VP", "Operating Partner"], index=0)
if st.button(f"Ask AI {persona} for Pack Commentary"):
    summary = (
        f"Target company {', '.join(clean[clean['Company']=='Target'].values[0].astype(str))}\n"
        f"Included comps: {', '.join(select_comps)}\n"
        f"Comps {kpi} P50: {p50:.2f} (Target: {target_val:.2f})\n"
        f"Sensitivity base: {base_val}, -10%: {minus_10:.1f}, +10%: {plus_10:.1f}\n"
    )
    persona_prompts = {
        "Associate": "You are a private equity associate writing an analysis pack summary.",
        "VP": "You are a PE VP reviewing the associate's data pack and analysis.",
        "Operating Partner": "You are an operating partner, reviewing the data pack for operational insights."
    }
    prompt = (
        persona_prompts[persona] + "\n"
        "Given the pack below, summarize:\n"
        "1. How does the target stack up on the selected KPI?\n"
        "2. Any red/green flags in the data or comps?\n"
        "3. What next questions or analyses should go in the IC deck?\n"
        f"Pack summary: {summary}\n"
        "Write in a crisp, action-oriented way for a PE audience."
    )
    with st.spinner("AI persona writing commentary..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": persona_prompts[persona]},
                    {"role": "user", "content": prompt}
                ]
            )
            llm_narrative = response.choices[0].message.content.strip()
            st.markdown(f"**AI {persona} Commentary:**\n\n{llm_narrative}")
        except Exception as e:
            st.error(f"OpenAI API error: {e}")

st.markdown("""
---
**How to use:**  
1. Review and clean financials, then curate comps.  
2. Run sensitivity and Monte Carlo for your metric.  
3. Download your analysis pack, or ask the AI persona for commentary for your IC memo!
""")
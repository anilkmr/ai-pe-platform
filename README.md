# **AI-Driven Valuation Simulation Platform**

### **Requirements & User Stories (MVP v2 – July 2025)**

---

## **General Platform Requirements**

- **Platform must support:** Interactive dashboards, scenario simulation, persona/behavior toggles, Monte Carlo modeling, and LLM-powered AI commentary for 6 roles: Deal Partner, VP, Associate, Operating Partner, CxO, Management Team.
- **Authentication:** OpenAI key via environment variable; no confidential data stored.

---

## **Role-Based Modules & User Stories**

### **1. Deal Partner: AI-Driven Scenario Modeling**

- **Requirement:** Simulate investment scenarios with Monte Carlo (IRR, MOIC, exit value) and see probability bands.
- **User Story:** *As a Deal Partner, I want to adjust levers (growth, margin, multiple, pricing, churn, macro shocks) and see probability-weighted IRR/MOIC bands, so that I can make decision-grade, risk-adjusted investment recommendations.*
- **Requirement:** Persona/behavior toggles (cost takeout, retention, pricing backlash).
- **Requirement:** Get an LLM-powered investment memo from an AI Deal Partner/CFO/Op Partner persona based on my simulation.
- **Acceptance Criteria:**
    - User can adjust all levers in the sidebar and run >100 Monte Carlo sims.
    - IRR and MOIC probability bands (P25/P50/P75) are displayed after each simulation.
    - Persona toggles (cost takeout, retention, pricing backlash) affect the scenario outcome as described in UI help text.
    - After running a scenario, user can request an AI (Deal Partner/CFO/Operating Partner) summary, which is generated and visible in the app.
    - The summary references scenario results and persona logic.

---

### **2. VP: Valuation/Bid Scenario Engine**

- **Requirement:** Rapidly adjust valuation levers (multiple, EBITDA, growth, macro/diligence shocks).
- **User Story:** *As a VP, I want to model the impact of diligence findings and macro events on bid ranges and compare against comps, so I can structure a defensible bid.*
- **Requirement:** Monte Carlo simulation of enterprise value/bid ranges.
- **Requirement:** LLM persona (VP/CFO/Op Partner) review of bid scenarios.
- **Acceptance Criteria:**
    - User can adjust multiple and EBITDA, toggle diligence findings, and run >100 Monte Carlo sims.
    - Enterprise value/bid range output shows probability bands.
    - Comps table/chart are visible for benchmarking.
    - AI persona review (VP/CFO/Operating Partner) can be triggered and result appears in the UI.
    - All toggled diligence effects and macro shocks are reflected in the calculation and AI summary.

---

### **3. Associate: Pack Automation & Benchmarking**

- **Requirement:** Upload, clean, and curate data packs; auto-remove outliers.
- **User Story:**
    
    *As an Associate, I want to clean financials, curate comps, run sensitivity and benchmarking, and download analysis packs for IC.*
    
- **Requirement:** Sensitivity analysis on any metric; Monte Carlo comp benchmarking for KPIs.
- **Requirement:** LLM persona (Associate/VP/Op Partner) commentary for IC pack.
- **Acceptance Criteria:**
    - On page load, financial data is cleaned with clear outlier removal messaging.
    - User can select/deselect comps, and the comps chart updates accordingly.
    - Sensitivity analysis table is generated for a user-selected metric.
    - User can run Monte Carlo benchmarking for any KPI.
    - Analysis pack is downloadable as a CSV file.
    - AI persona review (Associate/VP/Operating Partner) can be triggered for the current analysis pack and produces relevant summary.

---

### **4. Operating Partner: KPI Simulation & Dashboard**

- **Requirement:** Dashboard of current/target/simulated KPIs (Revenue, EBITDA, Churn, NPS, Cash Conversion).
- **User Story:**
    
    *As an Operating Partner, I want to simulate the impact of value levers (pricing, cost, automation, working capital, customer success) and macro scenarios on future KPIs, so I can recommend and monitor value creation initiatives.*
    
- **Requirement:** Monte Carlo simulation for future KPI bands under stress.
- **Requirement:** LLM persona (Op Partner/CFO/COO) operating review and recommendations.
- **Acceptance Criteria:**
    - Value levers and macro/behavior toggles update the simulated KPI dashboard in real time.
    - Current, target, and simulated KPIs are displayed in a data frame.
    - User can run a Monte Carlo simulation for any KPI and see output bands.
    - Dashboard is downloadable as CSV.
    - AI persona review (Operating Partner/CFO/COO) is generated and shown after simulation.

---

### **5. CxO: Control Tower & Resource Allocation**

- **Requirement:** Control tower dashboard with KPI traffic lights; allocate budgets/resources to functions via sliders.
- **User Story:**
    
    *As a CxO, I want to allocate resources between Sales, Marketing, Product, Ops, and Service, and instantly see the impact on all major KPIs and functional outputs under different market scenarios.*
    
- **Requirement:** Behavior toggles for macro/cost/investment strategies.
- **Requirement:** Downloadable dashboard; LLM (CEO/CFO/COO) scenario review.
- **Acceptance Criteria:**
    - Budget sliders control resource allocation, with total available budget enforced.
    - KPI dashboard (traffic lights, deltas) updates as allocation/macro/persona toggles change.
    - Functional output and KPI impact tables update live.
    - Dashboard is downloadable as CSV.
    - AI persona review (CEO/CFO/COO) reflects current dashboard and allocation in its output.

---

### **6. Management Team: Initiative Impact Tracking**

- **Requirement:** Add, complete, and track initiatives (e.g., launches, campaigns, cost programs) and see their simulated effect on time-series KPIs.
- **User Story:**
    
    *As a Management Team member, I want to check off initiatives and see their impact on KPIs in real time, so I can drive performance and communicate results to the board.*
    
- **Requirement:** Multi-KPI trend charts; downloadable tracker.
- **Requirement:** LLM persona (CEO/COO/CRO) management review and recommendations.
- **Acceptance Criteria:**
    - User can mark initiatives as complete or add new ones, and completed initiatives immediately adjust relevant KPIs.
    - KPI trend chart updates dynamically to show impact of initiatives.
    - Initiative tracker and simulated KPIs are downloadable as CSV.
    - AI persona review (CEO/COO/CRO) references completed initiatives, highlights KPI trajectory, and recommends next actions.

---

## **Shared User Stories**

- *As any user, I want to download my scenario dashboard/pack for reporting or further analysis.*
- *As any user, I want to ask an AI persona for a tailored summary or recommendation, using my real scenario and outputs.*
- *As any user, I want simulation results to reflect not just numerical levers, but realistic management/customer behaviors.*

## **Shared Acceptance Criteria**

- All Monte Carlo simulations run in <5 seconds for 500 runs on typical laptop.
- User can trigger AI persona review with a single button; result appears in UI within 10 seconds or an error is shown.
- All outputs (charts, dashboards, packs) are downloadable via button.
- Any scenario or persona toggle change updates calculations and visuals immediately.
- No API key is stored in code or UI; only environment variable is used.
- App works end-to-end on Mac/PC with Streamlit and provided sample data.

---

## **Non-Functional Requirements**

- **Performance:** Monte Carlo sims must run in-browser in < 5 seconds for 500 runs.
- **Security:** No OpenAI key in code; must use environment variable.
- **Extensibility:** Each role/module is a standalone Streamlit page; new data or logic can be plugged in.
- **Usability:** All scenario changes update charts, metrics, and AI responses in real time.

---

## **Next Extensions (for backlog):**

- Enable file upload for real data (csv/xlsx).
- Add time-series/period-over-period tracking for CxO/OP/Management.
- Auto-generate Board slides from any dashboard/pack.
- Add “compare scenarios” and save/share functions.
- Multi-user/team collaboration.

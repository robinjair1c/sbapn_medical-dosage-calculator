import streamlit as st
import json
import sys
from datetime import datetime

# Import the interpreter modules
from interpreter import run, run_and_raise_on_alert
from errors import (
    LexicalError, ParseError, ExecutionError, 
    UnknownDrugError, SafetyLimitExceeded
)

# Page Configuration
st.set_page_config(
    page_title="Medical Dosage Calculator",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    :root {
        --bg: #0f172a;         /* slate-900 */
        --panel: #111827;      /* gray-900 */
        --panel-2: #0b1220;    /* darker sidebar */
        --text: #e5e7eb;       /* gray-200 */
        --muted: #9ca3af;      /* gray-400 */
        --primary: #14b8a6;    /* teal-500 */
        --primary-2: #0ea5a4;  /* teal-600 */
        --primary-3: #2dd4bf;  /* teal-400 */
    }

    html, body, [data-testid="stAppViewContainer"] { background-color: var(--bg); color: var(--text); }
    .block-container { padding-top: 1rem; }

    .main-header {
        font-size: 2.4rem;
        font-weight: 800;
        color: var(--primary-3);
        text-align: center;
        letter-spacing: .2px;
        margin-bottom: .25rem;
    }
    .sub-header { color: var(--muted); text-align: center; font-size: 1rem; margin-bottom: 1rem; }

    [data-testid="stSidebar"] { background: var(--panel-2); color: var(--text); }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: var(--text); }

    .stButton>button {
        background: var(--primary);
        color: #0b1322;
        border: 1px solid rgba(255,255,255,0.08);
        padding: .55rem .9rem;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(20,184,166,.25);
        transition: transform .15s ease, box-shadow .15s ease, background .15s ease;
    }
    .stButton>button:hover { transform: translateY(-1px); background: var(--primary-2); box-shadow: 0 10px 28px rgba(20,184,166,.35); }

    .stTextArea textarea, .stNumberInput input, .stSelectbox [role="combobox"], .stRadio > div { 
        background: var(--panel);
        color: var(--text);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,.08);
        box-shadow: 0 2px 6px rgba(0,0,0,.35);
    }

    .stTabs [role="tablist"] button {
        padding: .55rem .9rem;
        margin-right: .4rem;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,.12);
        background: var(--panel);
        color: var(--muted);
    }
    .stTabs [role="tablist"] button[aria-selected="true"] {
        background: #0e1a2b;
        border-color: rgba(20,184,166,.35);
        color: var(--primary-3);
        font-weight: 700;
    }

    .stAlert { border-radius: 12px; background: var(--panel); color: var(--text); border: 1px solid rgba(255,255,255,.12); box-shadow: 0 8px 24px rgba(0,0,0,.35); }
    .stMetric { background: var(--panel); border: 1px solid rgba(255,255,255,.12); border-radius: 12px; padding: .75rem; color: var(--text); }

    .chip { display: inline-block; padding: .35rem .7rem; border-radius: 999px; background: #0e1a2b; color: var(--primary-3); border: 1px solid rgba(20,184,166,.35); margin: .25rem .25rem .25rem 0; font-size: .85rem; }

    hr { border: none; height: 1px; background: linear-gradient(90deg, #0000, rgba(255,255,255,.12), #0000); margin: 1.25rem 0; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'command_history' not in st.session_state:
    st.session_state.command_history = []
if 'result_history' not in st.session_state:
    st.session_state.result_history = []

# Header
st.markdown('<div class="main-header">💊 Medical Dosage Calculation Interpreter</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Clinical Decision Support Tool</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Navigation")
    st.markdown('<div class="page-badge">Actions</div>', unsafe_allow_html=True)
    if st.button("🧮 Calculate Dose", use_container_width=True):
        st.session_state.active_tab = "Calc"
        st.rerun()
    if st.button("⚖️ Check Interaction", use_container_width=True):
        st.session_state.active_tab = "Interact"
        st.rerun()
    if st.button("✅ Validate Prescription", use_container_width=True):
        st.session_state.active_tab = "Validate"
        st.rerun()
    st.divider()
    if st.button("📊 Results", use_container_width=True):
        st.session_state.active_tab = "Results"
        st.rerun()
    if st.button("📝 History", use_container_width=True):
        st.session_state.active_tab = "History"
        st.rerun()
    if st.button("ℹ️ About", use_container_width=True):
        st.session_state.active_tab = "About"
        st.rerun()

# Main content area
# Ensure active tab state
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'Calc'

active = st.session_state.active_tab

if active == 'Builder':
    st.header("Setup Command")

    drugs = [
        "amlodipine", "losartan", "metformin", "glimepiride",
        "amoxicillin", "azithromycin", "paracetamol",
        "ibuprofen", "salbutamol", "montelukast"
    ]
    condition_map = {
        "amlodipine": ["hypertension"],
        "losartan": ["hypertension"],
        "metformin": ["diabetes"],
        "glimepiride": ["diabetes"],
        "amoxicillin": ["infection"],
        "azithromycin": ["infection"],
        "paracetamol": ["pain"],
        "ibuprofen": ["pain", "inflammation"],
        "salbutamol": ["asthma"],
        "montelukast": ["asthma"],
    }

    action = st.radio("Choose Action", ["Calculate Dose", "Check Interaction", "Validate Prescription"], horizontal=True)

    command = ""
    if action == "Calculate Dose":
        col1, col2 = st.columns(2)
        with col1:
            sel_drug = st.selectbox("Drug", options=drugs, index=2)
            cond_opts = condition_map.get(sel_drug, ["general"])
            sel_condition = st.selectbox("Condition", options=cond_opts, index=0)
        with col2:
            weight = st.number_input("Weight (kg)", min_value=1.0, max_value=300.0, value=70.0, step=0.5)
            age = st.number_input("Age", min_value=0, max_value=120, value=45, step=1)
            kidney_function = st.selectbox("Kidney Function", options=["normal","impaired","reduced","ckd"], index=0)
        command = f"CALCULATE DOSE FOR drug={sel_drug}, condition={sel_condition}, weight={weight}kg, age={int(age)}, kidney_function={kidney_function}"

    elif action == "Check Interaction":
        col1, col2 = st.columns(2)
        with col1:
            drug_a = st.selectbox("Drug A", options=drugs, index=1)
        with col2:
            drug_b = st.selectbox("Drug B", options=drugs, index=0)
        if drug_a == drug_b:
            st.warning("Select two different drugs to check interactions.")
        command = f"CHECK INTERACTION BETWEEN {drug_a} AND {drug_b}"

    elif action == "Validate Prescription":
        col1, col2 = st.columns(2)
        with col1:
            v_drug = st.selectbox("Drug", options=drugs, index=0, key="val_drug")
        with col2:
            dose = st.number_input("Dose (mg/day)", min_value=0.0, max_value=5000.0, value=500.0, step=50.0)
        command = f"VALIDATE PRESCRIPTION drug={v_drug}, dose={int(dose)}mg"

    execute_btn = st.button("▶️ Execute", type="primary")

    if execute_btn and command.strip():
        st.divider()
        st.subheader("Execution Results")

        try:
            result = run(command)
            st.session_state.command_history.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'command': command
            })
            st.session_state.result_history.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'command': command,
                'result': result,
                'status': 'success'
            })
            # Navigate to Results after execution
            st.session_state.active_tab = 'Results'
            st.rerun()

            if result.get('type') == 'CALCULATE':
                st.success("✅ Dose calculation completed successfully!")
                r = result['result']
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Drug", r['drug'].title())
                    st.metric("Condition", r['condition'].title())
                    st.metric("Recommended Daily Dose", f"{r['recommended_mg_per_day']} mg/day")
                with col2:
                    if r['per_dose_mg']:
                        st.metric("Per-Dose Amount", f"{r['per_dose_mg']} mg")
                        st.metric("Doses Per Day", r['doses_per_day'])
                    st.metric("Safety Range", f"{r['safety_range_mg_day'][0]}-{r['safety_range_mg_day'][1]} mg/day")
                st.info(f"**Rationale:** {r['rationale']}")
                if r.get('alert'):
                    st.warning(f"⚠️ **ALERT:** {r['alert']}")

            elif result.get('type') == 'CHECK':
                st.success("✅ Interaction check completed!")
                st.info(f"**Interaction:** {result['interaction']}")

            elif result.get('type') == 'VALIDATE':
                r = result['result']
                if r['status'] == 'OK':
                    st.success(f"✅ **{r['status']}:** {r['message']}")
                elif r['status'] == 'EXCEEDS':
                    st.error(f"❌ **{r['status']}:** {r['message']}")
                else:
                    st.warning(f"⚠️ **{r['status']}:** {r['message']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Drug", r['drug'].title())
                with col2:
                    st.metric("Prescribed Dose", f"{r['dose_mg_per_day']} mg/day")
                with col3:
                    st.metric("Status", r['status'])

            elif result.get('type') == 'ADJUST':
                st.success("✅ Dose adjustment completed successfully!")
                r = result['result']
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Drug", r['drug'].title())
                    st.metric("Condition", r['condition'].title())
                    st.metric("Adjusted Daily Dose", f"{r['recommended_mg_per_day']} mg/day")
                with col2:
                    if r['per_dose_mg']:
                        st.metric("Per-Dose Amount", f"{r['per_dose_mg']} mg")
                        st.metric("Doses Per Day", r['doses_per_day'])
                    st.metric("Safety Range", f"{r['safety_range_mg_day'][0]}-{r['safety_range_mg_day'][1]} mg/day")
                st.info(f"**Rationale:** {r['rationale']}")
                if r.get('alert'):
                    st.warning(f"⚠️ **ALERT:** {r['alert']}")

            elif result.get('type') == 'REPORT':
                st.success(f"✅ Regimen report for Patient ID: {result['patient_id']}")
                entries = result['entries']
                if entries:
                    st.write(f"**Total Entries:** {len(entries)}")
                    for i, entry in enumerate(entries, 1):
                        with st.expander(f"Entry {i}: {entry.get('drug', 'N/A').title()}"):
                            st.json(entry)
                else:
                    st.info("No regimen entries found for this patient.")

            elif result.get('type') == 'ALERT_RULE':
                st.success("✅ Alert rule configured!")
                st.info(f"**Rule:** {result['rule']}")
                st.info(f"**Status:** {result['status']}")

            with st.expander("View Raw JSON Response"):
                st.json(result)

        except LexicalError as e:
            st.error(f"❌ **Lexical Error:** {str(e)}")
            st.session_state.result_history.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'command': command,
                'error': str(e),
                'error_type': 'LexicalError',
                'status': 'error'
            })
        except ParseError as e:
            st.error(f"❌ **Parse Error:** {str(e)}")
            st.session_state.result_history.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'command': command,
                'error': str(e),
                'error_type': 'ParseError',
                'status': 'error'
            })
        except UnknownDrugError as e:
            st.error(f"❌ **Unknown Drug Error:** {str(e)}")
            st.info("Please check the supported drugs list in the sidebar.")
            st.session_state.result_history.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'command': command,
                'error': str(e),
                'error_type': 'UnknownDrugError',
                'status': 'error'
            })
        except ExecutionError as e:
            st.error(f"❌ **Execution Error:** {str(e)}")
            st.session_state.result_history.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'command': command,
                'error': str(e),
                'error_type': 'ExecutionError',
                'status': 'error'
            })
        except Exception as e:
            st.error(f"❌ **Unexpected Error:** {str(e)}")
            st.session_state.result_history.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'command': command,
                'error': str(e),
                'error_type': 'Exception',
                'status': 'error'
            })

elif active == 'Results':
    st.header("Latest Results")
    if st.session_state.result_history:
        latest = st.session_state.result_history[-1]
        st.subheader(f"Executed at: {latest['timestamp']}")
        st.code(latest['command'], language="text")
        if latest['status'] == 'success':
            st.success("✅ Command executed successfully")
            with st.expander("View Full Results"):
                st.json(latest['result'])
        else:
            st.error(f"❌ Error: {latest.get('error_type', 'Unknown')}")
            st.write(latest.get('error', 'No error message'))
    else:
        st.info("No results yet. Execute a command in the Command Builder.")

elif active == 'History':
    st.header("Command History")
    if st.session_state.result_history:
        st.write(f"**Total Commands:** {len(st.session_state.result_history)}")
        for i, entry in enumerate(reversed(st.session_state.result_history), 1):
            with st.expander(f"{entry['timestamp']} - {entry['status'].upper()}"):
                st.code(entry['command'], language="text")
                if entry['status'] == 'success':
                    st.json(entry['result'])
                else:
                    st.error(f"**Error Type:** {entry.get('error_type', 'Unknown')}")
                    st.write(entry.get('error', 'No error message'))
        if st.button("🗑️ Clear History"):
            st.session_state.result_history = []
            st.session_state.command_history = []
            st.rerun()
    else:
        st.info("No command history yet.")

elif active == 'About':
    st.header("About This Application")
    st.markdown("""
    ### Medical Dosage Calculation Interpreter

    This application is a **domain-specific language (DSL) interpreter** designed for healthcare 
    professionals to calculate medication dosages, check drug interactions, validate prescriptions, 
    and manage patient medication regimens.

    #### Features

    - **✅ Automated Dose Calculations:** Computes appropriate medication doses based on patient 
      weight, age, and medical conditions while enforcing safety limits
    - **✅ Drug Interaction Checking:** Identifies potentially dangerous combinations of medications
    - **✅ Prescription Validation:** Verifies that prescribed doses fall within safe therapeutic ranges
    - **✅ Patient Regimen Management:** Tracks and reports medication histories for individual patients
    - **✅ Safety Alerts:** Raises warnings when computed doses exceed established safety thresholds

    #### Technology Stack

    - **Frontend:** Streamlit
    - **Backend:** Custom Python interpreter with lexer, parser, and executor
    - **Language:** Medical Prescription Language (MPL)

    #### Important Disclaimers

    ⚠️ **This is a demonstration tool for educational purposes only.**

    - This application is NOT approved for clinical use
    - Always consult with qualified healthcare professionals
    - Do not use for actual patient care without proper validation
    - Drug dosing rules are simplified for demonstration purposes

    #### Developed By

    **Software Bros And Programming Nerds (SBAPN)**
    - Besario, Adrian
    - Macatangay, Robin
    - Magat, Rolando
    - Villosa, Emmanuel

    CSS125L - Principles of Programming Languages Laboratory
    """)
    st.divider()
    st.subheader("System Architecture")
    st.image("https://via.placeholder.com/800x300?text=Lexer+%E2%86%92+Parser+%E2%86%92+AST+%E2%86%92+Executor+%E2%86%92+Results")
    st.markdown("""
    1. **Lexer:** Tokenizes raw command input
    2. **Parser:** Validates syntax and builds Abstract Syntax Tree
    3. **AST:** Structured representation of the command
    4. **Executor:** Processes command using drug rules
    5. **Results:** Returns calculation or error messages
    """)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <small>© 2025 Medical Dosage Calculator | For Educational Purposes Only</small>
</div>
""", unsafe_allow_html=True)

# Improve visuals: add card and badge styles
st.markdown("""
<style>
.card { background: var(--panel); border-radius: 16px; border: 1px solid rgba(255,255,255,.10); padding: 1rem 1.25rem; box-shadow: 0 12px 28px rgba(0,0,0,.35); }
.section-title { display:flex; align-items:center; gap:.5rem; font-weight:700; color: var(--primary-3); margin-bottom:.5rem; }
.page-badge { display:inline-block; padding:.25rem .6rem; border-radius:999px; background:#0e1a2b; border:1px solid rgba(20,184,166,.35); color:var(--primary-3); font-size:.8rem; }
</style>
""", unsafe_allow_html=True)

if active == 'Interact':
    st.markdown('<div class="page-badge">Check Interaction</div>', unsafe_allow_html=True)
    st.header("Check Interaction")
    drugs = [
        "amlodipine", "losartan", "metformin", "glimepiride",
        "amoxicillin", "azithromycin", "paracetamol",
        "ibuprofen", "salbutamol", "montelukast"
    ]
    col1, col2 = st.columns(2)
    with col1:
        drug_a = st.selectbox("Drug A", options=drugs, index=1)
    with col2:
        drug_b = st.selectbox("Drug B", options=drugs, index=0)
    if drug_a == drug_b:
        st.warning("Select two different drugs to check interactions.")
    command = f"CHECK INTERACTION BETWEEN {drug_a} AND {drug_b}"
    execute_btn = st.button("▶️ Execute", type="primary")
    if execute_btn and command.strip():
        try:
            result = run(command)
            st.session_state.command_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command})
            st.session_state.result_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'result': result,'status': 'success'})
            st.session_state.active_tab = 'Results'
            st.rerun()
        except Exception as e:
            st.error(str(e))
elif active == 'Validate':
    st.markdown('<div class="page-badge">Validate Prescription</div>', unsafe_allow_html=True)
    st.header("Validate Prescription")
    drugs = [
        "amlodipine", "losartan", "metformin", "glimepiride",
        "amoxicillin", "azithromycin", "paracetamol",
        "ibuprofen", "salbutamol", "montelukast"
    ]
    col1, col2 = st.columns(2)
    with col1:
        v_drug = st.selectbox("Drug", options=drugs, index=0, key="val_drug_page")
    with col2:
        dose = st.number_input("Dose (mg/day)", min_value=0.0, max_value=5000.0, value=500.0, step=50.0)
    command = f"VALIDATE PRESCRIPTION drug={v_drug}, dose={int(dose)}mg"
    execute_btn = st.button("▶️ Execute", type="primary")
    if execute_btn and command.strip():
        try:
            result = run(command)
            st.session_state.command_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command})
            st.session_state.result_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'result': result,'status': 'success'})
            st.session_state.active_tab = 'Results'
            st.rerun()
        except Exception as e:
            st.error(str(e))
else:
    st.info("No results yet. Execute a command in the Command Builder.")
    st.rerun()
    st.markdown("""
    1. **Lexer:** Tokenizes raw command input
    2. **Parser:** Validates syntax and builds Abstract Syntax Tree
    3. **AST:** Structured representation of the command
    4. **Executor:** Processes command using drug rules
    5. **Results:** Returns calculation or error messages
    """)

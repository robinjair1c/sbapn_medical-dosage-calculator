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
    .block-container { padding-top: 3rem; }

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
# Added unified page section state and per-section latest results
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'Actions'
if 'active_section' not in st.session_state:
    st.session_state.active_section = 'calc'
if 'section_results' not in st.session_state:
    st.session_state.section_results = {'calc': None, 'interact': None, 'validate': None}

# Cached data helpers (fix NameError)
@st.cache_data
def get_drugs():
    return [
        "amlodipine", "losartan", "metformin", "glimepiride",
        "amoxicillin", "azithromycin", "paracetamol",
        "ibuprofen", "salbutamol", "montelukast"
    ]

@st.cache_data
def get_condition_map():
    return {
        "amlodipine": ["hypertension"],
        "losartan": ["hypertension"],
        "metformin": ["diabetes"],
        "glimepiride": ["diabetes"],
        "amoxicillin": ["infection"],
        "azithromycin": ["infection"],
        "paracetamol": ["pain", "fever"],
        "ibuprofen": ["pain", "fever"],
        "salbutamol": ["asthma"],
        "montelukast": ["asthma"],
    }

# Helper: render result in original format
# (defined before routing to avoid breaking if/elif chain)

def render_original_output(result_dict: dict):
    res_type = result_dict.get('type')
    if res_type in ('CALCULATE','ADJUST'):
        r = result_dict['result']
        if res_type == 'CALCULATE':
            st.success("✅ Dose calculation completed successfully!")
        else:
            st.success("✅ Dose adjustment completed successfully!")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Drug", r['drug'].title())
            st.metric("Condition", r['condition'].title())
            label = "Recommended Daily Dose" if res_type == 'CALCULATE' else "Adjusted Daily Dose"
            st.metric(label, f"{r['recommended_mg_per_day']} mg/day")
        with col2:
            if r.get('per_dose_mg'):
                st.metric("Per-Dose Amount", f"{r['per_dose_mg']} mg")
                st.metric("Doses Per Day", r['doses_per_day'])
            sr = r.get('safety_range_mg_day')
            if sr:
                st.metric("Safety Range", f"{sr[0]}-{sr[1]} mg/day")
        st.info(f"**Rationale:** {r.get('rationale','')}")
        if r.get('alert'):
            st.warning(f"⚠️ **ALERT:** {r['alert']}")
    elif res_type == 'CHECK':
        st.success("✅ Interaction check completed!")
        st.info(f"**Interaction:** {result_dict['interaction']}")
    elif res_type == 'VALIDATE':
        r = result_dict['result']
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
    elif res_type == 'REPORT':
        st.success(f"✅ Regimen report for Patient ID: {result_dict['patient_id']}")
        entries = result_dict.get('entries', [])
        if entries:
            st.write(f"**Total Entries:** {len(entries)}")
            for i, entry in enumerate(entries, 1):
                show = st.checkbox(f"Show Entry {i}: {entry.get('drug', 'N/A').title()}", key=f"report_show_{i}")
                if show:
                    st.json(entry)
        else:
            st.info("No regimen entries found for this patient.")
    elif res_type == 'ALERT_RULE':
        st.success("✅ Alert rule configured!")
        st.info(f"**Rule:** {result_dict['rule']}")
        st.info(f"**Status:** {result_dict['status']}")

# Header
st.markdown('<div class="main-header">💊 Medical Dosage Calculation Interpreter</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Software Bros And Programming Nerds</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Navigation")
    st.markdown('<div class="page-badge">Actions</div>', unsafe_allow_html=True)
    if st.button("🧮 Calculate Dose", use_container_width=True):
        st.session_state.active_tab = "Actions"
        st.session_state.active_section = "calc"
        st.rerun()
    if st.button("⚖️ Check Interaction", use_container_width=True):
        st.session_state.active_tab = "Actions"
        st.session_state.active_section = "interact"
        st.rerun()
    if st.button("✅ Validate Prescription", use_container_width=True):
        st.session_state.active_tab = "Actions"
        st.session_state.active_section = "validate"
        st.rerun()
    st.divider()
    if st.button("📝 History", use_container_width=True):
        st.session_state.active_tab = "History"
        st.rerun()
    if st.button("ℹ️ About", use_container_width=True):
        st.session_state.active_tab = "About"
        st.rerun()

# Main content area
active = st.session_state.active_tab
# Add navigation guardrails
allowed_tabs = {'Actions','History','About','Interact','Validate','Results'}
if active not in allowed_tabs:
    st.warning(f"Unknown tab '{active}'. Redirecting to Actions.")
    st.session_state.active_tab = 'Actions'
    active = 'Actions'

# Unified Actions page with three sections, results inline
if active == 'Actions':
    sections = ['calc','interact','validate']
    active_section = st.session_state.get('active_section','calc')
    # Keep original section order; emphasize selected via expanded expander
    for sec in sections:
        if sec == 'calc':
            with st.expander("🧮 Calculate Dose", expanded=(active_section=='calc')):
                st.header("Calculate Dose")
                drugs = get_drugs()
                condition_map = get_condition_map()
                col1, col2 = st.columns(2)
                with col1:
                    sel_drug = st.selectbox("Drug", options=drugs, index=2, key="calc_drug")
                    cond_opts = condition_map.get(sel_drug, ["general"]) 
                    sel_condition = st.selectbox("Condition", options=cond_opts, index=0, key="calc_condition")
                with col2:
                    weight = st.number_input("Weight (kg)", min_value=1.0, max_value=300.0, value=70.0, step=0.5, key="calc_weight")
                    age = st.number_input("Age", min_value=0, max_value=120, value=45, step=1, key="calc_age")
                    kidney_function = st.selectbox("Kidney Function", options=["normal","impaired","reduced","ckd"], index=0, key="calc_kidney")
                command = f"CALCULATE DOSE FOR drug={sel_drug}, condition={sel_condition}, weight={weight}kg, age={int(age)}, kidney_function={kidney_function}"
                execute_btn = st.button("▶️ Execute", type="primary", key="calc_execute")
                if execute_btn and command.strip():
                    try:
                        result = run(command)
                        st.session_state.command_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command})
                        st.session_state.result_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'result': result,'status': 'success'})
                        st.session_state.command_history = st.session_state.command_history[-200:]
                        st.session_state.result_history = st.session_state.result_history[-200:]
                        st.session_state.section_results['calc'] = {'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'result': result,'status': 'success'}
                        st.session_state.active_section = 'calc'
                        st.rerun()
                    except Exception as e:
                        st.error(f"Execution failed: {str(e)}")
                        st.session_state.section_results['calc'] = {'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'error': str(e),'error_type': 'Exception','status': 'error'}
                        st.session_state.result_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'error': str(e),'error_type': 'Exception','status': 'error'})
                        st.session_state.result_history = st.session_state.result_history[-200:]
                latest = st.session_state.section_results.get('calc')
                if latest:
                    st.caption(f"Last executed at {latest['timestamp']}")
                    if latest.get('status') == 'error':
                        st.error(f"❌ Execution error: {latest.get('error_type','Error')} — {latest.get('error','')}")
                        st.code(latest.get('command',''), language='text')
                    else:
                        render_original_output(latest.get('result', {}))
                        show_raw = st.checkbox("Show Raw Output", key="calc_show_raw")
                        if show_raw:
                            st.json(latest.get('result', {}))
                        st.write(f"Command: `{latest.get('command','')}`")
            st.markdown("<hr>", unsafe_allow_html=True)
        elif sec == 'interact':
            with st.expander("⚖️ Check Interaction", expanded=(active_section=='interact')):
                st.header("Check Interaction")
                drugs = get_drugs()
                col1, col2 = st.columns(2)
                with col1:
                    drug_a = st.selectbox("Drug A", options=drugs, index=1, key="interact_a")
                with col2:
                    drug_b = st.selectbox("Drug B", options=drugs, index=0, key="interact_b")
                if drug_a == drug_b:
                    st.warning("Select two different drugs to check interactions.")
                command = f"CHECK INTERACTION BETWEEN {drug_a} AND {drug_b}"
                execute_btn = st.button("▶️ Execute", type="primary", key="interact_execute")
                if execute_btn and command.strip():
                    try:
                        result = run(command)
                        st.session_state.command_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command})
                        st.session_state.result_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'result': result,'status': 'success'})
                        st.session_state.command_history = st.session_state.command_history[-200:]
                        st.session_state.result_history = st.session_state.result_history[-200:]
                        st.session_state.section_results['interact'] = {'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'result': result,'status': 'success'}
                        st.session_state.active_section = 'interact'
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                        st.session_state.section_results['interact'] = {'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'error': str(e),'error_type': 'Exception','status': 'error'}
                        st.session_state.result_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'error': str(e),'error_type': 'Exception','status': 'error'})
                        st.session_state.result_history = st.session_state.result_history[-200:]
                latest = st.session_state.section_results.get('interact')
                if latest:
                    st.caption(f"Last executed at {latest['timestamp']}")
                    if latest.get('status') == 'error':
                        st.error(f"❌ Execution error: {latest.get('error_type','Error')} — {latest.get('error','')}")
                        st.code(latest.get('command',''), language='text')
                    else:
                        render_original_output(latest.get('result', {}))
                        show_raw = st.checkbox("Show Raw Output", key="interact_show_raw")
                        if show_raw:
                            st.json(latest.get('result', {}))
                        st.write(f"Command: `{latest.get('command','')}`")
            st.markdown("<hr>", unsafe_allow_html=True)
        elif sec == 'validate':
            with st.expander("✅ Validate Prescription", expanded=(active_section=='validate')):
                st.header("Validate Prescription")
                drugs = get_drugs()
                col1, col2 = st.columns(2)
                with col1:
                    v_drug = st.selectbox("Drug", options=drugs, index=0, key="val_drug_page")
                with col2:
                    dose = st.number_input("Dose (mg/day)", min_value=0.0, max_value=5000.0, value=500.0, step=50.0, key="val_dose_page")
                command = f"VALIDATE PRESCRIPTION drug={v_drug}, dose={int(dose)}mg"
                execute_btn = st.button("▶️ Execute", type="primary", key="validate_execute")
                if execute_btn and command.strip():
                    try:
                        result = run(command)
                        st.session_state.command_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command})
                        st.session_state.result_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'result': result,'status': 'success'})
                        st.session_state.command_history = st.session_state.command_history[-200:]
                        st.session_state.result_history = st.session_state.result_history[-200:]
                        st.session_state.section_results['validate'] = {'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'result': result,'status': 'success'}
                        st.session_state.active_section = 'validate'
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                        st.session_state.section_results['validate'] = {'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'error': str(e),'error_type': 'Exception','status': 'error'}
                        st.session_state.result_history.append({'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'command': command,'error': str(e),'error_type': 'Exception','status': 'error'})
                        st.session_state.result_history = st.session_state.result_history[-200:]
                latest = st.session_state.section_results.get('validate')
                if latest:
                    st.caption(f"Last executed at {latest['timestamp']}")
                    if latest.get('status') == 'error':
                        st.error(f"❌ Execution error: {latest.get('error_type','Error')} — {latest.get('error','')}")
                        st.code(latest.get('command',''), language='text')
                    else:
                        render_original_output(latest.get('result', {}))
                        show_raw = st.checkbox("Show Raw Output", key="validate_show_raw")
                        if show_raw:
                            st.json(latest.get('result', {}))
                        st.write(f"Command: `{latest.get('command','')}`")
            st.markdown("<hr>", unsafe_allow_html=True)

# Disable legacy individual tabs migrated into Actions page
elif active == 'Interact':
    # migrated into Actions page
    pass
elif active == 'Validate':
    # migrated into Actions page
    pass
elif active == 'Results':
    # removed standalone Results tab; results now inline under sections
    pass

# History and About remain the same below
elif active == 'History':
    st.header("History")
    try:
        if not st.session_state.command_history and not st.session_state.result_history:
            st.info("No history yet. Execute commands to populate history.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Commands")
                for item in st.session_state.command_history[-50:]:
                    st.write(f"- `{item['timestamp']}` — `{item['command']}`")
            with col2:
                st.subheader("Results")
                for item in st.session_state.result_history[-50:]:
                    status = item.get('status','success')
                    label = "✅ Success" if status != 'error' else "❌ Error"
                    st.write(f"- `{item['timestamp']}` — {label}")
                    with st.expander(item.get('command','(unknown)')):
                        if status == 'error':
                            st.error(item.get('error',''))
                        else:
                            st.json(item.get('result', {}))
    except Exception as e:
        st.error(f"Failed to render History: {str(e)}")

elif active == 'About':
    st.header("About")
    try:
        st.write("Medical Dosage Calculation Interpreter — Software Bros And Programming Nerds.")
        st.write("Use the action sections to construct and execute commands. Results render inline under each section; the History tab records activity.")
        st.write("Performance guardrails applied: capped histories and cached data. Validation harness and tests are available in the repo.")
    except Exception as e:
        st.error(f"Failed to render About: {str(e)}")

# Fallback
else:
    st.info("Select an action from the sidebar to get started.")

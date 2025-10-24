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
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
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
    st.header("📋 Quick Guide")

    st.subheader("Supported Commands")
    st.markdown("""
    1. **CALCULATE DOSE FOR**
       - Calculate medication dosage
    2. **CHECK INTERACTION BETWEEN**
       - Check drug interactions
    3. **ADJUST DOSE FOR**
       - Adjust dose with patient factors
    4. **VALIDATE PRESCRIPTION**
       - Validate prescribed dose
    5. **REPORT REGIMEN**
       - Get patient medication history
    6. **ALERT WHEN DOSE EXCEEDS SAFETY_LIMIT**
       - Configure alerts
    """)

    st.subheader("Supported Drugs")
    drugs = [
        "amlodipine", "losartan", "metformin", "glimepiride",
        "amoxicillin", "azithromycin", "paracetamol",
        "ibuprofen", "salbutamol", "montelukast"
    ]
    st.markdown("\n".join([f"- {drug}" for drug in drugs]))

    st.subheader("Example Commands")
    st.code("CALCULATE DOSE FOR drug=metformin, condition=diabetes, weight=70kg, age=45", language="text")
    st.code("CHECK INTERACTION BETWEEN losartan AND ibuprofen", language="text")
    st.code("VALIDATE PRESCRIPTION drug=amlodipine, dose=5mg", language="text")

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["🩺 Command Input", "📊 Results", "📝 History", "ℹ️ About"])

with tab1:
    st.header("Enter Medical Command")

    # Command templates
    st.subheader("Quick Templates")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Calculate Dose", use_container_width=True):
            st.session_state.command_template = "CALCULATE DOSE FOR drug=, condition=, weight=kg, age="
    with col2:
        if st.button("Check Interaction", use_container_width=True):
            st.session_state.command_template = "CHECK INTERACTION BETWEEN  AND "
    with col3:
        if st.button("Validate Prescription", use_container_width=True):
            st.session_state.command_template = "VALIDATE PRESCRIPTION drug=, dose=mg"

    # Command input
    default_command = st.session_state.get('command_template', '')
    command = st.text_area(
        "Command:",
        value=default_command,
        height=100,
        placeholder="Enter your medical command here...",
        help="Type or use templates above"
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        execute_btn = st.button("▶️ Execute", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)

    if clear_btn:
        st.session_state.command_template = ''
        st.rerun()

    if execute_btn and command.strip():
        st.divider()
        st.subheader("Execution Results")

        try:
            # Execute the command
            result = run(command)

            # Store in history
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

            # Display results based on command type
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

            # Show raw JSON in expander
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

with tab2:
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
        st.info("No results yet. Execute a command in the 'Command Input' tab.")

with tab3:
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

with tab4:
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

# Medical Prescription Interpreter System

## Project Overview
This project implements a Medical Prescription Interpreter — a domain-specific language interpreter designed for healthcare professionals to calculate medication dosages, check drug interactions, validate prescriptions, and manage patient medication regimens. It aims to reduce medication errors and improve patient safety by automating complex dose calculations with safety checks based on clinical rules.

## Project Streamlit Application Link: https://sbapn-medical-dosage-calculator.streamlit.app/

## Authors
**Group: Software Bros And Programming Nerds (SBAPN)**

**Members:**
- Besario, Adrian
- Macatangay, Robin
- Magat, Rolando
- Villosa, Emmanuel

## Features
- Custom interpreter for structured medical dosage commands
- Supports commands like `CALCULATE DOSE FOR`, `CHECK INTERACTION BETWEEN`, `VALIDATE PRESCRIPTION`, and more
- Implements safety alerting for doses exceeding predefined limits
- Handles patient-specific adjustments based on age, weight, and kidney function
- Comprehensive error handling and meaningful feedback
- Fully implemented in Python with clear modular design

## Setup and Usage

### Prerequisites
- Python 3.10 or newer
- No external libraries required (only Python standard library)

### Running Locally
1. Download all `.py` files and the Jupyter notebook (`SBAPN_Machine_Project.ipynb`) into the same directory.
2. Open the Jupyter notebook with:
    ```
    jupyter notebook SBAPN_Machine_Project.ipynb
    ```
3. Run all cells sequentially to load modules and test the interpreter.
4. Use the example commands in the Testing section to validate functionality.

### Running on Google Colab
1. Upload all `.py` files and the notebook to your Google Drive.
2. Open the notebook `SBAPN_Machine_Project.ipynb` in Colab.
3. If using files from Drive, mount Drive with:
    ```
    from google.colab import drive
    drive.mount('/content/drive')
    ```
4. Change paths as needed to reference files in Drive, or upload files directly to the Colab environment.
5. Run the notebook cells to load and test the interpreter.

## File Structure
- `SBAPN_Machine_Project.ipynb` — Main notebook containing all code and documentation.
- `tokens.py`, `lexer.py`, `parser.py`, `ast_nodes.py`, `interpreter.py`, `executor.py`, `rules.py`, `errors.py`, `init.py` — Python modules implementing the interpreter.

## Notes
- Ensure all `.py` files are in the same folder when running locally.
- For Google Colab, upload or link files as needed, because unlike local runs, files aren't persistent between sessions.
- If issues regarding `.py` files ariase, modify the imports in the `.py` files to remove relative import dots (`from .tokens` → `from tokens`) for notebook compatibility.


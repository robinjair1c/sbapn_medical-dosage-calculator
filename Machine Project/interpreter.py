from __future__ import annotations
from typing import Dict, Any
from lexer import lex
from parser import Parser
from errors import InterpreterError, SafetyLimitExceeded
from ast_nodes import *
from executor import (
    normalize_ctx, compute_dose, check_interaction, validate_prescription,
    record_regimen, report_regimen, enforce_alerts
)


def run(source: str) -> Dict[str, Any]:
    tokens = lex(source)
    node = Parser(tokens).parse()
    if isinstance(node, CalculateDose):
        ctx = normalize_ctx(node.params)
        result = compute_dose(ctx)
        if "patient_id" in ctx:
            rec = {"type": "dose", **result}
            record_regimen(ctx["patient_id"], rec)
        return {"type": "CALCULATE", "result": result}
    if isinstance(node, CheckInteraction):
        msg = check_interaction(node.params["drug_a"], node.params["drug_b"])
        return {"type": "CHECK", "interaction": msg}
    if isinstance(node, AdjustDose):
        ctx = normalize_ctx(node.params)
        if "drug" not in ctx or "condition" not in ctx:
            raise InterpreterError("ADJUST requires at least 'drug' and 'condition' plus modifiers like age or kidney_function")
        result = compute_dose(ctx)
        return {"type": "ADJUST", "result": result}
    if isinstance(node, ValidatePrescription):
        ctx = normalize_ctx(node.params)
        drug = ctx.get("drug")
        total = ctx.get("dose_mg_input")
        if drug is None or total is None:
            raise InterpreterError("VALIDATE requires 'drug' and 'dose'")
        res = validate_prescription(drug, total)
        return {"type": "VALIDATE", "result": res}
    if isinstance(node, ReportRegimen):
        ctx = normalize_ctx(node.params)
        pid = ctx.get("patient_id")
        if not pid:
            raise InterpreterError("REPORT requires patient_id=<id>")
        data = report_regimen(pid)
        return {"type": "REPORT", "patient_id": pid, "entries": data}
    if isinstance(node, AlertThreshold):
        return {"type": "ALERT_RULE", "rule": "dose_exceeds_safety_limit", "status": "armed (demo)"}
    raise InterpreterError("Unsupported command type")

def run_and_raise_on_alert(source: str) -> Dict[str, Any]:
    out = run(source)
    if out.get("type") in ("CALCULATE","ADJUST"):
        try:
            enforce_alerts(out["result"])
        except SafetyLimitExceeded as e:
            raise
    return out

from __future__ import annotations
from typing import Dict, Any, Tuple
import json, os
from errors import ExecutionError, UnknownDrugError, UnknownConditionError, SafetyLimitExceeded
from rules import DRUG_RULES, INTERACTIONS

STATE_FILE = os.path.join(os.getcwd(), "regimens.json")

def _load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)

    return {"patients": {}}

def _save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def parse_number_unit(value: str) -> tuple[float, str | None]:
    import re
    m = re.match(r"^(\d+(?:\.\d+)?)([A-Za-z/]+)?$", value)
    if not m:
        raise ExecutionError(f"Invalid numeric value '{value}'")
    n = float(m.group(1))
    unit = m.group(2)
    return n, unit

def normalize_ctx(params):
    ctx = {}
    p = {str(k).lower(): v for k, v in params.items()}
    if "weight" in p:
        n, u = parse_number_unit(p["weight"])
        if u and u.lower() != "kg":
            raise ExecutionError(f"Expected weight in kg, got '{u}'")
        ctx["weight_kg"] = n
    if "age" in p:
        n, u = parse_number_unit(p["age"])
        ctx["age"] = int(n)
        ctx["elderly"] = ctx["age"] >= 65
    if "kidney_function" in p:
        ctx["kidney_function"] = p["kidney_function"].lower()
        ctx["renal_impaired"] = ctx["kidney_function"] in ("impaired", "reduced", "ckd")
    if "condition" in p:
        ctx["condition"] = p["condition"].lower()
    if "patient_id" in p:
        ctx["patient_id"] = str(p["patient_id"])
    if "drug" in p:
        ctx["drug"] = p["drug"].lower()
    if "dose" in p:
        n, u = parse_number_unit(p["dose"])
        if u and u.lower() not in ("mg", "mcg", "g"):
            raise ExecutionError(f"Unsupported dose unit '{u}'")
        factor = {"mg": 1.0, "mcg": 0.001, "g": 1000.0}.get((u or "mg").lower(), 1.0)
        ctx["dose_mg_input"] = n * factor
    return ctx


def compute_dose(ctx: Dict[str, Any]) -> Dict[str, Any]:
    drug = ctx.get("drug")
    condition = ctx.get("condition")
    if not drug:
        raise ExecutionError("Missing parameter: drug")
    if condition is None:
        raise ExecutionError("Missing parameter: condition")
    rule = DRUG_RULES.get(drug)
    if not rule:
        raise UnknownDrugError(drug)
    mg_day, rationale = rule.calculator(ctx)
    adjust = 1.0
    if ctx.get("renal_impaired", False):
        adjust *= rule.renal_adjust_factor
    if ctx.get("elderly", False):
        adjust *= rule.elderly_adjust_factor
    adjusted = mg_day * adjust
    low, high = rule.safe_range
    alert = None
    if adjusted > high:
        alert = f"computed {adjusted:.0f} mg/day exceeds safety limit {high:.0f} mg/day"
    if adjusted < low:
        if low > 0:
            alert = (alert or "") + ("" if alert is None else "; ") + f"computed {adjusted:.0f} mg/day below typical minimum {low:.0f} mg/day"
    per_dose = None
    if rule.max_single_dose_mg:
        doses = max(1, int(round(adjusted / rule.max_single_dose_mg)))
        per_dose = min(rule.max_single_dose_mg, adjusted / doses)
    return {
        "drug": drug,
        "condition": condition,
        "recommended_mg_per_day": round(adjusted, 2),
        "per_dose_mg": None if per_dose is None else round(per_dose, 2),
        "doses_per_day": None if per_dose is None else max(1, int(round(adjusted / per_dose))),
        "rationale": rationale + (f"; adjustments factor={adjust:.2f}" if adjust != 1.0 else ""),
        "safety_range_mg_day": (low, high),
        "alert": alert,
    }

def check_interaction(drug_a: str, drug_b: str) -> str:
    a, b = drug_a.lower(), drug_b.lower()
    key = frozenset([a,b])
    return INTERACTIONS.get(key, "no known interaction in demo database")

def validate_prescription(drug: str, dose_mg: float) -> Dict[str, Any]:
    rule = DRUG_RULES.get(drug)
    if not rule:
        raise UnknownDrugError(drug)
    low, high = rule.safe_range
    status = "OK"
    message = "within safety range"
    alert = None
    if dose_mg > high:
        status = "EXCEEDS"
        message = f"dose {dose_mg:.0f} mg/day exceeds safety limit {high:.0f} mg/day"
        alert = message
    elif dose_mg < low and low > 0:
        status = "LOW"
        message = f"dose {dose_mg:.0f} mg/day below typical minimum {low:.0f} mg/day"
    return {"drug": drug, "dose_mg_per_day": dose_mg, "status": status, "message": message, "alert": alert}

def record_regimen(patient_id: str, entry: Dict[str, Any]):
    state = _load_state()
    state["patients"].setdefault(patient_id, []).append(entry)
    _save_state(state)

def report_regimen(patient_id: str):
    state = _load_state()
    return state["patients"].get(patient_id, [])

def enforce_alerts(result: Dict[str, Any]) -> None:
    if result.get("alert"):
        raise SafetyLimitExceeded(result["alert"], computed=result["recommended_mg_per_day"], limit=result["safety_range_mg_day"][1])

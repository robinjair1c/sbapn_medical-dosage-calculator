from dataclasses import dataclass
from typing import Callable, Optional, Dict, Tuple

@dataclass
class DrugRule:
    calculator: Callable[[dict], Tuple[float, str]]
    safe_range: Tuple[float, float]
    max_single_dose_mg: Optional[float] = None
    renal_adjust_factor: float = 1.0
    elderly_adjust_factor: float = 1.0

def per_kg_mg_day(mg_per_kg: float, cap: float):
    def calc(ctx):
        wt = ctx.get("weight_kg")
        if wt is None:
            return (0.0, "No weight provided; cannot compute per-kg dose.")
        val = mg_per_kg * wt
        return (min(val, cap), f"{mg_per_kg} mg/kg/day capped at {cap} mg/day")
    return calc

def fixed_mg_day(amount: float):
    def calc(ctx):
        return (amount, f"Fixed {amount} mg/day")
    return calc

def condition_based(default: float, by_condition: Dict[str, float], cap: float | None = None):
    def calc(ctx):
        cond = ctx.get("condition")
        base = by_condition.get(cond, default)
        if cap is not None and base > cap:
            return (cap, f"Condition-based {base} mg/day capped at {cap}")
        return (base, f"Condition-based {base} mg/day for {cond}")
    return calc

DRUG_RULES: Dict[str, DrugRule] = {
    "amlodipine": DrugRule(
        calculator=condition_based(5.0, {"hypertension": 5.0}, cap=10.0),
        safe_range=(2.5, 10.0),
        max_single_dose_mg=10.0,
        elderly_adjust_factor=0.8
    ),
    "losartan": DrugRule(
        calculator=condition_based(50.0, {"hypertension": 50.0}, cap=100.0),
        safe_range=(25.0, 100.0),
        max_single_dose_mg=100.0,
        renal_adjust_factor=0.8,
        elderly_adjust_factor=0.9
    ),
    "metformin": DrugRule(
        calculator=per_kg_mg_day(20.0, cap=2000.0),
        safe_range=(500.0, 2000.0),
        max_single_dose_mg=1000.0,
        renal_adjust_factor=0.5,
        elderly_adjust_factor=0.8
    ),
    "glimepiride": DrugRule(
        calculator=condition_based(2.0, {"diabetes": 2.0}, cap=8.0),
        safe_range=(1.0, 8.0),
        max_single_dose_mg=4.0
    ),
    "amoxicillin": DrugRule(
        calculator=per_kg_mg_day(30.0, cap=1500.0),
        safe_range=(500.0, 1500.0),
        max_single_dose_mg=1000.0,
        renal_adjust_factor=0.5
    ),
    "azithromycin": DrugRule(
        calculator=per_kg_mg_day(10.0, cap=500.0),
        safe_range=(250.0, 500.0),
        max_single_dose_mg=500.0
    ),
    "paracetamol": DrugRule(
        calculator=per_kg_mg_day(60.0, cap=4000.0),
        safe_range=(0.0, 4000.0),
        max_single_dose_mg=1000.0
    ),
    "ibuprofen": DrugRule(
        calculator=per_kg_mg_day(20.0, cap=1200.0),
        safe_range=(0.0, 1200.0),
        max_single_dose_mg=400.0
    ),
    "salbutamol": DrugRule(
        calculator=per_kg_mg_day(0.3, cap=12.0),
        safe_range=(2.0, 12.0),
        max_single_dose_mg=4.0
    ),
    "montelukast": DrugRule(
        calculator=fixed_mg_day(10.0),
        safe_range=(5.0, 10.0),
        max_single_dose_mg=10.0
    ),
}

INTERACTIONS: Dict[frozenset[str], str] = {
    frozenset(["losartan", "ibuprofen"]): "caution: NSAIDs may blunt antihypertensive effect",
    frozenset(["azithromycin", "amlodipine"]): "caution: potential hypotension risk",
    frozenset(["amlodipine", "losartan"]): "no significant interaction reported (commonly co-prescribed)",
}

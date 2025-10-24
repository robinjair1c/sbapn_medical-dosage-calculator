from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class Command:
    name: str
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CalculateDose(Command):
    pass

@dataclass
class CheckInteraction(Command):
    pass

@dataclass
class AdjustDose(Command):
    pass

@dataclass
class ValidatePrescription(Command):
    pass

@dataclass
class ReportRegimen(Command):
    pass

@dataclass
class AlertThreshold(Command):
    pass

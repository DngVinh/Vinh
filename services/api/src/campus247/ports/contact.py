from typing import Protocol, Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class ContactInfo:
    phone: str
    description: str

class ContactConfigPort(Protocol):
    def get_emergency_contact(self) -> Optional[ContactInfo]:
        ...

class AlertPort(Protocol):
    def emit_operational_alert(self, code: str, message: str) -> None:
        ...

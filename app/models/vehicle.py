from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Vehicle:
    plate: str
    max_weight: float
    id: UUID = field(default_factory=uuid4)

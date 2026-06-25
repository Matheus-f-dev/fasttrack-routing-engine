from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Package:
    recipient_name: str
    destination_x: float
    destination_y: float
    weight: float
    access_cost: float
    id: UUID = field(default_factory=uuid4)

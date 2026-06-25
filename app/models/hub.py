from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Hub:
    name: str
    x: float
    y: float
    is_main: bool = False
    id: UUID = field(default_factory=uuid4)

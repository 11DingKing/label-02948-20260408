"""BPMN element data models."""
from dataclasses import dataclass, field


@dataclass
class BpmnElement:
    """Base BPMN element."""
    id: str
    name: str = ""
    element_type: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0


@dataclass
class BpmnNode(BpmnElement):
    """A BPMN node (task, event, gateway)."""
    incoming: list = field(default_factory=list)
    outgoing: list = field(default_factory=list)


@dataclass
class BpmnEdge(BpmnElement):
    """A BPMN sequence flow / connection."""
    source_ref: str = ""
    target_ref: str = ""
    waypoints: list = field(default_factory=list)
    label: str = ""
    label_x: float = 0.0
    label_y: float = 0.0

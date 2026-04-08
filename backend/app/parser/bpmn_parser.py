"""BPMN XML parser - extracts elements and diagram info from .bpmn files."""
import logging

from lxml import etree

from ..exceptions import BpmnParseError
from .models import BpmnEdge, BpmnNode

logger = logging.getLogger(__name__)

# BPMN 2.0 namespaces
NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
}

# Element type classification
EVENT_TYPES = {
    "startEvent", "endEvent", "intermediateCatchEvent",
    "intermediateThrowEvent", "boundaryEvent",
}
TASK_TYPES = {
    "task", "userTask", "serviceTask", "scriptTask",
    "businessRuleTask", "sendTask", "receiveTask", "manualTask",
    "callActivity", "subProcess",
}
GATEWAY_TYPES = {
    "exclusiveGateway", "parallelGateway", "inclusiveGateway",
    "eventBasedGateway", "complexGateway",
}
FLOW_TYPES = {"sequenceFlow", "messageFlow", "association"}


class BpmnParser:
    """Parses a BPMN 2.0 XML file into structured data."""

    def __init__(self):
        self.nodes: dict[str, BpmnNode] = {}
        self.edges: list[BpmnEdge] = []
        self._shapes: dict[str, dict] = {}
        self._edge_data: dict[str, dict] = {}

    def parse(self, bpmn_content: str) -> tuple[dict[str, BpmnNode], list[BpmnEdge]]:
        """Parse BPMN XML content and return nodes and edges."""
        # Reset state to avoid cross-call data contamination
        self.nodes = {}
        self.edges = []
        self._shapes = {}
        self._edge_data = {}

        try:
            # Secure parser: disable DTD, external entities, and network access
            # to prevent XXE (XML External Entity) attacks
            secure_parser = etree.XMLParser(
                resolve_entities=False,
                no_network=True,
                dtd_validation=False,
                load_dtd=False,
            )
            raw = bpmn_content.encode("utf-8") if isinstance(bpmn_content, str) else bpmn_content
            root = etree.fromstring(raw, parser=secure_parser)
        except etree.XMLSyntaxError as e:
            logger.error("XML syntax error: %s", e)
            raise BpmnParseError(f"Invalid XML: {e}") from e

        self._parse_diagram(root)
        self._parse_process(root)
        self._apply_positions()

        logger.info("Parsed %d nodes and %d edges", len(self.nodes), len(self.edges))
        return self.nodes, self.edges

    def _parse_diagram(self, root):
        """Extract shape positions and edge waypoints from BPMNDiagram."""
        for shape in root.iter(f"{{{NS['bpmndi']}}}BPMNShape"):
            element_id = shape.get("bpmnElement", "")
            bounds = shape.find(f"{{{NS['dc']}}}Bounds")
            if bounds is not None:
                self._shapes[element_id] = {
                    "x": float(bounds.get("x", 0)),
                    "y": float(bounds.get("y", 0)),
                    "width": float(bounds.get("width", 0)),
                    "height": float(bounds.get("height", 0)),
                }

        for edge_el in root.iter(f"{{{NS['bpmndi']}}}BPMNEdge"):
            element_id = edge_el.get("bpmnElement", "")
            waypoints = []
            for wp in edge_el.findall(f"{{{NS['di']}}}waypoint"):
                waypoints.append((float(wp.get("x", 0)), float(wp.get("y", 0))))
            label_bounds = edge_el.find(f".//{{{NS['dc']}}}Bounds")
            label_x, label_y = 0.0, 0.0
            if label_bounds is not None:
                label_x = float(label_bounds.get("x", 0))
                label_y = float(label_bounds.get("y", 0))
            self._edge_data[element_id] = {
                "waypoints": waypoints,
                "label_x": label_x,
                "label_y": label_y,
            }

    def _parse_process(self, root):
        """Extract process elements (nodes and flows)."""
        for process in root.iter(f"{{{NS['bpmn']}}}process"):
            self._parse_elements_recursive(process)
        # Also check collaboration-level elements
        for collab in root.iter(f"{{{NS['bpmn']}}}collaboration"):
            self._parse_elements_recursive(collab)

    def _parse_elements_recursive(self, parent):
        """Recursively parse BPMN elements from a parent node."""
        for child in parent:
            tag = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""

            if tag in EVENT_TYPES or tag in TASK_TYPES or tag in GATEWAY_TYPES:
                self._add_node(child, tag)
            elif tag in FLOW_TYPES:
                self._add_edge(child, tag)
            elif tag in ("laneSet", "lane", "subProcess"):
                if tag in ("subProcess",):
                    self._add_node(child, tag)
                self._parse_elements_recursive(child)
            elif tag == "participant":
                node_id = child.get("id", "")
                node_name = child.get("name", "")
                if node_id:
                    self.nodes[node_id] = BpmnNode(
                        id=node_id, name=node_name, element_type="participant"
                    )

    def _add_node(self, element, element_type: str):
        """Add a BPMN node."""
        node_id = element.get("id", "")
        node_name = element.get("name", "")
        if not node_id:
            return
        incoming = [el.text for el in element.findall(f"{{{NS['bpmn']}}}incoming") if el.text]
        outgoing = [el.text for el in element.findall(f"{{{NS['bpmn']}}}outgoing") if el.text]
        self.nodes[node_id] = BpmnNode(
            id=node_id, name=node_name, element_type=element_type,
            incoming=incoming, outgoing=outgoing,
        )

    def _add_edge(self, element, element_type: str):
        """Add a BPMN edge."""
        edge_id = element.get("id", "")
        edge_name = element.get("name", "")
        source = element.get("sourceRef", "")
        target = element.get("targetRef", "")
        if not edge_id:
            return
        self.edges.append(BpmnEdge(
            id=edge_id, name=edge_name, element_type=element_type,
            source_ref=source, target_ref=target, label=edge_name,
        ))

    def _apply_positions(self):
        """Apply diagram positions to parsed nodes and edges."""
        for node_id, node in self.nodes.items():
            if node_id in self._shapes:
                s = self._shapes[node_id]
                node.x, node.y = s["x"], s["y"]
                node.width, node.height = s["width"], s["height"]

        for edge in self.edges:
            if edge.id in self._edge_data:
                ed = self._edge_data[edge.id]
                edge.waypoints = ed["waypoints"]
                edge.label_x = ed["label_x"]
                edge.label_y = ed["label_y"]

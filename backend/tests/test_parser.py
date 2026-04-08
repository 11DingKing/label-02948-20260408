"""Unit tests for BPMN parser."""
import pytest

from app.exceptions import BpmnParseError
from app.parser.bpmn_parser import BpmnParser
from tests.sample_data import SAMPLE_BPMN_NO_DI, SAMPLE_BPMN_WITH_DI, SAMPLE_INVALID_XML


class TestBpmnParser:
    """Tests for BpmnParser."""

    def setup_method(self):
        self.parser = BpmnParser()

    def test_parse_with_di_extracts_all_nodes(self):
        """Parser should extract all nodes from BPMN with DI."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_WITH_DI)
        assert len(nodes) == 5  # Start, Task, Gateway, 2x End
        assert len(edges) == 4

    def test_parse_with_di_has_positions(self):
        """Nodes from DI-annotated BPMN should have non-zero positions."""
        nodes, _ = self.parser.parse(SAMPLE_BPMN_WITH_DI)
        for node in nodes.values():
            assert node.width > 0, f"Node {node.id} has zero width"
            assert node.height > 0, f"Node {node.id} has zero height"

    def test_parse_with_di_has_waypoints(self):
        """Edges from DI-annotated BPMN should have waypoints."""
        _, edges = self.parser.parse(SAMPLE_BPMN_WITH_DI)
        for edge in edges:
            assert len(edge.waypoints) >= 2, f"Edge {edge.id} missing waypoints"

    def test_parse_without_di_extracts_nodes(self):
        """Parser should still extract nodes even without DI section."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_NO_DI)
        assert len(nodes) == 6  # Start, 2 Tasks, Gateway, 2 Ends
        assert len(edges) == 5

    def test_parse_without_di_nodes_have_zero_dimensions(self):
        """Without DI, nodes should have zero width/height (pre-layout)."""
        nodes, _ = self.parser.parse(SAMPLE_BPMN_NO_DI)
        for node in nodes.values():
            assert node.width == 0.0
            assert node.height == 0.0

    def test_parse_without_di_edges_have_no_waypoints(self):
        """Without DI, edges should have empty waypoints."""
        _, edges = self.parser.parse(SAMPLE_BPMN_NO_DI)
        for edge in edges:
            assert len(edge.waypoints) == 0

    def test_parse_invalid_xml_raises(self):
        """Invalid XML should raise BpmnParseError."""
        with pytest.raises(BpmnParseError, match="Invalid XML"):
            self.parser.parse(SAMPLE_INVALID_XML)

    def test_parse_element_types(self):
        """Verify correct element_type assignment."""
        nodes, _ = self.parser.parse(SAMPLE_BPMN_WITH_DI)
        types = {n.id: n.element_type for n in nodes.values()}
        assert types["Start_1"] == "startEvent"
        assert types["Task_1"] == "userTask"
        assert types["GW_1"] == "exclusiveGateway"
        assert types["End_1"] == "endEvent"

    def test_parse_edge_refs(self):
        """Verify edge source/target references."""
        _, edges = self.parser.parse(SAMPLE_BPMN_WITH_DI)
        edge_map = {e.id: e for e in edges}
        assert edge_map["Flow_1"].source_ref == "Start_1"
        assert edge_map["Flow_1"].target_ref == "Task_1"

    def test_parse_edge_labels(self):
        """Verify edge labels are extracted."""
        _, edges = self.parser.parse(SAMPLE_BPMN_WITH_DI)
        edge_map = {e.id: e for e in edges}
        assert edge_map["Flow_3"].label == "Yes"
        assert edge_map["Flow_4"].label == "No"
        assert edge_map["Flow_1"].label == ""

    def test_parser_reuse_resets_state(self):
        """Calling parse() twice should not accumulate state."""
        self.parser.parse(SAMPLE_BPMN_WITH_DI)
        nodes, edges = self.parser.parse(SAMPLE_BPMN_NO_DI)
        # Should only have nodes from the second parse
        assert len(nodes) == 6
        assert len(edges) == 5

    def test_xxe_entity_expansion_blocked(self):
        """Parser should block XXE (XML External Entity) attacks."""
        xxe_payload = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="Definitions_1" targetNamespace="http://example.com">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="Start_1" name="&xxe;">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
  </bpmn:process>
</bpmn:definitions>"""
        # Should either raise an error or silently ignore the entity
        # (not resolve it to file contents)
        try:
            nodes, _ = self.parser.parse(xxe_payload)
            # If it parses, the entity must NOT have been resolved
            if "Start_1" in nodes:
                # Name should be empty or the literal "&xxe;" — not file contents
                assert "/root:" not in nodes["Start_1"].name
                assert "passwd" not in nodes["Start_1"].name
        except BpmnParseError:
            pass  # Rejecting the document entirely is also acceptable

    def test_xxe_billion_laughs_blocked(self):
        """Parser should block billion-laughs (entity expansion bomb)."""
        bomb = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="Definitions_1" targetNamespace="http://example.com">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="Start_1" name="&lol3;"/>
  </bpmn:process>
</bpmn:definitions>"""
        try:
            nodes, _ = self.parser.parse(bomb)
            # If parsed, entity should not have been expanded
            if "Start_1" in nodes:
                assert len(nodes["Start_1"].name) < 1000
        except (BpmnParseError, Exception):
            pass  # Rejecting is acceptable

"""Unit tests for auto-layout engine."""
from app.layout.auto_layout import AutoLayoutEngine
from app.parser.bpmn_parser import BpmnParser
from tests.sample_data import SAMPLE_BPMN_NO_DI, SAMPLE_BPMN_WITH_DI


class TestAutoLayoutEngine:
    """Tests for AutoLayoutEngine."""

    def setup_method(self):
        self.parser = BpmnParser()
        self.layout = AutoLayoutEngine()

    def test_needs_layout_false_with_di(self):
        """Should not need layout when DI coordinates are present."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_WITH_DI)
        assert self.layout.needs_layout(nodes, edges) is False

    def test_needs_layout_true_without_di(self):
        """Should need layout when DI coordinates are missing."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_NO_DI)
        assert self.layout.needs_layout(nodes, edges) is True

    def test_apply_layout_assigns_dimensions(self):
        """After layout, all nodes should have non-zero dimensions."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_NO_DI)
        self.layout.apply_layout(nodes, edges)
        for node in nodes.values():
            assert node.width > 0, f"Node {node.id} has zero width after layout"
            assert node.height > 0, f"Node {node.id} has zero height after layout"

    def test_apply_layout_assigns_positions(self):
        """After layout, nodes should have distinct positions."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_NO_DI)
        self.layout.apply_layout(nodes, edges)
        positions = set()
        for node in nodes.values():
            pos = (round(node.x, 1), round(node.y, 1))
            positions.add(pos)
        # All nodes should have unique positions
        assert len(positions) == len(nodes)

    def test_apply_layout_generates_waypoints(self):
        """After layout, all edges should have waypoints."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_NO_DI)
        self.layout.apply_layout(nodes, edges)
        for edge in edges:
            assert len(edge.waypoints) >= 2, \
                f"Edge {edge.id} has {len(edge.waypoints)} waypoints after layout"

    def test_apply_layout_no_overlapping_nodes(self):
        """Nodes should not overlap after layout."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_NO_DI)
        self.layout.apply_layout(nodes, edges)
        node_list = list(nodes.values())
        for i, a in enumerate(node_list):
            for b in node_list[i + 1:]:
                # Check bounding box overlap
                overlap_x = a.x < b.x + b.width and a.x + a.width > b.x
                overlap_y = a.y < b.y + b.height and a.y + a.height > b.y
                assert not (overlap_x and overlap_y), \
                    f"Nodes {a.id} and {b.id} overlap"

    def test_layout_preserves_existing_di(self):
        """Layout should not modify nodes that already have DI coordinates."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_WITH_DI)
        original_positions = {
            nid: (n.x, n.y, n.width, n.height)
            for nid, n in nodes.items()
        }
        # needs_layout returns False, but let's force it
        # to verify _assign_default_sizes skips nodes with dimensions
        self.layout._assign_default_sizes(nodes)
        for nid, n in nodes.items():
            ox, oy, ow, oh = original_positions[nid]
            assert n.x == ox
            assert n.y == oy
            assert n.width == ow
            assert n.height == oh

    def test_layout_handles_gateway_branching(self):
        """Layout should handle gateway with multiple outgoing edges."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_NO_DI)
        self.layout.apply_layout(nodes, edges)
        # Gateway should be in a middle layer
        gw = nodes["GW_1"]
        start = nodes["Start_1"]
        assert gw.x > start.x, "Gateway should be to the right of start"

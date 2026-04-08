"""Unit tests for SVG renderer."""
from app.layout.auto_layout import AutoLayoutEngine
from app.parser.bpmn_parser import BpmnParser
from app.renderer.svg_renderer import SvgRenderer
from tests.sample_data import SAMPLE_BPMN_NO_DI, SAMPLE_BPMN_WITH_DI


class TestSvgRenderer:
    """Tests for SvgRenderer."""

    def setup_method(self):
        self.parser = BpmnParser()
        self.renderer = SvgRenderer(padding=40)
        self.layout = AutoLayoutEngine()

    def test_render_with_di_produces_valid_svg(self):
        """Rendering BPMN with DI should produce valid SVG."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_WITH_DI)
        svg = self.renderer.render(nodes, edges)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert "xmlns" in svg

    def test_render_contains_all_node_names(self):
        """SVG should contain text for all named nodes."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_WITH_DI)
        svg = self.renderer.render(nodes, edges)
        assert "Start" in svg
        assert "Review" in svg
        assert "Approved?" in svg
        assert "Done" in svg

    def test_render_contains_edge_labels(self):
        """SVG should contain edge labels."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_WITH_DI)
        svg = self.renderer.render(nodes, edges)
        assert "Yes" in svg
        assert "No" in svg

    def test_render_contains_arrowhead_marker(self):
        """SVG should define arrowhead markers."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_WITH_DI)
        svg = self.renderer.render(nodes, edges)
        assert 'id="arrowhead"' in svg

    def test_render_without_di_after_layout(self):
        """Rendering BPMN without DI after auto-layout should work."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_NO_DI)
        self.layout.apply_layout(nodes, edges)
        svg = self.renderer.render(nodes, edges)
        assert svg.startswith("<svg")
        assert "Fill Form" in svg
        assert "Process" in svg  # "Process Data" may be word-wrapped
        assert "Valid?" in svg

    def test_render_without_di_has_nonzero_dimensions(self):
        """SVG from auto-laid-out BPMN should have reasonable dimensions."""
        nodes, edges = self.parser.parse(SAMPLE_BPMN_NO_DI)
        self.layout.apply_layout(nodes, edges)
        svg = self.renderer.render(nodes, edges)
        # Extract width from SVG
        import re
        match = re.search(r'width="(\d+)"', svg)
        assert match is not None
        width = int(match.group(1))
        assert width > 100, f"SVG width too small: {width}"

    def test_render_empty_produces_minimal_svg(self):
        """Rendering empty nodes/edges should still produce valid SVG."""
        svg = self.renderer.render({}, [])
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

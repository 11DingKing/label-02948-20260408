"""SVG renderer for BPMN diagrams."""
import logging
from xml.sax.saxutils import escape

from ..parser.models import BpmnEdge, BpmnNode
from .styles import (
    BACKGROUND_COLOR,
    COLORS,
    DEFAULT_STYLE,
    FLOW_DEFAULT,
    FONT_COLOR,
    FONT_FAMILY,
    FONT_SIZE_EDGE,
    FONT_SIZE_NODE,
    GATEWAY_MARKERS,
)

logger = logging.getLogger(__name__)

EVENT_TYPES = {"startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent", "boundaryEvent"}
GATEWAY_TYPES = {"exclusiveGateway", "parallelGateway", "inclusiveGateway", "eventBasedGateway", "complexGateway"}
TASK_TYPES = {
    "task", "userTask", "serviceTask", "scriptTask", "businessRuleTask",
    "sendTask", "receiveTask", "manualTask", "callActivity", "subProcess",
}


class SvgRenderer:
    """Renders BPMN elements into SVG markup."""

    def __init__(self, padding: int = 40):
        self.padding = padding
        self._parts: list[str] = []

    def render(self, nodes: dict[str, BpmnNode], edges: list[BpmnEdge]) -> str:
        """Render nodes and edges into a complete SVG string."""
        self._parts = []
        min_x, min_y, max_x, max_y = self._compute_bounds(nodes, edges)

        svg_width = max_x - min_x + self.padding * 2
        svg_height = max_y - min_y + self.padding * 2
        offset_x = -min_x + self.padding
        offset_y = -min_y + self.padding

        self._parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{svg_width:.0f}" height="{svg_height:.0f}" '
            f'viewBox="0 0 {svg_width:.0f} {svg_height:.0f}">'
        )
        self._add_defs()
        self._parts.append(
            f'<rect width="100%" height="100%" fill="{BACKGROUND_COLOR}"/>'
        )
        self._parts.append(f'<g transform="translate({offset_x:.1f},{offset_y:.1f})">')

        # Render participants (pools) first as background
        for node in nodes.values():
            if node.element_type == "participant":
                self._render_participant(node)

        # Render edges
        for edge in edges:
            self._render_edge(edge)

        # Render nodes (except participants)
        for node in nodes.values():
            if node.element_type != "participant":
                self._render_node(node)

        self._parts.append("</g></svg>")
        svg_content = "\n".join(self._parts)
        logger.info("Generated SVG: %d chars, %.0fx%.0f", len(svg_content), svg_width, svg_height)
        return svg_content

    def _add_defs(self):
        """Add SVG definitions (markers, filters)."""
        self._parts.append("""<defs>
  <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#616161"/>
  </marker>
  <marker id="arrowhead-msg" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#616161" fill-opacity="0.6"/>
  </marker>
  <filter id="shadow" x="-10%" y="-10%" width="130%" height="130%">
    <feDropShadow dx="1" dy="1" stdDeviation="2" flood-opacity="0.15"/>
  </filter>
</defs>""")

    def _compute_bounds(self, nodes, edges) -> tuple[float, float, float, float]:
        """Compute bounding box of all elements."""
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        for node in nodes.values():
            if node.width > 0:
                min_x = min(min_x, node.x)
                min_y = min(min_y, node.y)
                max_x = max(max_x, node.x + node.width)
                max_y = max(max_y, node.y + node.height)

        for edge in edges:
            for wx, wy in edge.waypoints:
                min_x = min(min_x, wx)
                min_y = min(min_y, wy)
                max_x = max(max_x, wx)
                max_y = max(max_y, wy)

        if min_x == float("inf"):
            return 0, 0, 400, 300

        return min_x, min_y, max_x, max_y

    def _render_node(self, node: BpmnNode):
        """Render a single BPMN node."""
        if node.element_type in EVENT_TYPES:
            self._render_event(node)
        elif node.element_type in GATEWAY_TYPES:
            self._render_gateway(node)
        elif node.element_type in TASK_TYPES:
            self._render_task(node)

    def _render_event(self, node: BpmnNode):
        """Render an event (circle)."""
        style = COLORS.get(node.element_type, DEFAULT_STYLE)
        cx = node.x + node.width / 2
        cy = node.y + node.height / 2
        r = min(node.width, node.height) / 2

        self._parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'fill="{style["fill"]}" stroke="{style["stroke"]}" '
            f'stroke-width="{style["stroke_width"]}" filter="url(#shadow)"/>'
        )

        # Double circle for intermediate events
        if "intermediate" in node.element_type.lower() or node.element_type == "boundaryEvent":
            self._parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r - 3:.1f}" '
                f'fill="none" stroke="{style["stroke"]}" stroke-width="1"/>'
            )

        # Inner filled circle for end events
        if node.element_type == "endEvent":
            self._parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.45:.1f}" '
                f'fill="{style["stroke"]}" stroke="none"/>'
            )

        if node.name:
            self._render_text(cx, cy + r + 16, node.name, FONT_SIZE_NODE)

    def _render_gateway(self, node: BpmnNode):
        """Render a gateway (diamond)."""
        style = COLORS.get(node.element_type, DEFAULT_STYLE)
        cx = node.x + node.width / 2
        cy = node.y + node.height / 2
        hw = node.width / 2
        hh = node.height / 2

        points = f"{cx:.1f},{cy - hh:.1f} {cx + hw:.1f},{cy:.1f} {cx:.1f},{cy + hh:.1f} {cx - hw:.1f},{cy:.1f}"
        self._parts.append(
            f'<polygon points="{points}" fill="{style["fill"]}" '
            f'stroke="{style["stroke"]}" stroke-width="{style["stroke_width"]}" filter="url(#shadow)"/>'
        )

        marker = GATEWAY_MARKERS.get(node.element_type, "")
        if marker:
            font_size = 18 if marker in ("X", "+") else 14
            self._parts.append(
                f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" '
                f'dominant-baseline="central" font-family="{FONT_FAMILY}" '
                f'font-size="{font_size}" font-weight="bold" fill="{style["stroke"]}">'
                f'{escape(marker)}</text>'
            )

        if node.name:
            self._render_text(cx, cy + hh + 16, node.name, FONT_SIZE_NODE)

    def _render_task(self, node: BpmnNode):
        """Render a task (rounded rectangle)."""
        style = COLORS.get(node.element_type, DEFAULT_STYLE)
        rx = 8

        self._parts.append(
            f'<rect x="{node.x:.1f}" y="{node.y:.1f}" '
            f'width="{node.width:.1f}" height="{node.height:.1f}" rx="{rx}" '
            f'fill="{style["fill"]}" stroke="{style["stroke"]}" '
            f'stroke-width="{style["stroke_width"]}" filter="url(#shadow)"/>'
        )

        # Task type icon
        icon_x = node.x + 8
        icon_y = node.y + 8
        self._render_task_icon(node.element_type, icon_x, icon_y, style["stroke"])

        # Bold border for callActivity
        if node.element_type == "callActivity":
            self._parts.append(
                f'<rect x="{node.x + 2:.1f}" y="{node.y + 2:.1f}" '
                f'width="{node.width - 4:.1f}" height="{node.height - 4:.1f}" rx="{rx - 1}" '
                f'fill="none" stroke="{style["stroke"]}" stroke-width="1"/>'
            )

        if node.name:
            cx = node.x + node.width / 2
            cy = node.y + node.height / 2
            self._render_wrapped_text(cx, cy, node.name, node.width - 20, FONT_SIZE_NODE)

    def _render_task_icon(self, element_type: str, x: float, y: float, color: str):
        """Render a small icon indicating the task type."""
        size = 14
        if element_type == "userTask":
            # Simple person icon
            self._parts.append(
                f'<circle cx="{x + size / 2:.1f}" cy="{y + 4:.1f}" r="3.5" '
                f'fill="none" stroke="{color}" stroke-width="1.2"/>'
                f'<path d="M{x + 1:.1f},{y + size:.1f} '
                f'Q{x + size / 2:.1f},{y + 8:.1f} {x + size - 1:.1f},{y + size:.1f}" '
                f'fill="none" stroke="{color}" stroke-width="1.2"/>'
            )
        elif element_type == "serviceTask":
            # Gear icon
            cx_i, cy_i = x + size / 2, y + size / 2
            self._parts.append(
                f'<circle cx="{cx_i:.1f}" cy="{cy_i:.1f}" r="4" '
                f'fill="none" stroke="{color}" stroke-width="1.2"/>'
                f'<circle cx="{cx_i:.1f}" cy="{cy_i:.1f}" r="2" '
                f'fill="{color}"/>'
            )
        elif element_type == "scriptTask":
            # Script lines
            for i in range(3):
                ly = y + 3 + i * 4
                self._parts.append(
                    f'<line x1="{x + 2:.1f}" y1="{ly:.1f}" '
                    f'x2="{x + size - 2:.1f}" y2="{ly:.1f}" '
                    f'stroke="{color}" stroke-width="1.2"/>'
                )

    def _render_participant(self, node: BpmnNode):
        """Render a participant (pool)."""
        style = COLORS.get("participant", DEFAULT_STYLE)
        self._parts.append(
            f'<rect x="{node.x:.1f}" y="{node.y:.1f}" '
            f'width="{node.width:.1f}" height="{node.height:.1f}" '
            f'fill="{style["fill"]}" stroke="{style["stroke"]}" '
            f'stroke-width="{style["stroke_width"]}"/>'
        )
        # Vertical label band
        band_width = 30
        self._parts.append(
            f'<line x1="{node.x + band_width:.1f}" y1="{node.y:.1f}" '
            f'x2="{node.x + band_width:.1f}" y2="{node.y + node.height:.1f}" '
            f'stroke="{style["stroke"]}" stroke-width="{style["stroke_width"]}"/>'
        )
        if node.name:
            tx = node.x + band_width / 2
            ty = node.y + node.height / 2
            self._parts.append(
                f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" '
                f'dominant-baseline="central" font-family="{FONT_FAMILY}" '
                f'font-size="{FONT_SIZE_NODE}" fill="{FONT_COLOR}" '
                f'transform="rotate(-90,{tx:.1f},{ty:.1f})">'
                f'{escape(node.name)}</text>'
            )

    def _render_edge(self, edge: BpmnEdge):
        """Render a sequence flow / connection."""
        if len(edge.waypoints) < 2:
            return

        style = COLORS.get(edge.element_type, FLOW_DEFAULT)
        points_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in edge.waypoints)

        dash = ""
        marker = "url(#arrowhead)"
        if edge.element_type == "messageFlow":
            dash = ' stroke-dasharray="6,4"'
            marker = "url(#arrowhead-msg)"
        elif edge.element_type == "association":
            dash = ' stroke-dasharray="3,3"'
            marker = ""

        marker_attr = f' marker-end="{marker}"' if marker else ""
        self._parts.append(
            f'<polyline points="{points_str}" fill="none" '
            f'stroke="{style["stroke"]}" stroke-width="{style["stroke_width"]}"{dash}'
            f'{marker_attr}/>'
        )

        if edge.label:
            if edge.label_x and edge.label_y:
                lx, ly = edge.label_x, edge.label_y
            else:
                mid = len(edge.waypoints) // 2
                lx = (edge.waypoints[mid - 1][0] + edge.waypoints[mid][0]) / 2
                ly = (edge.waypoints[mid - 1][1] + edge.waypoints[mid][1]) / 2 - 8
            self._parts.append(
                f'<rect x="{lx - 2:.1f}" y="{ly - FONT_SIZE_EDGE:.1f}" '
                f'width="{len(edge.label) * 6 + 4:.1f}" height="{FONT_SIZE_EDGE + 6:.1f}" '
                f'fill="white" fill-opacity="0.85" rx="2"/>'
            )
            self._render_text(lx + len(edge.label) * 3, ly, edge.label, FONT_SIZE_EDGE)

    def _render_text(self, x: float, y: float, text: str, font_size: int):
        """Render centered text."""
        self._parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" '
            f'dominant-baseline="central" font-family="{FONT_FAMILY}" '
            f'font-size="{font_size}" fill="{FONT_COLOR}">'
            f'{escape(text)}</text>'
        )

    def _render_wrapped_text(self, cx: float, cy: float, text: str,
                              max_width: float, font_size: int):
        """Render text with simple word wrapping."""
        avg_char_width = font_size * 0.6
        max_chars = max(1, int(max_width / avg_char_width))
        lines = []
        words = text.split()
        current_line = ""

        for word in words:
            test = f"{current_line} {word}".strip()
            if len(test) <= max_chars:
                current_line = test
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        if not lines:
            return

        line_height = font_size + 4
        start_y = cy - (len(lines) - 1) * line_height / 2

        for i, line in enumerate(lines):
            y = start_y + i * line_height
            self._parts.append(
                f'<text x="{cx:.1f}" y="{y:.1f}" text-anchor="middle" '
                f'dominant-baseline="central" font-family="{FONT_FAMILY}" '
                f'font-size="{font_size}" fill="{FONT_COLOR}">'
                f'{escape(line)}</text>'
            )

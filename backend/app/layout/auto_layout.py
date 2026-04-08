"""
Auto-layout engine for BPMN diagrams lacking DI (diagram interchange) coordinates.

Uses a layered graph layout approach (Sugiyama-style):
1. Topological sort to assign layers (ranks)
2. Minimize edge crossings within layers via barycenter heuristic
3. Assign concrete x/y coordinates with configurable spacing
4. Generate orthogonal waypoints for edges
"""
import logging
from collections import defaultdict, deque

from ..parser.models import BpmnEdge, BpmnNode

logger = logging.getLogger(__name__)

# Default element dimensions by category
DEFAULT_SIZES = {
    "event": (36, 36),
    "task": (100, 80),
    "gateway": (50, 50),
    "participant": (600, 200),
}

EVENT_TYPES = {
    "startEvent", "endEvent", "intermediateCatchEvent",
    "intermediateThrowEvent", "boundaryEvent",
}
GATEWAY_TYPES = {
    "exclusiveGateway", "parallelGateway", "inclusiveGateway",
    "eventBasedGateway", "complexGateway",
}

# Layout spacing constants
HORIZONTAL_SPACING = 60
VERTICAL_SPACING = 80
LAYER_WIDTH = 160
INITIAL_X = 80
INITIAL_Y = 80


class AutoLayoutEngine:
    """Assigns positions to BPMN nodes and generates edge waypoints
    when the BPMN file has no DI (diagram interchange) section."""

    def needs_layout(self, nodes: dict[str, BpmnNode], edges: list[BpmnEdge]) -> bool:
        """Check if auto-layout is needed.

        Returns True if any non-participant node has zero width/height
        (meaning no DI coordinates were provided).
        """
        for node in nodes.values():
            if node.element_type == "participant":
                continue
            if node.width <= 0 or node.height <= 0:
                return True
        # Also check if all edges lack waypoints
        return bool(edges and all(len(e.waypoints) == 0 for e in edges))

    def apply_layout(self, nodes: dict[str, BpmnNode],
                     edges: list[BpmnEdge]) -> None:
        """Apply auto-layout to nodes and edges in-place."""
        logger.info("Applying auto-layout to %d nodes, %d edges",
                     len(nodes), len(edges))

        # Step 1: Assign default sizes to nodes missing dimensions
        self._assign_default_sizes(nodes)

        # Step 2: Build adjacency from edges
        adj, reverse_adj = self._build_adjacency(nodes, edges)

        # Step 3: Assign layers via topological sort (longest path)
        layers = self._assign_layers(nodes, adj, reverse_adj)

        # Step 4: Order nodes within layers (barycenter heuristic)
        ordered_layers = self._order_within_layers(layers, adj, nodes)

        # Step 5: Assign x/y coordinates
        self._assign_coordinates(ordered_layers, nodes)

        # Step 6: Generate edge waypoints
        self._generate_waypoints(nodes, edges)

        logger.info("Auto-layout complete")

    def _assign_default_sizes(self, nodes: dict[str, BpmnNode]) -> None:
        """Assign default width/height based on element type."""
        for node in nodes.values():
            if node.width > 0 and node.height > 0:
                continue
            if node.element_type in EVENT_TYPES:
                node.width, node.height = DEFAULT_SIZES["event"]
            elif node.element_type in GATEWAY_TYPES:
                node.width, node.height = DEFAULT_SIZES["gateway"]
            elif node.element_type == "participant":
                node.width, node.height = DEFAULT_SIZES["participant"]
            else:
                node.width, node.height = DEFAULT_SIZES["task"]

    def _build_adjacency(self, nodes: dict[str, BpmnNode],
                         edges: list[BpmnEdge]
                         ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        """Build forward and reverse adjacency lists from edges."""
        adj: dict[str, list[str]] = defaultdict(list)
        reverse_adj: dict[str, list[str]] = defaultdict(list)
        for edge in edges:
            src, tgt = edge.source_ref, edge.target_ref
            if src in nodes and tgt in nodes:
                adj[src].append(tgt)
                reverse_adj[tgt].append(src)
        return adj, reverse_adj

    def _assign_layers(self, nodes: dict[str, BpmnNode],
                       adj: dict[str, list[str]],
                       reverse_adj: dict[str, list[str]]
                       ) -> dict[int, list[str]]:
        """Assign layer (rank) to each node using longest-path algorithm.

        Nodes with no predecessors start at layer 0.
        Each subsequent node is placed at max(predecessor layers) + 1.
        """
        node_ids = [nid for nid, n in nodes.items()
                    if n.element_type != "participant"]

        if not node_ids:
            return {}

        # In-degree for topological sort
        in_degree = {nid: 0 for nid in node_ids}
        for nid in node_ids:
            for pred in reverse_adj.get(nid, []):
                if pred in in_degree:
                    in_degree[nid] += 1

        # BFS topological order
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        rank = {nid: 0 for nid in node_ids}
        topo_order = []

        while queue:
            nid = queue.popleft()
            topo_order.append(nid)
            for succ in adj.get(nid, []):
                if succ not in in_degree:
                    continue
                rank[succ] = max(rank[succ], rank[nid] + 1)
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        # Handle nodes not reached (disconnected components)
        for nid in node_ids:
            if nid not in rank:
                rank[nid] = 0

        # Group by layer
        layers: dict[int, list[str]] = defaultdict(list)
        for nid, r in rank.items():
            layers[r].append(nid)

        return dict(layers)

    def _order_within_layers(self, layers: dict[int, list[str]],
                             adj: dict[str, list[str]],
                             nodes: dict[str, BpmnNode]
                             ) -> list[list[str]]:
        """Order nodes within each layer using barycenter heuristic
        to reduce edge crossings."""
        if not layers:
            return []

        max_layer = max(layers.keys())
        ordered: list[list[str]] = [[] for _ in range(max_layer + 1)]

        # Initialize first layer order
        ordered[0] = sorted(layers.get(0, []),
                            key=lambda nid: nodes[nid].name)

        # Forward sweep: order each layer based on predecessor positions
        for layer_idx in range(1, max_layer + 1):
            layer_nodes = layers.get(layer_idx, [])
            if not layer_nodes:
                continue

            prev_positions = {nid: i for i, nid in enumerate(ordered[layer_idx - 1])}
            barycenters = {}

            for nid in layer_nodes:
                # Find predecessors in previous layer
                preds_in_prev = []
                for prev_nid, succs in adj.items():
                    if nid in succs and prev_nid in prev_positions:
                        preds_in_prev.append(prev_positions[prev_nid])

                if preds_in_prev:
                    barycenters[nid] = sum(preds_in_prev) / len(preds_in_prev)
                else:
                    barycenters[nid] = float("inf")

            ordered[layer_idx] = sorted(layer_nodes,
                                        key=lambda nid: barycenters.get(nid, 0))

        return ordered

    def _assign_coordinates(self, ordered_layers: list[list[str]],
                            nodes: dict[str, BpmnNode]) -> None:
        """Assign concrete x/y coordinates to nodes based on layer assignment."""
        for layer_idx, layer_nodes in enumerate(ordered_layers):
            x = INITIAL_X + layer_idx * LAYER_WIDTH

            # Center nodes vertically within the layer
            total_height = sum(nodes[nid].height for nid in layer_nodes)
            total_spacing = VERTICAL_SPACING * max(0, len(layer_nodes) - 1)
            start_y = INITIAL_Y + max(0, (400 - total_height - total_spacing) / 2)

            current_y = start_y
            for nid in layer_nodes:
                node = nodes[nid]
                # Center the node horizontally within its layer slot
                node.x = x + (LAYER_WIDTH - HORIZONTAL_SPACING - node.width) / 2
                node.y = current_y
                current_y += node.height + VERTICAL_SPACING

    def _generate_waypoints(self, nodes: dict[str, BpmnNode],
                            edges: list[BpmnEdge]) -> None:
        """Generate orthogonal waypoints for edges based on node positions."""
        for edge in edges:
            if edge.waypoints:
                continue  # Already has waypoints from DI

            src = nodes.get(edge.source_ref)
            tgt = nodes.get(edge.target_ref)
            if not src or not tgt:
                continue

            # Source connection point: right center
            src_cx = src.x + src.width
            src_cy = src.y + src.height / 2

            # Target connection point: left center
            tgt_cx = tgt.x
            tgt_cy = tgt.y + tgt.height / 2

            # Generate waypoints
            if abs(src_cy - tgt_cy) < 5:
                # Straight horizontal line
                edge.waypoints = [(src_cx, src_cy), (tgt_cx, tgt_cy)]
            else:
                # Orthogonal routing: horizontal -> vertical -> horizontal
                mid_x = (src_cx + tgt_cx) / 2
                edge.waypoints = [
                    (src_cx, src_cy),
                    (mid_x, src_cy),
                    (mid_x, tgt_cy),
                    (tgt_cx, tgt_cy),
                ]

            # Place label at midpoint
            if edge.label:
                mid_idx = len(edge.waypoints) // 2
                p1 = edge.waypoints[mid_idx - 1]
                p2 = edge.waypoints[mid_idx]
                edge.label_x = (p1[0] + p2[0]) / 2
                edge.label_y = (p1[1] + p2[1]) / 2 - 10

"""Interfaces (Protocols) for dependency injection."""
from typing import Protocol, runtime_checkable

from .parser.models import BpmnEdge, BpmnNode


@runtime_checkable
class IBpmnParser(Protocol):
    """Interface for BPMN file parsing."""
    def parse(self, bpmn_content: str) -> tuple[dict[str, BpmnNode], list[BpmnEdge]]:
        ...


@runtime_checkable
class ISvgRenderer(Protocol):
    """Interface for SVG rendering."""
    def render(self, nodes: dict[str, BpmnNode], edges: list[BpmnEdge]) -> str:
        ...


@runtime_checkable
class IImageConverter(Protocol):
    """Interface for image format conversion."""
    @staticmethod
    def svg_to_png(svg_content: str, dpi: int = 150, scale: float = 2.0) -> bytes:
        ...

    @staticmethod
    def svg_to_bytes(svg_content: str) -> bytes:
        ...


@runtime_checkable
class ILayoutEngine(Protocol):
    """Interface for auto-layout engine."""
    def needs_layout(self, nodes: dict[str, BpmnNode], edges: list[BpmnEdge]) -> bool:
        ...

    def apply_layout(self, nodes: dict[str, BpmnNode], edges: list[BpmnEdge]) -> None:
        ...

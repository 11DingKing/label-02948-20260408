"""Service package - provides factory for wiring dependencies."""
from ..config import Config
from ..layout.auto_layout import AutoLayoutEngine
from ..parser.bpmn_parser import BpmnParser
from ..renderer.image_converter import ImageConverter
from ..renderer.svg_renderer import SvgRenderer
from .converter_service import ConverterService


def create_converter_service() -> ConverterService:
    """Factory: wire up all dependencies and return a ConverterService."""
    return ConverterService(
        parser=BpmnParser(),
        renderer=SvgRenderer(padding=Config.DEFAULT_PADDING),
        converter=ImageConverter(),
        layout_engine=AutoLayoutEngine(),
    )

"""BPMN conversion service - orchestrates parsing, layout, and rendering."""
import logging
import os
import uuid

from ..config import Config
from ..exceptions import BpmnParseError, FileValidationError
from ..interfaces import IBpmnParser, IImageConverter, ILayoutEngine, ISvgRenderer

logger = logging.getLogger(__name__)


class ConverterService:
    """Orchestrates BPMN file parsing and image rendering.

    Dependencies are injected via constructor to support testing
    and component replacement.
    """

    ALLOWED_FORMATS = {"png", "svg"}

    def __init__(
        self,
        parser: IBpmnParser,
        renderer: ISvgRenderer,
        converter: IImageConverter,
        layout_engine: ILayoutEngine,
    ):
        self.parser = parser
        self.renderer = renderer
        self.converter = converter
        self.layout_engine = layout_engine

    def validate_file(self, filename: str) -> str:
        """Validate uploaded file and return its extension."""
        if not filename:
            raise FileValidationError("No file selected")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in Config.ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"Invalid file type '.{ext}'. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}"
            )
        return ext

    def convert(self, bpmn_content: str, output_format: str = "png",
                dpi: int = 150, scale: float = 2.0) -> tuple[bytes, str]:
        """
        Convert BPMN content to image.

        Returns:
            Tuple of (image_bytes, content_type)
        """
        output_format = output_format.lower()
        if output_format not in self.ALLOWED_FORMATS:
            raise FileValidationError(
                f"Unsupported format '{output_format}'. "
                f"Allowed: {', '.join(self.ALLOWED_FORMATS)}"
            )

        logger.info("Starting BPMN conversion to %s (dpi=%d, scale=%.1f)",
                     output_format, dpi, scale)

        # Parse
        nodes, edges = self.parser.parse(bpmn_content)
        if not nodes and not edges:
            raise BpmnParseError("No BPMN elements found in the file")

        # Auto-layout if DI coordinates are missing
        if self.layout_engine.needs_layout(nodes, edges):
            logger.info("DI coordinates missing or incomplete, applying auto-layout")
            self.layout_engine.apply_layout(nodes, edges)

        # Render to SVG
        svg_content = self.renderer.render(nodes, edges)

        # Convert to target format
        if output_format == "svg":
            return self.converter.svg_to_bytes(svg_content), "image/svg+xml"
        else:
            png_bytes = self.converter.svg_to_png(svg_content, dpi=dpi, scale=scale)
            return png_bytes, "image/png"

    def save_output(self, image_bytes: bytes, output_format: str) -> str:
        """Save converted image to output directory."""
        Config.init_dirs()
        filename = f"{uuid.uuid4().hex}.{output_format}"
        filepath = os.path.join(Config.OUTPUT_FOLDER, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        logger.info("Saved output to %s", filepath)
        return filepath

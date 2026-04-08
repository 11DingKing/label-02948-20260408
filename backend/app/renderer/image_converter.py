"""Convert SVG to PNG raster images via CairoSVG."""
import logging

from cairosvg import svg2png

from ..exceptions import RenderError

logger = logging.getLogger(__name__)


class ImageConverter:
    """Converts SVG content to raster images."""

    @staticmethod
    def svg_to_png(svg_content: str, dpi: int = 150, scale: float = 2.0) -> bytes:
        """Convert SVG string to PNG bytes."""
        try:
            png_bytes = svg2png(
                bytestring=svg_content.encode("utf-8"),
                dpi=dpi,
                scale=scale,
            )
            logger.info("Converted SVG to PNG: %d bytes", len(png_bytes))
            return png_bytes
        except Exception as e:
            logger.error("SVG to PNG conversion failed: %s", e)
            raise RenderError(f"PNG conversion failed: {e}") from e

    @staticmethod
    def svg_to_bytes(svg_content: str) -> bytes:
        """Return SVG as UTF-8 bytes."""
        return svg_content.encode("utf-8")

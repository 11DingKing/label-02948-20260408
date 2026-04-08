#!/usr/bin/env python3
"""
CLI tool: Convert BPMN files to images.

Usage:
    python convert.py input.bpmn                     # -> input.png
    python convert.py input.bpmn -o output.png
    python convert.py input.bpmn -f svg -o flow.svg
    python convert.py input.bpmn --dpi 300 --scale 3
"""
import argparse
import logging
import os
import sys

from app.exceptions import AppException
from app.layout.auto_layout import AutoLayoutEngine
from app.parser.bpmn_parser import BpmnParser
from app.renderer.image_converter import ImageConverter
from app.renderer.svg_renderer import SvgRenderer

# Validation constants — kept in sync with API (_parse_convert_params)
DPI_MIN, DPI_MAX = 72, 600
SCALE_MIN, SCALE_MAX = 0.5, 5.0
ALLOWED_EXTENSIONS = {"bpmn", "xml"}


def main() -> int:
    """CLI entry point. Returns exit code."""
    args = _parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("bpmn-convert")

    try:
        _validate_input(args)
        output_path = _resolve_output_path(args)
        bpmn_content = _read_file(args.input)

        logger.info("Parsing %s ...", args.input)
        nodes, edges = BpmnParser().parse(bpmn_content)

        if not nodes and not edges:
            _error("No BPMN elements found in the file")

        logger.info("Found %d nodes and %d edges", len(nodes), len(edges))

        # Auto-layout if DI coordinates are missing
        layout_engine = AutoLayoutEngine()
        if layout_engine.needs_layout(nodes, edges):
            logger.info("DI coordinates missing, applying auto-layout")
            layout_engine.apply_layout(nodes, edges)

        # Render
        svg_content = SvgRenderer(padding=args.padding).render(nodes, edges)

        # Output
        if args.format == "svg":
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(svg_content)
        else:
            png_bytes = ImageConverter.svg_to_png(
                svg_content, dpi=args.dpi, scale=args.scale
            )
            with open(output_path, "wb") as f:
                f.write(png_bytes)

        file_size = os.path.getsize(output_path)
        print(f"✅ Converted: {args.input} -> {output_path} ({_format_size(file_size)})")
        return 0

    except AppException as e:
        print(f"❌ Error: {e.message}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.debug("Unexpected error", exc_info=True)
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def _parse_args() -> argparse.Namespace:
    """Parse and return CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Convert BPMN 2.0 files to PNG or SVG images.",
        epilog="Examples:\n"
               "  python convert.py flow.bpmn\n"
               "  python convert.py flow.bpmn -f svg -o diagram.svg\n"
               "  python convert.py flow.bpmn --dpi 300 --scale 3\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="Path to the BPMN file (.bpmn or .xml)")
    parser.add_argument("-o", "--output", help="Output file path (default: <input>.<format>)")
    parser.add_argument("-f", "--format", choices=["png", "svg"], default="png",
                        help="Output format (default: png)")
    parser.add_argument("--dpi", type=int, default=150,
                        help=f"DPI for PNG output ({DPI_MIN}-{DPI_MAX}, default: 150)")
    parser.add_argument("--scale", type=float, default=2.0,
                        help=f"Scale factor for PNG ({SCALE_MIN}-{SCALE_MAX}, default: 2.0)")
    parser.add_argument("--padding", type=int, default=40,
                        help="Padding around the diagram in pixels (default: 40)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose logging")
    return parser.parse_args()


def _validate_input(args: argparse.Namespace) -> None:
    """Validate input file and parameter ranges."""
    if not os.path.isfile(args.input):
        _error(f"File not found: {args.input}")

    ext = args.input.rsplit(".", 1)[-1].lower() if "." in args.input else ""
    if ext not in ALLOWED_EXTENSIONS:
        _error(f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    if not (DPI_MIN <= args.dpi <= DPI_MAX):
        _error(f"DPI must be between {DPI_MIN} and {DPI_MAX}, got {args.dpi}")

    if not (SCALE_MIN <= args.scale <= SCALE_MAX):
        _error(f"Scale must be between {SCALE_MIN} and {SCALE_MAX}, got {args.scale}")

    if args.padding < 0:
        _error(f"Padding must be non-negative, got {args.padding}")


def _resolve_output_path(args: argparse.Namespace) -> str:
    """Determine output file path."""
    if args.output:
        return args.output
    base = args.input.rsplit(".", 1)[0]
    return f"{base}.{args.format}"


def _read_file(path: str) -> str:
    """Read file content as UTF-8 string."""
    with open(path, encoding="utf-8") as f:
        return f.read()


def _format_size(size_bytes: int) -> str:
    """Format file size for display."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1048576:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / 1048576:.1f} MB"


def _error(message: str) -> None:
    """Print error and exit."""
    print(f"❌ Error: {message}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())

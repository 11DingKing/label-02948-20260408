"""API routes for BPMN conversion."""
import base64
import io
import logging

from flask import Blueprint, jsonify, request, send_file

from ..exceptions import FileValidationError
from ..service import create_converter_service

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")

converter_service = create_converter_service()


def _parse_convert_params():
    """Parse and validate common conversion parameters from request.

    Returns:
        Tuple of (file, bpmn_content, output_format, dpi, scale)

    Raises:
        FileValidationError: If any parameter is invalid.
    """
    if "file" not in request.files:
        raise FileValidationError("No file part in request")

    file = request.files["file"]
    converter_service.validate_file(file.filename)

    output_format = request.form.get("format", "png").lower()
    dpi = int(request.form.get("dpi", 150))
    scale = float(request.form.get("scale", 2.0))

    if dpi < 72 or dpi > 600:
        raise FileValidationError("DPI must be between 72 and 600")
    if scale < 0.5 or scale > 5.0:
        raise FileValidationError("Scale must be between 0.5 and 5.0")

    bpmn_content = file.read().decode("utf-8")
    return file, bpmn_content, output_format, dpi, scale


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "bpmn-to-image-converter"})


@api_bp.route("/convert", methods=["POST"])
def convert_bpmn():
    """
    Convert uploaded BPMN file to image.

    Form params:
        file: BPMN file (.bpmn or .xml)
        format: Output format (png or svg), default: png
        dpi: DPI for PNG output (72-600), default: 150
        scale: Scale factor (0.5-5.0), default: 2.0
    """
    file, bpmn_content, output_format, dpi, scale = _parse_convert_params()
    logger.info("Converting file '%s' to %s", file.filename, output_format)

    image_bytes, content_type = converter_service.convert(
        bpmn_content, output_format, dpi, scale
    )

    ext = "svg" if output_format == "svg" else "png"
    download_name = file.filename.rsplit(".", 1)[0] + f".{ext}"

    return send_file(
        io.BytesIO(image_bytes),
        mimetype=content_type,
        as_attachment=True,
        download_name=download_name,
    )


@api_bp.route("/convert/preview", methods=["POST"])
def convert_bpmn_preview():
    """
    Convert BPMN and return base64 for preview.

    Form params: same as /api/convert
    """
    file, bpmn_content, output_format, dpi, scale = _parse_convert_params()
    logger.info("Preview converting file '%s' to %s", file.filename, output_format)

    image_bytes, content_type = converter_service.convert(
        bpmn_content, output_format, dpi, scale
    )

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return jsonify({
        "success": True,
        "image": f"data:{content_type};base64,{b64}",
        "format": output_format,
        "size": len(image_bytes),
    })

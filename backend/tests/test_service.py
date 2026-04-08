"""Unit tests for ConverterService with dependency injection."""
from unittest.mock import MagicMock

import pytest

from app.exceptions import BpmnParseError, FileValidationError
from app.parser.models import BpmnNode
from app.service.converter_service import ConverterService


class TestConverterServiceValidation:
    """Tests for file validation logic."""

    def setup_method(self):
        self.service = ConverterService(
            parser=MagicMock(),
            renderer=MagicMock(),
            converter=MagicMock(),
            layout_engine=MagicMock(),
        )

    def test_validate_valid_bpmn(self):
        ext = self.service.validate_file("diagram.bpmn")
        assert ext == "bpmn"

    def test_validate_valid_xml(self):
        ext = self.service.validate_file("process.xml")
        assert ext == "xml"

    def test_validate_invalid_extension(self):
        with pytest.raises(FileValidationError, match="Invalid file type"):
            self.service.validate_file("image.png")

    def test_validate_empty_filename(self):
        with pytest.raises(FileValidationError, match="No file selected"):
            self.service.validate_file("")

    def test_validate_no_extension(self):
        with pytest.raises(FileValidationError, match="Invalid file type"):
            self.service.validate_file("noextension")


class TestConverterServiceConvert:
    """Tests for conversion logic with mocked dependencies."""

    def _make_service(self, nodes=None, edges=None, needs_layout=False):
        """Helper to create service with configured mocks."""
        parser = MagicMock()
        parser.parse.return_value = (
            nodes or {"n1": BpmnNode(id="n1", name="Start", element_type="startEvent",
                                     width=36, height=36, x=100, y=100)},
            edges or [],
        )
        renderer = MagicMock()
        renderer.render.return_value = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
        converter = MagicMock()
        converter.svg_to_png.return_value = b"\x89PNG_FAKE"
        converter.svg_to_bytes.return_value = b"<svg></svg>"
        layout = MagicMock()
        layout.needs_layout.return_value = needs_layout
        return ConverterService(
            parser=parser, renderer=renderer,
            converter=converter, layout_engine=layout,
        ), parser, renderer, converter, layout

    def test_convert_png_calls_svg_to_png(self):
        svc, parser, renderer, converter, layout = self._make_service()
        result, content_type = svc.convert("<bpmn/>", "png")
        converter.svg_to_png.assert_called_once()
        assert content_type == "image/png"

    def test_convert_svg_calls_svg_to_bytes(self):
        svc, parser, renderer, converter, layout = self._make_service()
        result, content_type = svc.convert("<bpmn/>", "svg")
        converter.svg_to_bytes.assert_called_once()
        assert content_type == "image/svg+xml"

    def test_convert_invalid_format_raises(self):
        svc, *_ = self._make_service()
        with pytest.raises(FileValidationError, match="Unsupported format"):
            svc.convert("<bpmn/>", "gif")

    def test_convert_empty_process_raises(self):
        parser = MagicMock()
        parser.parse.return_value = ({}, [])
        layout = MagicMock()
        layout.needs_layout.return_value = False
        svc = ConverterService(
            parser=parser, renderer=MagicMock(),
            converter=MagicMock(), layout_engine=layout,
        )
        with pytest.raises(BpmnParseError, match="No BPMN elements"):
            svc.convert("<bpmn/>")

    def test_convert_triggers_layout_when_needed(self):
        """When layout engine says layout is needed, it should be called."""
        svc, parser, renderer, converter, layout = self._make_service(needs_layout=True)
        svc.convert("<bpmn/>", "png")
        layout.apply_layout.assert_called_once()

    def test_convert_skips_layout_when_not_needed(self):
        """When layout engine says no layout needed, it should not be called."""
        svc, parser, renderer, converter, layout = self._make_service(needs_layout=False)
        svc.convert("<bpmn/>", "png")
        layout.apply_layout.assert_not_called()

    def test_convert_passes_dpi_and_scale(self):
        svc, parser, renderer, converter, layout = self._make_service()
        svc.convert("<bpmn/>", "png", dpi=300, scale=3.0)
        converter.svg_to_png.assert_called_once()
        call_args = converter.svg_to_png.call_args
        assert call_args.kwargs.get("dpi") == 300 or call_args[1].get("dpi") == 300

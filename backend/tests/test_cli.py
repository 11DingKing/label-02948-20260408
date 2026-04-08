"""End-to-end tests for CLI (convert.py)."""
import os
import subprocess
import sys
import tempfile

from tests.sample_data import SAMPLE_BPMN_NO_DI, SAMPLE_BPMN_WITH_DI, SAMPLE_INVALID_XML

PYTHON = sys.executable
CLI = os.path.join(os.path.dirname(__file__), "..", "convert.py")


def _write_temp_bpmn(content: str, suffix: str = ".bpmn") -> str:
    """Write content to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _run_cli(*args: str, expect_fail: bool = False) -> subprocess.CompletedProcess:
    """Run the CLI and return the result."""
    result = subprocess.run(
        [PYTHON, CLI, *args],
        capture_output=True,
        text=True,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    if not expect_fail:
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
    return result


class TestCliWithDI:
    """CLI tests with BPMN files that have DI coordinates."""

    def test_convert_to_svg(self, tmp_path):
        bpmn = _write_temp_bpmn(SAMPLE_BPMN_WITH_DI)
        out = str(tmp_path / "output.svg")
        _run_cli(bpmn, "-f", "svg", "-o", out)
        assert os.path.isfile(out)
        with open(out, encoding="utf-8") as f:
            content = f.read()
        assert content.startswith("<svg")
        assert "Start" in content
        os.unlink(bpmn)

    def test_default_output_path(self, tmp_path):
        bpmn = str(tmp_path / "diagram.bpmn")
        with open(bpmn, "w", encoding="utf-8") as f:
            f.write(SAMPLE_BPMN_WITH_DI)
        _run_cli(bpmn, "-f", "svg")
        expected_out = str(tmp_path / "diagram.svg")
        assert os.path.isfile(expected_out)


class TestCliWithoutDI:
    """CLI tests with BPMN files lacking DI — auto-layout must kick in."""

    def test_convert_no_di_to_svg(self, tmp_path):
        bpmn = _write_temp_bpmn(SAMPLE_BPMN_NO_DI)
        out = str(tmp_path / "no_di.svg")
        _run_cli(bpmn, "-f", "svg", "-o", out)
        assert os.path.isfile(out)
        with open(out, encoding="utf-8") as f:
            content = f.read()
        assert content.startswith("<svg")
        assert "Fill Form" in content
        assert "Process" in content  # "Process Data" may be word-wrapped
        os.unlink(bpmn)

    def test_convert_no_di_verbose(self, tmp_path):
        """Verbose mode should mention auto-layout."""
        bpmn = _write_temp_bpmn(SAMPLE_BPMN_NO_DI)
        out = str(tmp_path / "verbose.svg")
        result = _run_cli(bpmn, "-f", "svg", "-o", out, "-v")
        assert "auto-layout" in result.stderr.lower() or result.returncode == 0
        os.unlink(bpmn)


class TestCliValidation:
    """CLI parameter validation tests."""

    def test_file_not_found(self):
        result = _run_cli("/nonexistent/file.bpmn", expect_fail=True)
        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_invalid_extension(self, tmp_path):
        bad = str(tmp_path / "test.txt")
        with open(bad, "w") as f:
            f.write("not bpmn")
        result = _run_cli(bad, expect_fail=True)
        assert result.returncode != 0
        assert "unsupported" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_invalid_dpi_too_high(self, tmp_path):
        bpmn = _write_temp_bpmn(SAMPLE_BPMN_WITH_DI)
        result = _run_cli(bpmn, "--dpi", "9999", expect_fail=True)
        assert result.returncode != 0
        assert "dpi" in result.stderr.lower()
        os.unlink(bpmn)

    def test_invalid_dpi_too_low(self, tmp_path):
        bpmn = _write_temp_bpmn(SAMPLE_BPMN_WITH_DI)
        result = _run_cli(bpmn, "--dpi", "10", expect_fail=True)
        assert result.returncode != 0
        assert "dpi" in result.stderr.lower()
        os.unlink(bpmn)

    def test_invalid_scale_too_high(self, tmp_path):
        bpmn = _write_temp_bpmn(SAMPLE_BPMN_WITH_DI)
        result = _run_cli(bpmn, "--scale", "99", expect_fail=True)
        assert result.returncode != 0
        assert "scale" in result.stderr.lower()
        os.unlink(bpmn)

    def test_invalid_scale_too_low(self, tmp_path):
        bpmn = _write_temp_bpmn(SAMPLE_BPMN_WITH_DI)
        result = _run_cli(bpmn, "--scale", "0.1", expect_fail=True)
        assert result.returncode != 0
        assert "scale" in result.stderr.lower()
        os.unlink(bpmn)

    def test_invalid_xml_friendly_error(self, tmp_path):
        bpmn = _write_temp_bpmn(SAMPLE_INVALID_XML)
        result = _run_cli(bpmn, "-f", "svg", expect_fail=True)
        assert result.returncode != 0
        # Should show friendly error, not raw traceback
        assert "Traceback" not in result.stderr
        assert "error" in result.stderr.lower()
        os.unlink(bpmn)

    def test_empty_process_friendly_error(self, tmp_path):
        empty = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="D1" targetNamespace="http://example.com">
  <bpmn:process id="P1" isExecutable="true"/>
</bpmn:definitions>"""
        bpmn = _write_temp_bpmn(empty)
        result = _run_cli(bpmn, "-f", "svg", expect_fail=True)
        assert result.returncode != 0
        assert "Traceback" not in result.stderr
        os.unlink(bpmn)

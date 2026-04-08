"""Integration tests for API endpoints."""
import io

from tests.sample_data import SAMPLE_BPMN_NO_DI, SAMPLE_BPMN_WITH_DI, SAMPLE_INVALID_XML


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"


class TestConvertEndpoint:
    def _upload(self, client, content, filename="test.bpmn",
                fmt="svg", endpoint="/api/convert"):
        """Helper to POST a BPMN file."""
        data = {
            "file": (io.BytesIO(content.encode("utf-8")), filename),
            "format": fmt,
        }
        return client.post(endpoint, data=data, content_type="multipart/form-data")

    def test_convert_with_di_returns_svg(self, client):
        resp = self._upload(client, SAMPLE_BPMN_WITH_DI, fmt="svg")
        assert resp.status_code == 200
        assert resp.content_type.startswith("image/svg+xml")
        assert b"<svg" in resp.data

    def test_convert_without_di_returns_svg(self, client):
        """Critical: BPMN without DI should still produce valid output."""
        resp = self._upload(client, SAMPLE_BPMN_NO_DI, fmt="svg")
        assert resp.status_code == 200
        assert b"<svg" in resp.data
        # Node names should appear (may be word-wrapped)
        assert b"Fill Form" in resp.data
        assert b"Process" in resp.data  # "Process Data" may be wrapped

    def test_convert_invalid_xml_returns_400(self, client):
        resp = self._upload(client, SAMPLE_INVALID_XML)
        assert resp.status_code == 400

    def test_convert_no_file_returns_400(self, client):
        resp = client.post("/api/convert", data={},
                           content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_convert_wrong_extension_returns_400(self, client):
        resp = self._upload(client, SAMPLE_BPMN_WITH_DI, filename="test.txt")
        assert resp.status_code == 400

    def test_convert_invalid_dpi_returns_400(self, client):
        data = {
            "file": (io.BytesIO(SAMPLE_BPMN_WITH_DI.encode()), "test.bpmn"),
            "format": "png",
            "dpi": "9999",
        }
        resp = client.post("/api/convert", data=data,
                           content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_convert_invalid_scale_returns_400(self, client):
        data = {
            "file": (io.BytesIO(SAMPLE_BPMN_WITH_DI.encode()), "test.bpmn"),
            "format": "png",
            "scale": "0.1",
        }
        resp = client.post("/api/convert", data=data,
                           content_type="multipart/form-data")
        assert resp.status_code == 400


class TestPreviewEndpoint:
    def test_preview_returns_base64(self, client):
        data = {
            "file": (io.BytesIO(SAMPLE_BPMN_WITH_DI.encode()), "test.bpmn"),
            "format": "svg",
        }
        resp = client.post("/api/convert/preview", data=data,
                           content_type="multipart/form-data")
        assert resp.status_code == 200
        json_data = resp.get_json()
        assert json_data["success"] is True
        assert json_data["image"].startswith("data:image/svg+xml;base64,")

    def test_preview_no_di_returns_base64(self, client):
        """Preview of BPMN without DI should also work."""
        data = {
            "file": (io.BytesIO(SAMPLE_BPMN_NO_DI.encode()), "test.bpmn"),
            "format": "svg",
        }
        resp = client.post("/api/convert/preview", data=data,
                           content_type="multipart/form-data")
        assert resp.status_code == 200
        json_data = resp.get_json()
        assert json_data["success"] is True

    def test_preview_invalid_dpi_returns_400(self, client):
        """Preview should enforce same DPI validation as convert."""
        data = {
            "file": (io.BytesIO(SAMPLE_BPMN_WITH_DI.encode()), "test.bpmn"),
            "format": "png",
            "dpi": "9999",
        }
        resp = client.post("/api/convert/preview", data=data,
                           content_type="multipart/form-data")
        assert resp.status_code == 400
        json_data = resp.get_json()
        assert "DPI" in json_data["error"]

    def test_preview_invalid_scale_returns_400(self, client):
        """Preview should enforce same scale validation as convert."""
        data = {
            "file": (io.BytesIO(SAMPLE_BPMN_WITH_DI.encode()), "test.bpmn"),
            "format": "png",
            "scale": "99.0",
        }
        resp = client.post("/api/convert/preview", data=data,
                           content_type="multipart/form-data")
        assert resp.status_code == 400
        json_data = resp.get_json()
        assert "Scale" in json_data["error"]

    def test_preview_no_file_returns_400(self, client):
        """Preview should reject requests without file."""
        resp = client.post("/api/convert/preview", data={},
                           content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_preview_wrong_extension_returns_400(self, client):
        """Preview should reject invalid file extensions."""
        data = {
            "file": (io.BytesIO(SAMPLE_BPMN_WITH_DI.encode()), "test.jpg"),
            "format": "svg",
        }
        resp = client.post("/api/convert/preview", data=data,
                           content_type="multipart/form-data")
        assert resp.status_code == 400

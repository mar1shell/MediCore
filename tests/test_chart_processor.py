"""Service-level tests for backend/ocr/chart_processor.py with mocked HTTP."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.ocr.chart_processor import ChartProcessor, OCRProcessingError, _detect_mime
from backend.ocr.config import OCRConfig
from backend.ocr.models import OCRResult


@pytest.fixture
def config() -> OCRConfig:
    return OCRConfig(api_key="test-key", request_timeout=10.0)


def _mistral_ocr_response(pages: list[dict] | None = None) -> MagicMock:
    """Build a fake httpx response resembling Mistral OCR output."""
    if pages is None:
        pages = [
            {
                "index": 0,
                "markdown": "Patient: John Smith\nAllergies: Penicillin",
                "dimensions": {"width": 595.0, "height": 842.0},
            }
        ]
    payload = {"pages": pages, "model": "mistral-ocr-latest", "usage_info": {"pages_processed": len(pages)}}
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ---------------------------------------------------------------------------
# _detect_mime helper
# ---------------------------------------------------------------------------

class TestDetectMime:
    def test_explicit_pdf(self):
        assert _detect_mime("chart.pdf", "application/pdf") == "application/pdf"

    def test_explicit_jpeg(self):
        assert _detect_mime("scan.jpg", "image/jpeg") == "image/jpeg"

    def test_falls_back_to_extension(self):
        assert _detect_mime("chart.pdf", None) == "application/pdf"
        assert _detect_mime("scan.png", None) == "image/png"
        assert _detect_mime("scan.jpg", None) == "image/jpeg"

    def test_unsupported_raises(self):
        with pytest.raises(OCRProcessingError):
            _detect_mime("notes.txt", "text/plain")

    def test_no_extension_no_content_type_raises(self):
        with pytest.raises(OCRProcessingError):
            _detect_mime("chartfile", None)


# ---------------------------------------------------------------------------
# ChartProcessor.process — success paths
# ---------------------------------------------------------------------------

class TestChartProcessor:
    @pytest.mark.asyncio
    async def test_process_pdf_success(self, config):
        async with ChartProcessor(config) as processor:
            with patch.object(processor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_ocr_response()
                result = await processor.process(b"%PDF stub", "chart.pdf", "application/pdf")

        assert isinstance(result, OCRResult)
        assert result.filename == "chart.pdf"
        assert result.pages_processed == 1
        assert "John Smith" in result.full_text

    @pytest.mark.asyncio
    async def test_process_image_success(self, config):
        async with ChartProcessor(config) as processor:
            with patch.object(processor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_ocr_response()
                result = await processor.process(b"\x89PNG...", "chart.png", "image/png")

        assert result.model_used == "mistral-ocr-latest"

    @pytest.mark.asyncio
    async def test_process_multi_page(self, config):
        pages = [
            {"index": 0, "markdown": "Page 1 content", "dimensions": {"width": 595.0, "height": 842.0}},
            {"index": 1, "markdown": "Page 2 content", "dimensions": {"width": 595.0, "height": 842.0}},
        ]
        async with ChartProcessor(config) as processor:
            with patch.object(processor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_ocr_response(pages)
                result = await processor.process(b"%PDF stub", "chart.pdf", "application/pdf")

        assert result.pages_processed == 2
        assert len(result.pages) == 2
        assert "Page 1 content" in result.full_text
        assert "Page 2 content" in result.full_text

    @pytest.mark.asyncio
    async def test_process_returns_correct_char_count(self, config):
        text = "x" * 200
        pages = [{"index": 0, "markdown": text, "dimensions": {}}]
        async with ChartProcessor(config) as processor:
            with patch.object(processor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_ocr_response(pages)
                result = await processor.process(b"%PDF stub", "chart.pdf", "application/pdf")

        assert result.char_count == 200
        assert result.is_usable is True

    # -----------------------------------------------------------------------
    # Error paths
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_process_raises_on_empty_pages(self, config):
        empty_resp = MagicMock()
        empty_resp.json.return_value = {"pages": [], "model": "mistral-ocr-latest", "usage_info": {}}
        empty_resp.raise_for_status = MagicMock()

        async with ChartProcessor(config) as processor:
            with patch.object(processor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = empty_resp
                with pytest.raises(OCRProcessingError, match="no pages"):
                    await processor.process(b"%PDF stub", "chart.pdf", "application/pdf")

    @pytest.mark.asyncio
    async def test_process_raises_on_http_error(self, config):
        import httpx

        async with ChartProcessor(config) as processor:
            error_resp = MagicMock()
            error_resp.status_code = 429
            error_resp.text = "Rate limit exceeded"
            http_err = httpx.HTTPStatusError("429", request=MagicMock(), response=error_resp)

            with patch.object(processor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = http_err
                with pytest.raises(OCRProcessingError, match="429"):
                    await processor.process(b"%PDF stub", "chart.pdf", "application/pdf")

    @pytest.mark.asyncio
    async def test_process_raises_on_timeout(self, config):
        import httpx

        async with ChartProcessor(config) as processor:
            with patch.object(processor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = httpx.ReadTimeout("timeout")
                with pytest.raises(OCRProcessingError, match="timeout"):
                    await processor.process(b"%PDF stub", "chart.pdf", "application/pdf")

    @pytest.mark.asyncio
    async def test_process_raises_on_network_error(self, config):
        import httpx

        async with ChartProcessor(config) as processor:
            with patch.object(processor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = httpx.ConnectError("unreachable")
                with pytest.raises(OCRProcessingError, match="Network error"):
                    await processor.process(b"%PDF stub", "chart.pdf", "application/pdf")

    # -----------------------------------------------------------------------
    # Payload structure
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_pdf_payload_uses_document_url(self, config):
        async with ChartProcessor(config) as processor:
            with patch.object(processor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_ocr_response()
                await processor.process(b"%PDF stub", "chart.pdf", "application/pdf")

        call_kwargs = mock_post.call_args
        payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
        assert payload["document"]["type"] == "document_url"
        assert payload["document"]["document_url"].startswith("data:application/pdf;base64,")

    @pytest.mark.asyncio
    async def test_image_payload_uses_image_url(self, config):
        async with ChartProcessor(config) as processor:
            with patch.object(processor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_ocr_response()
                await processor.process(b"\x89PNG", "scan.png", "image/png")

        call_kwargs = mock_post.call_args
        payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
        assert payload["document"]["type"] == "image_url"
        assert payload["document"]["image_url"].startswith("data:image/png;base64,")

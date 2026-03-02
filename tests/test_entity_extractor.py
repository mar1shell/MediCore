"""Service-level tests for backend/ocr/entity_extractor.py with mocked HTTP."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.ocr.entity_extractor import EntityExtractor, EntityExtractionError
from backend.ocr.config import OCRConfig
from backend.ocr.models import ExtractedEntities


@pytest.fixture
def config() -> OCRConfig:
    return OCRConfig(api_key="test-key", request_timeout=10.0)


def _mistral_chat_response(data: dict) -> MagicMock:
    """Build a fake httpx response resembling Mistral chat completions output."""
    content = json.dumps(data)
    payload = {"choices": [{"message": {"content": content}}]}
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


FULL_CHART_TEXT = (
    "Patient: John Smith, DOB: 1960-03-14\n"
    "Allergies: Penicillin (anaphylaxis)\n"
    "Current medications: Metformin 500mg twice daily, Lisinopril 10mg once daily\n"
    "Diagnosis: Type 2 Diabetes Mellitus with Hypertension\n"
)


# ---------------------------------------------------------------------------
# Successful extraction
# ---------------------------------------------------------------------------

class TestEntityExtractor:
    @pytest.mark.asyncio
    async def test_extract_returns_entities(self, config):
        response_data = {
            "allergies": ["penicillin"],
            "medications": [{"name": "metformin", "dose": "500mg twice daily"}],
            "diagnosis": "type 2 diabetes mellitus",
            "extraction_notes": None,
        }
        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_chat_response(response_data)
                result = await extractor.extract(FULL_CHART_TEXT)

        assert isinstance(result, ExtractedEntities)
        assert result.allergies == ["penicillin"]
        assert len(result.medications) == 1
        assert result.medications[0]["name"] == "metformin"
        assert result.diagnosis == "type 2 diabetes mellitus"

    @pytest.mark.asyncio
    async def test_extract_source_defaults_to_chart(self, config):
        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_chat_response({"allergies": [], "medications": [], "diagnosis": None})
                result = await extractor.extract(FULL_CHART_TEXT)
        assert result.source == "chart"

    @pytest.mark.asyncio
    async def test_extract_spoken_source(self, config):
        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_chat_response({"allergies": [], "medications": [], "diagnosis": None})
                result = await extractor.extract(FULL_CHART_TEXT, source="spoken")
        assert result.source == "spoken"

    @pytest.mark.asyncio
    async def test_extract_allergies_lowercased(self, config):
        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_chat_response({
                    "allergies": ["PENICILLIN", "Sulfa Drugs"],
                    "medications": [],
                    "diagnosis": None,
                })
                result = await extractor.extract(FULL_CHART_TEXT)
        assert result.allergies == ["penicillin", "sulfa drugs"]

    @pytest.mark.asyncio
    async def test_extract_medications_lowercased(self, config):
        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_chat_response({
                    "allergies": [],
                    "medications": [{"name": "METFORMIN", "dose": "500MG"}],
                    "diagnosis": None,
                })
                result = await extractor.extract(FULL_CHART_TEXT)
        assert result.medications[0]["name"] == "metformin"

    @pytest.mark.asyncio
    async def test_extract_skips_meds_without_name(self, config):
        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_chat_response({
                    "allergies": [],
                    "medications": [{"name": "", "dose": "10mg"}, {"name": "lisinopril", "dose": "10mg"}],
                    "diagnosis": None,
                })
                result = await extractor.extract(FULL_CHART_TEXT)
        assert len(result.medications) == 1
        assert result.medications[0]["name"] == "lisinopril"

    @pytest.mark.asyncio
    async def test_extract_empty_allergies_when_nkda(self, config):
        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_chat_response({
                    "allergies": [],
                    "medications": [],
                    "diagnosis": "NKDA noted",
                })
                result = await extractor.extract("Patient denies allergies (NKDA)")
        assert result.allergies == []

    # -----------------------------------------------------------------------
    # Short / empty text — returns empty entities without calling API
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_extract_short_text_returns_empty_without_api_call(self, config):
        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                result = await extractor.extract("too short")
                mock_post.assert_not_called()

        assert result.allergies == []
        assert result.medications == []

    @pytest.mark.asyncio
    async def test_extract_empty_string_returns_empty(self, config):
        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                result = await extractor.extract("")
                mock_post.assert_not_called()

        assert isinstance(result, ExtractedEntities)

    # -----------------------------------------------------------------------
    # Error paths
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_extract_raises_on_http_error(self, config):
        import httpx

        async with EntityExtractor(config) as extractor:
            err_resp = MagicMock()
            err_resp.status_code = 401
            err_resp.text = "Unauthorized"
            http_err = httpx.HTTPStatusError("401", request=MagicMock(), response=err_resp)

            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = http_err
                with pytest.raises(EntityExtractionError, match="401"):
                    await extractor.extract(FULL_CHART_TEXT)

    @pytest.mark.asyncio
    async def test_extract_raises_on_invalid_json_response(self, config):
        bad_resp = MagicMock()
        bad_resp.json.return_value = {"choices": [{"message": {"content": "not valid JSON {"}}]}
        bad_resp.raise_for_status = MagicMock()

        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = bad_resp
                with pytest.raises(EntityExtractionError, match="Invalid response"):
                    await extractor.extract(FULL_CHART_TEXT)

    @pytest.mark.asyncio
    async def test_extract_raises_on_malformed_response_structure(self, config):
        bad_resp = MagicMock()
        bad_resp.json.return_value = {"unexpected": "structure"}
        bad_resp.raise_for_status = MagicMock()

        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = bad_resp
                with pytest.raises(EntityExtractionError):
                    await extractor.extract(FULL_CHART_TEXT)

    @pytest.mark.asyncio
    async def test_extract_raises_on_network_error(self, config):
        import httpx

        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = httpx.ConnectError("unreachable")
                with pytest.raises(EntityExtractionError, match="Error calling Mistral"):
                    await extractor.extract(FULL_CHART_TEXT)

    # -----------------------------------------------------------------------
    # Input truncation at 8000 chars
    # -----------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_extract_truncates_long_text(self, config):
        long_text = "A" * 20_000

        async with EntityExtractor(config) as extractor:
            with patch.object(extractor.client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _mistral_chat_response(
                    {"allergies": [], "medications": [], "diagnosis": None}
                )
                await extractor.extract(long_text)

        # Verify the user message content was truncated to 8000 chars
        call_kwargs = mock_post.call_args
        payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
        user_msg = payload["messages"][1]["content"]
        # The template text adds some overhead; the embedded text portion is at most 8000
        assert len(user_msg) <= 8000 + 200  # 200 chars headroom for template wrapper

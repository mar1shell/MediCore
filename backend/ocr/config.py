import os
from dataclasses import dataclass

@dataclass
class OCRConfig:
    api_key: str
    request_timeout: float = 60.0
    @classmethod
    def from_env(cls) -> "OCRConfig":
        api_key = os.environ.get("MISTRAL_API_KEY", "")
        if not api_key:
            raise EnvironmentError("MISTRAL_API_KEY environment variable is not set.")
        return cls(
            api_key=api_key,
            request_timeout=float(os.environ.get("OCR_REQUEST_TIMEOUT", 60.0))
        )
        
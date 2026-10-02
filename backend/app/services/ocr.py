import io
import json
from dataclasses import dataclass

from pypdf import PdfReader


@dataclass
class OCRResult:
    text: str
    fields: dict
    pages: int = 1
    provider: str = "unknown"


class OCRProvider:
    def extract(self, content: bytes, content_type: str) -> OCRResult:
        raise NotImplementedError


class PaddleOCRProvider(OCRProvider):
    def __init__(self):
        self.engine = None

    def extract(self, content: bytes, content_type: str) -> OCRResult:
        if content_type == "application/pdf":
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
            return OCRResult(text=text, fields={}, pages=len(reader.pages), provider="pypdf")
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError("PaddleOCR 未安装，请安装 backend 的 ocr extra") from exc
        if self.engine is None:
            self.engine = PaddleOCR(use_angle_cls=True, lang="ch")
        result = self.engine.ocr(content, cls=True)
        lines: list[str] = []
        for page in result or []:
            for line in page or []:
                if len(line) >= 2 and line[1]:
                    lines.append(str(line[1][0]))
        return OCRResult(text="\n".join(lines), fields={}, provider="paddleocr")


def get_ocr_provider(provider_name: str) -> OCRProvider:
    if provider_name.lower() == "paddleocr":
        return PaddleOCRProvider()
    raise RuntimeError(f"不支持的 OCR_PROVIDER: {provider_name}")


def result_json(result: OCRResult) -> str:
    return json.dumps({"text": result.text, "fields": result.fields, "pages": result.pages, "provider": result.provider}, ensure_ascii=False)

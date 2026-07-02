import base64
import io

import pypdf

from app.llm.base import Message
from app.llm.router import TaskType, router

MIN_CHARS_PER_PAGE = 40


def _extract_native_text(raw_bytes: bytes) -> list[str]:
    reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
    return [page.extract_text() or "" for page in reader.pages]


async def _vision_ocr_page(pdf_bytes: bytes, page_index: int) -> str:
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(pdf_bytes)
    page = pdf[page_index]
    bitmap = page.render(scale=2.0)
    pil_image = bitmap.to_pil()
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    messages = [
        Message(role="system", content="Transcribe all visible text from this document page exactly, preserving structure. Output only the transcribed text."),
        Message(role="user", content="Transcribe this page.", image_base64=image_b64, image_media_type="image/png"),
    ]
    response = await router.complete_with_fallback(TaskType.SUMMARIZATION, messages, max_tokens=2048)
    return response.content


async def parse_pdf(raw_bytes: bytes, allow_vision_fallback: bool = True) -> list[tuple[str, int | None]]:
    native_pages = _extract_native_text(raw_bytes)
    results: list[tuple[str, int | None]] = []
    for index, text in enumerate(native_pages):
        if len(text.strip()) >= MIN_CHARS_PER_PAGE or not allow_vision_fallback:
            results.append((text, index + 1))
        else:
            ocr_text = await _vision_ocr_page(raw_bytes, index)
            results.append((ocr_text, index + 1))
    return results

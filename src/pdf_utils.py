import re
from dataclasses import dataclass
from typing import List
from pypdf import PdfReader


@dataclass
class UploadedPdf:
    filename: str
    text: str
    category: str
    page_count: int


CATEGORY_RULES = [
    ("main_notice", ["채용 공고", "채용공고", "전형일정", "응시자격", "접수기간", "채용분야 및 규모"]),
    ("job_description", ["직무기술서", "NCS", "직무수행", "필요지식", "필요기술"]),
    ("application_form", ["입사지원서", "자기소개서", "자기 소개서", "지원동기", "경험", "역량"]),
    ("ai_guide", ["AI전형", "AI 전형", "역량검사", "AI역량검사", "진행방법"]),
    ("return_request", ["채용서류 반환청구서", "반환청구서"]),
    ("appeal_form", ["이의신청서", "채용 이의신청서"]),
    ("major_list", ["관련학과", "국가기술자격의 종목별 관련학과", "직무분야별 학과"]),
]


CATEGORY_LABELS = {
    "main_notice": "메인 채용공고",
    "job_description": "직무기술서",
    "application_form": "입사지원서/자기소개서",
    "ai_guide": "AI전형 안내",
    "return_request": "채용서류 반환청구서",
    "appeal_form": "채용 이의신청서",
    "major_list": "관련학과 목록",
    "reference": "기타 참고자료",
}


def read_pdf(uploaded_file) -> tuple[str, int]:
    reader = PdfReader(uploaded_file)
    parts = []
    for i, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            parts.append(f"\n--- PAGE {i} ---\n{page_text.strip()}")
    return "\n".join(parts).strip(), len(reader.pages)


def classify_pdf(filename: str, text: str) -> str:
    haystack = f"{filename}\n{text[:5000]}".lower().replace(" ", "")
    scores = {}
    for category, keywords in CATEGORY_RULES:
        score = 0
        for keyword in keywords:
            if keyword.lower().replace(" ", "") in haystack:
                score += 1
        if score:
            scores[category] = score
    if not scores:
        return "reference"
    return max(scores, key=scores.get)


def compact_text(text: str, max_chars: int = 60000) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) <= max_chars:
        return text
    head = text[: int(max_chars * 0.72)]
    tail = text[-int(max_chars * 0.28):]
    return head + "\n\n...[중간 일부 생략]...\n\n" + tail


def prepare_documents(uploaded_files) -> List[UploadedPdf]:
    docs = []
    for uploaded_file in uploaded_files:
        uploaded_file.seek(0)
        text, page_count = read_pdf(uploaded_file)
        category = classify_pdf(uploaded_file.name, text)
        docs.append(UploadedPdf(uploaded_file.name, text, category, page_count))
    return docs


def build_source_bundle(docs: List[UploadedPdf]) -> str:
    order = {
        "main_notice": 0,
        "job_description": 1,
        "application_form": 2,
        "ai_guide": 3,
        "major_list": 4,
        "reference": 5,
        "return_request": 6,
        "appeal_form": 7,
    }
    sorted_docs = sorted(docs, key=lambda d: order.get(d.category, 99))
    chunks = []
    for doc in sorted_docs:
        chunks.append(
            f"===== FILE: {doc.filename} / CATEGORY: {doc.category} / PAGES: {doc.page_count} =====\n{doc.text}"
        )
    return compact_text("\n\n".join(chunks))

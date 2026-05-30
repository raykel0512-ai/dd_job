import json
import os
import re
import streamlit as st

from .schema import DEFAULT_FIELDS


def extract_json_from_text(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def api_key(name: str):
    return os.getenv(name) or st.secrets.get(name, None)


def build_prompt(source_bundle: str, target_field_hint: str, school_context: str) -> str:
    schema_json = json.dumps(DEFAULT_FIELDS, ensure_ascii=False, indent=2)
    return f"""
너는 특성화고 취업부 교사를 돕는 채용공고 정리 전문가다.
업로드된 여러 PDF 원문을 읽고 학교 배포용 정보를 JSON으로 정리해라.

사용 목적:
- 담임교사에게 메신저로 전달
- 학생에게 공고 핵심만 쉽게 안내
- 카카오톡용 짧은 요약 생성
- 자기소개서 문항 및 첨부파일 안내 추출

학교/업무 맥락:
{school_context or "특성화고 취업부"}

우선 추출할 분야:
{target_field_hint or "고졸전형, 신입, 학생 지원 가능 분야"}

규칙:
1. JSON만 출력한다. 코드블록, 설명 금지.
2. 공고에 여러 직무가 있으면 우선 추출할 분야를 기준으로 하나를 선택한다.
3. 고졸전형, 신입, 학생 지원 가능 분야가 있으면 우선한다.
4. 원문에 없는 내용은 추측하지 말고 "확인 필요"라고 쓴다.
5. 접수기간, 마감시간, URL, 근무지, 인원은 특히 정확히 쓴다.
6. self_intro_questions는 자기소개서 문항을 배열로 넣는다. 없으면 빈 배열.
7. attachments_to_forward에는 학생/담임에게 함께 전달해야 할 첨부파일명을 넣는다.
8. exclude_attachments에는 반환청구서, 이의신청서처럼 보통 학급 배포 우선순위가 낮은 파일명을 넣는다.
9. ai_test_notice에는 AI전형이 있으면 응시 필요 여부와 핵심 안내를 간단히 쓴다.
10. available_majors는 관련학과 제한이 있는 경우 요약한다. 학교 학과명 매칭은 확실하지 않으면 "확인 필요"라고 쓴다.
11. missing_fields에는 확인이 필요한 필드명을 배열로 넣는다.
12. confidence는 "높음", "보통", "낮음" 중 하나로 쓴다.

반드시 아래 키를 모두 포함한다:
{schema_json}

PDF 원문:
{source_bundle}
""".strip()


def call_openai(prompt: str, model: str) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=api_key("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        temperature=0.1,
        messages=[
            {"role": "system", "content": "너는 채용공고를 학교 배포용 문구로 정확히 변환하는 도우미다."},
            {"role": "user", "content": prompt},
        ],
    )
    return extract_json_from_text(response.choices[0].message.content)


def call_gemini(prompt: str, model: str) -> dict:
    import google.generativeai as genai
    genai.configure(api_key=api_key("GEMINI_API_KEY"))
    gemini_model = genai.GenerativeModel(model)
    response = gemini_model.generate_content(prompt)
    return extract_json_from_text(response.text)


def normalize_result(result: dict) -> dict:
    normalized = DEFAULT_FIELDS.copy()
    normalized.update(result or {})
    for key, value in list(normalized.items()):
        if value is None:
            normalized[key] = "" if key in ["application_url", "notes"] else "확인 필요"
    if not isinstance(normalized.get("self_intro_questions"), list):
        normalized["self_intro_questions"] = [str(normalized["self_intro_questions"])]
    if not isinstance(normalized.get("attachments_to_forward"), list):
        normalized["attachments_to_forward"] = [str(normalized["attachments_to_forward"])]
    if not isinstance(normalized.get("exclude_attachments"), list):
        normalized["exclude_attachments"] = [str(normalized["exclude_attachments"])]
    if not isinstance(normalized.get("missing_fields"), list):
        normalized["missing_fields"] = [str(normalized["missing_fields"])]
    return normalized

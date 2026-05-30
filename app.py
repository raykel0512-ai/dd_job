import json
import re
from datetime import datetime

import streamlit as st

from src.ai_clients import (
    api_key,
    build_prompt,
    call_gemini,
    call_openai,
    normalize_result,
)
from src.docx_utils import make_docx
from src.pdf_utils import CATEGORY_LABELS, build_source_bundle, prepare_documents
from src.schema import FIELD_LABELS
from src.templates import kakao_notice, review_checklist, student_notice, teacher_notice


APP_TITLE = "취업공고 배포문 자동 변환기 PRO"


def safe_filename(text: str) -> str:
    text = re.sub(r"[^가-힣a-zA-Z0-9_-]+", "_", text or "채용공고").strip("_")
    return text or "채용공고"


def init_state():
    defaults = {
        "docs": [],
        "result": None,
        "teacher_text": "",
        "student_text": "",
        "kakao_text": "",
        "checklist_text": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def regenerate_texts(student_deadline: str, manager_name: str):
    data = st.session_state.result or {}
    st.session_state.teacher_text = teacher_notice(data, student_deadline, manager_name)
    st.session_state.student_text = student_notice(data)
    st.session_state.kakao_text = kakao_notice(data, student_deadline)
    st.session_state.checklist_text = review_checklist(data)


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="📌", layout="wide")
    init_state()

    st.title("📌 취업공고 배포문 자동 변환기 PRO")
    st.caption("채용공고 PDF 묶음을 업로드하면 교사용/학생용/카톡용 배포문을 자동 생성합니다.")

    with st.sidebar:
        st.header("기본 설정")
        provider = st.radio("AI 제공자", ["OpenAI GPT", "Google Gemini"])

        if provider == "OpenAI GPT":
            model = st.selectbox("모델", ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"])
            has_key = bool(api_key("OPENAI_API_KEY"))
            st.caption("필요 키: OPENAI_API_KEY")
        else:
            model = st.selectbox("모델", ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.1-pro"])
            has_key = bool(api_key("GEMINI_API_KEY"))
            st.caption("필요 키: GEMINI_API_KEY")

        if not has_key:
            st.warning("API 키가 없습니다. .env 또는 Streamlit Secrets에 등록하세요.")

        target_field_hint = st.text_input("우선 추출할 채용분야", "고졸전형 또는 사무행정")
        school_context = st.text_area("학교/업무 맥락", "특성화고 취업부, 담임교사에게 메신저로 채용공고 전달")
        student_deadline = st.text_input("지원 학생 명단 요청 기한", "6.11(목)")
        manager_name = st.text_input("취업특성화부 부장 성함", "이유정")

    uploaded_files = st.file_uploader(
        "PDF 파일을 업로드하세요",
        type=["pdf"],
        accept_multiple_files=True,
        help="채용공고, 직무기술서, 입사지원서, AI전형 안내자료 등을 한 번에 올리세요.",
    )

    col1, col2 = st.columns([1.05, 0.95])

    with col1:
        st.subheader("1. 파일 자동 분류")
        if uploaded_files:
            if st.button("PDF 읽기/분류", type="secondary"):
                with st.spinner("PDF 텍스트를 추출하고 파일을 분류하는 중입니다..."):
                    st.session_state.docs = prepare_documents(uploaded_files)

        if st.session_state.docs:
            rows = []
            for doc in st.session_state.docs:
                rows.append({
                    "파일명": doc.filename,
                    "분류": CATEGORY_LABELS.get(doc.category, doc.category),
                    "페이지": doc.page_count,
                    "추출 글자수": len(doc.text),
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

            with st.expander("분류된 원문 미리보기"):
                for doc in st.session_state.docs:
                    st.markdown(f"**{doc.filename}** · {CATEGORY_LABELS.get(doc.category, doc.category)}")
                    st.text_area(
                        f"preview_{doc.filename}",
                        doc.text[:3000],
                        height=180,
                        label_visibility="collapsed",
                    )

        analyze_disabled = not st.session_state.docs or not has_key
        if st.button("2. 공고문 분석하기", type="primary", disabled=analyze_disabled):
            with st.spinner("AI가 채용정보를 추출하고 있습니다..."):
                bundle = build_source_bundle(st.session_state.docs)
                prompt = build_prompt(bundle, target_field_hint, school_context)
                try:
                    if provider == "OpenAI GPT":
                        result = call_openai(prompt, model)
                    else:
                        result = call_gemini(prompt, model)
                    st.session_state.result = normalize_result(result)
                    regenerate_texts(student_deadline, manager_name)
                    st.success("분석 완료!")
                except Exception as exc:
                    st.error(f"분석 실패: {exc}")

    with col2:
        st.subheader("2. 추출 정보 확인/수정")
        if not st.session_state.result:
            st.info("먼저 PDF를 분류하고 공고문 분석을 실행하세요.")
        else:
            edited = dict(st.session_state.result)
            for key, label in FIELD_LABELS.items():
                default = edited.get(key, "")
                if key in ["eligibility", "preferred", "process", "required_documents", "ai_test_notice", "available_majors", "notes"]:
                    edited[key] = st.text_area(label, str(default), height=80)
                else:
                    edited[key] = st.text_input(label, str(default))

            st.markdown("**자기소개서 문항**")
            questions_text = st.text_area(
                "문항을 줄바꿈으로 구분",
                "\n".join(map(str, edited.get("self_intro_questions", []))),
                height=120,
                label_visibility="collapsed",
            )
            edited["self_intro_questions"] = [q.strip("- ").strip() for q in questions_text.splitlines() if q.strip()]

            st.markdown("**함께 전달 권장 첨부파일**")
            attach_text = st.text_area(
                "첨부파일을 줄바꿈으로 구분",
                "\n".join(map(str, edited.get("attachments_to_forward", []))),
                height=100,
                label_visibility="collapsed",
            )
            edited["attachments_to_forward"] = [x.strip("- ").strip() for x in attach_text.splitlines() if x.strip()]

            if st.button("수정 내용으로 문구 재생성"):
                st.session_state.result = normalize_result(edited)
                regenerate_texts(student_deadline, manager_name)
                st.success("문구를 다시 생성했습니다.")

            missing = st.session_state.result.get("missing_fields", [])
            if missing:
                st.warning("확인 필요: " + ", ".join(map(str, missing)))
            st.caption(f"AI 추출 신뢰도: {st.session_state.result.get('confidence', '확인 필요')}")

    st.divider()
    st.subheader("3. 생성 문구")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "교사용 배포문",
        "학생용 안내문",
        "카톡용 요약",
        "검토 체크리스트",
        "JSON",
    ])

    with tab1:
        st.session_state.teacher_text = st.text_area("교사용 배포문", st.session_state.teacher_text, height=430)
    with tab2:
        st.session_state.student_text = st.text_area("학생용 안내문", st.session_state.student_text, height=430)
    with tab3:
        st.session_state.kakao_text = st.text_area("카톡용 요약", st.session_state.kakao_text, height=300)
    with tab4:
        st.session_state.checklist_text = st.text_area("검토 체크리스트", st.session_state.checklist_text, height=300)
    with tab5:
        st.json(st.session_state.result or {})

    st.divider()
    st.subheader("4. 다운로드")

    company = safe_filename((st.session_state.result or {}).get("company", "채용공고"))
    today = datetime.now().strftime("%Y%m%d")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.download_button(
            "교사용 TXT",
            st.session_state.teacher_text,
            file_name=f"{today}_{company}_교사용.txt",
            mime="text/plain",
            disabled=not st.session_state.teacher_text,
        )
    with c2:
        st.download_button(
            "학생용 TXT",
            st.session_state.student_text,
            file_name=f"{today}_{company}_학생용.txt",
            mime="text/plain",
            disabled=not st.session_state.student_text,
        )
    with c3:
        all_text = "\n\n".join([
            "[교사용 배포문]",
            st.session_state.teacher_text,
            "[학생용 안내문]",
            st.session_state.student_text,
            "[카톡용 요약]",
            st.session_state.kakao_text,
            "[검토 체크리스트]",
            st.session_state.checklist_text,
        ])
        st.download_button(
            "전체 TXT",
            all_text,
            file_name=f"{today}_{company}_전체.txt",
            mime="text/plain",
            disabled=not all_text.strip(),
        )
    with c4:
        if st.session_state.teacher_text or st.session_state.student_text:
            docx_bytes = make_docx(
                f"{company} 채용공고 배포문",
                {
                    "교사용 배포문": st.session_state.teacher_text,
                    "학생용 안내문": st.session_state.student_text,
                    "카톡용 요약": st.session_state.kakao_text,
                    "검토 체크리스트": st.session_state.checklist_text,
                },
            )
        else:
            docx_bytes = b""
        st.download_button(
            "전체 DOCX",
            docx_bytes,
            file_name=f"{today}_{company}_배포문.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            disabled=not docx_bytes,
        )

    if st.session_state.result:
        st.download_button(
            "추출 JSON 다운로드",
            json.dumps(st.session_state.result, ensure_ascii=False, indent=2),
            file_name=f"{today}_{company}_추출결과.json",
            mime="application/json",
        )

    st.info("최종 배포 전에는 접수기간, URL, 채용인원, 지원자격을 원문과 한 번 더 대조하세요.")


if __name__ == "__main__":
    main()

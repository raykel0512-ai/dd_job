from typing import Dict, List


def val(data: Dict, key: str) -> str:
    value = data.get(key, "확인 필요")
    if value is None or value == "":
        return "" if key == "application_url" else "확인 필요"
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value) if value else "없음"
    return str(value)


def inline_list(value) -> str:
    if isinstance(value, list):
        return ", ".join(map(str, value)) if value else "없음"
    return str(value or "확인 필요")


def teacher_notice(data: Dict, student_deadline: str, manager_name: str = "이유정") -> str:
    return f"""선생님 안녕하세요 :)
지원 학생의 학번, 이름을 {student_deadline}까지 부탁드립니다. 감사합니다.

학기 중에는 담임선생님께 메신저를 통해 채용공고를 안내하고 있습니다. (단톡방 안내 지양)
★해당 공고와 첨부파일★ 모두 학급에 전달 부탁드립니다.

아울러, 취업진행상황을 취업특성화부 선생님들께 공유 부탁드립니다
- 진행상황 공유 내용 : 지원자 명단 및 채용진행상황(서류, 필기, 면접 합불여부)
- 취업담당 선생님이 부재중일 경우 취업특성화부 부장 {manager_name} 선생님을 참조로 넣어서 보내주세요

[채용공고]
- 기업체명 : {val(data, "company")}
- 근무지 : {val(data, "work_location")}
- 채용 분야 : {val(data, "recruitment_field")}
- 채용 직급 : {val(data, "job_grade")}
- 채용 직무 : {val(data, "job_duty")}
- 채용인원 : {val(data, "headcount")}
- 고용형태 : {val(data, "employment_type")}
- 지원 자격 : {val(data, "eligibility")}
- 채용 절차 : {val(data, "process")}
- 우대 사항 : {val(data, "preferred")}
- 접수 기간 : {val(data, "application_period")}
- 접수 방법 : {val(data, "application_method")}
{val(data, "application_url")}

[추가 안내]
- AI전형 : {val(data, "ai_test_notice")}
- 제출/증빙서류 : {val(data, "required_documents")}
- 관련학과/전공 : {val(data, "available_majors")}

[함께 전달 권장 첨부파일]
{val(data, "attachments_to_forward")}
"""


def student_notice(data: Dict) -> str:
    return f"""[채용공고 안내]

{val(data, "company")} 채용공고를 안내합니다.

- 근무지 : {val(data, "work_location")}
- 채용 분야 : {val(data, "recruitment_field")}
- 채용 직급 : {val(data, "job_grade")}
- 채용 직무 : {val(data, "job_duty")}
- 채용인원 : {val(data, "headcount")}
- 고용형태 : {val(data, "employment_type")}
- 지원 자격 : {val(data, "eligibility")}
- 우대 사항 : {val(data, "preferred")}
- 전형 절차 : {val(data, "process")}
- 접수 기간 : {val(data, "application_period")}
- 접수 방법 : {val(data, "application_method")}
{val(data, "application_url")}

[AI전형 안내]
{val(data, "ai_test_notice")}

[자기소개서 문항]
{val(data, "self_intro_questions")}

관심 있는 학생은 기한 내 지원하고, 지원 여부를 담임선생님께 알려주세요.
"""


def kakao_notice(data: Dict, student_deadline: str) -> str:
    return f"""[{val(data, "company")} 채용공고]
- 분야: {val(data, "recruitment_field")}
- 근무지: {val(data, "work_location")}
- 인원: {val(data, "headcount")}
- 자격: {val(data, "eligibility")}
- 우대: {val(data, "preferred")}
- 접수: {val(data, "application_period")}
- 방법: {val(data, "application_method")}
{val(data, "application_url")}

지원 희망 학생은 {student_deadline}까지 학번/이름을 알려주세요.
"""


def review_checklist(data: Dict) -> str:
    missing = data.get("missing_fields", [])
    missing_text = ", ".join(map(str, missing)) if missing else "없음"
    excluded = inline_list(data.get("exclude_attachments", []))
    return f"""[최종 확인 체크리스트]

1. 접수 마감일/시간 확인: {val(data, "application_period")}
2. 접수 URL 정상 접속 확인: {val(data, "application_url")}
3. 채용인원 확인: {val(data, "headcount")}
4. 지원자격 확인: {val(data, "eligibility")}
5. 우대사항 확인: {val(data, "preferred")}
6. 학급 배포 제외 가능 첨부파일: {excluded}
7. AI 추출 신뢰도: {val(data, "confidence")}
8. 확인 필요 항목: {missing_text}
"""

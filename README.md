# 취업공고 배포문 자동 변환기 PRO

특성화고 취업부에서 받은 채용공고 PDF 묶음을 업로드하면, 교사용/학생용/카톡용 배포문과 자기소개서 문항, 첨부파일 전달 안내까지 자동 생성하는 Streamlit 웹앱입니다.

## 주요 기능

- PDF 여러 개 업로드
- 파일 자동 분류
  - 메인 채용공고
  - 직무기술서
  - 입사지원서/자기소개서
  - AI전형 안내
  - 반환청구서/이의신청서 등 참고자료
- GPT 또는 Gemini 선택
- 채용정보 자동 추출
- 교사용 배포문 생성
- 학생용 안내문 생성
- 카카오톡용 짧은 요약 생성
- 자기소개서 문항 자동 추출
- 첨부파일 전달 안내 생성
- TXT / DOCX 다운로드
- 추출 결과 직접 수정 후 재생성

## 설치

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## API 키 설정

`.env.example`을 `.env`로 복사하고 API 키를 넣습니다.

```bash
cp .env.example .env
```

OpenAI 또는 Gemini 중 하나만 있어도 됩니다.

## 실행

```bash
streamlit run app.py
```

## Streamlit Cloud 배포

1. 이 폴더를 GitHub 저장소에 업로드
2. Streamlit Cloud에서 New app 생성
3. `app.py` 선택
4. App settings > Secrets에 아래 중 하나 등록

```toml
OPENAI_API_KEY = "sk-..."
# 또는
GEMINI_API_KEY = "..."
```

## 추천 사용 흐름

1. 채용공고 PDF를 포함해 관련 PDF 전체 업로드
2. 관심 분야에 `고졸전형`, `사무행정`, `생산직`, `전기`, `정보통신` 등 입력
3. 공고문 분석
4. 추출 정보 확인 및 수정
5. 교사용/학생용/카톡용 문구 다운로드 또는 복사

## 주의

AI가 생성한 내용은 최종 배포 전에 접수마감, URL, 채용인원, 지원자격을 반드시 원문과 대조하세요.

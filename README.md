# 📚 교과서 기반 영어 퀴즈 생성기

한국 고등학교 교과서를 기반으로 AI가 생성하는 맞춤형 영어 퀴즈 애플리케이션입니다.

## 🌟 주요 기능

- **교사 모드**: 지문 난이도 조정 및 퀴즈 생성
- **학생 모드**: 퀴즈 풀기 및 결과 확인
- **AI 기반**: OpenAI GPT를 활용한 지문 재작성 및 문제 생성
- **Firebase 연동**: 퀴즈 저장 및 학생 결과 관리

## 🚀 로컬에서 실행하기

1. 필요한 패키지 설치

   ```bash
   pip install -r requirements.txt
   ```

2. Firebase 인증 파일 설정
   - `firebase-credentials_2.json` 파일을 프로젝트 루트에 배치

3. Secrets 파일 설정
   - `.streamlit/secrets.toml` 파일에 API 키 추가:
   ```toml
   OPENAI_API_KEY = "your-openai-api-key"
   FIREBASE_WEB_API_KEY = "your-firebase-web-api-key"
   ```

4. 앱 실행

   ```bash
   streamlit run app.py
   ```

## 🌐 Streamlit Cloud 배포하기

1. **GitHub에 코드 푸시**
   ```bash
   git add .
   git commit -m "Add quiz generator app"
   git push origin main
   ```

2. **Streamlit Cloud 접속**
   - https://share.streamlit.io/ 방문
   - GitHub 계정으로 로그인

3. **새 앱 배포**
   - "New app" 클릭
   - Repository: `heisly729-star/english-reading`
   - Branch: `main`
   - Main file path: `app.py`
   - 클릭: "Deploy!"

4. **Secrets 설정 (중요!)**
   - 배포 후 앱 설정(⚙️) > "Secrets" 메뉴
   - 다음 내용 추가:
   ```toml
   OPENAI_API_KEY = "your-openai-api-key"
   FIREBASE_WEB_API_KEY = "your-firebase-web-api-key"
   ```

5. **Firebase 인증 파일 설정**
   - `firebase-credentials_2.json` 내용을 secrets에 추가:
   ```toml
   [firebase]
   type = "service_account"
   project_id = "your-project-id"
   # ... 나머지 Firebase 인증 정보
   ```

## 📝 사용 방법

### 교사
1. "교사 입장" 선택
2. 이메일/비밀번호로 로그인
3. 교과서 및 단원 선택
4. 지문 난이도 선택 및 변환
5. 문제 유형 선택 및 생성
6. 퀴즈 저장

### 학생
1. "학생 입장" 선택
2. 이름 입력
3. 최신 퀴즈 불러오기
4. 문제 풀기 및 제출
5. 결과 확인

## 🛠 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python, Firebase Admin SDK
- **Database**: Google Firestore
- **AI**: OpenAI GPT-3.5-turbo
- **Authentication**: Firebase Authentication

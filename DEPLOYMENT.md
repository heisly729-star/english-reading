# 🌐 Streamlit Cloud 배포 가이드

## 📋 배포 전 체크리스트

- [ ] GitHub 저장소에 코드 푸시
- [ ] `.gitignore`에 중요 파일들 추가 확인 (secrets.toml, firebase-credentials_2.json)
- [ ] `requirements.txt` 파일 존재 확인
- [ ] OpenAI API 키 준비
- [ ] Firebase Web API 키 준비
- [ ] Firebase 서비스 계정 JSON 내용 준비

## 🚀 단계별 배포 방법

### 1단계: GitHub에 코드 푸시

```bash
# 변경사항 확인
git status

# 모든 파일 추가 (secrets와 firebase credentials는 자동 제외됨)
git add .

# 커밋
git commit -m "Add English quiz generator app"

# GitHub에 푸시
git push origin main
```

### 2단계: Streamlit Cloud 접속 및 로그인

1. https://share.streamlit.io/ 접속
2. "Sign in with GitHub" 클릭
3. GitHub 계정으로 로그인 및 권한 승인

### 3단계: 새 앱 배포

1. **"New app" 버튼 클릭**

2. **앱 설정 입력:**
   - **Repository:** `heisly729-star/english-reading`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** 원하는 URL (예: `english-quiz-generator`)

3. **"Advanced settings" 클릭 (선택사항)**
   - Python version: 3.9 이상

4. **"Deploy!" 클릭**

### 4단계: Secrets 설정 (매우 중요!)

배포가 시작되면 앱이 실행되기 전에 Secrets를 설정해야 합니다.

1. **앱 페이지에서 ⚙️ (Settings) 클릭**

2. **"Secrets" 탭 선택**

3. **다음 내용을 입력:**

```toml
# OpenAI API Key
OPENAI_API_KEY = "sk-proj-..."

# Firebase Web API Key
FIREBASE_WEB_API_KEY = "AIza..."
```

4. **"Save" 클릭**

### 5단계: Firebase 인증 파일 처리

Firebase 인증 파일(`firebase-credentials_2.json`)은 GitHub에 올리면 안 되므로, 두 가지 방법이 있습니다:

#### 방법 1: 코드 수정 (권장)

`app.py`의 Firebase 초기화 부분을 수정하여 secrets에서 직접 읽어오도록 변경:

```python
# 기존 코드
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-credentials_2.json")
    firebase_admin.initialize_app(cred)

# 수정된 코드
if not firebase_admin._apps:
    if os.path.exists("firebase-credentials_2.json"):
        # 로컬 환경
        cred = credentials.Certificate("firebase-credentials_2.json")
    else:
        # Streamlit Cloud 환경
        firebase_config = {
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": st.secrets["firebase"]["private_key"],
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
        }
        cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)
```

그리고 Streamlit Cloud Secrets에 Firebase 정보 추가:

```toml
[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

⚠️ **주의:** `private_key`는 줄바꿈을 `\n`으로 표현해야 합니다.

#### 방법 2: GitHub Private Repository 사용

1. 저장소를 Private으로 설정
2. `firebase-credentials_2.json` 파일을 포함하여 푸시
3. Streamlit Cloud에서 Private 저장소 접근 권한 승인

### 6단계: 배포 확인

1. **배포 로그 확인**
   - 앱 페이지에서 "Manage app" > "Logs" 확인
   - 에러가 있으면 로그에서 확인 가능

2. **앱 테스트**
   - 배포 완료 후 제공되는 URL로 접속
   - 학생 모드와 교사 모드 모두 테스트

3. **문제 해결**
   - 에러 발생 시 Secrets 설정 재확인
   - Firebase 인증 정보 확인
   - 로그에서 구체적인 에러 메시지 확인

## 🔧 배포 후 관리

### 앱 재시작
- Settings > "Reboot app" 클릭
- Secrets 변경 후 자동으로 재시작됨

### 앱 업데이트
```bash
# 코드 수정 후
git add .
git commit -m "Update app"
git push origin main

# Streamlit Cloud에서 자동으로 재배포됨
```

### 앱 삭제
- Settings > "Delete app" 클릭

## 📊 모니터링

- **Usage:** 앱 사용량 확인
- **Logs:** 실시간 로그 확인
- **Analytics:** 방문자 통계 (Pro 플랜)

## 💡 팁

1. **무료 플랜 제한**
   - 1개의 private 앱
   - 무제한 public 앱
   - 리소스 제한 있음

2. **성능 최적화**
   - `@st.cache_data`, `@st.cache_resource` 활용
   - 불필요한 API 호출 최소화

3. **보안**
   - API 키는 절대 코드에 하드코딩하지 않기
   - Secrets 사용
   - Private 정보는 `.gitignore`에 추가

## 🆘 문제 해결

### "ModuleNotFoundError" 발생
→ `requirements.txt`에 패키지 추가 및 재배포

### Firebase 인증 오류
→ Secrets의 Firebase 설정 확인

### OpenAI API 오류
→ Secrets의 OPENAI_API_KEY 확인 및 API 크레딧 확인

### 앱이 느림
→ 캐싱 활용 및 불필요한 연산 제거

---

배포 성공을 기원합니다! 🎉

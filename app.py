import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os

# =====================
# Firebase Singleton Init (최상단)
# =====================
if not firebase_admin._apps:
    # 로컬 환경에서는 파일에서, Streamlit Cloud에서는 secrets에서 읽기
    if os.path.exists("firebase-credentials_2.json"):
        # 로컬 개발 환경
        cred = credentials.Certificate("firebase-credentials_2.json")
    else:
        # Streamlit Cloud 환경
        try:
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
        except Exception as e:
            st.error(f"❌ Firebase 인증 오류: {str(e)}")
            st.stop()
    firebase_admin.initialize_app(cred)
# Firestore Client 전역 선언
db = firestore.client()

import json
import os
from datetime import datetime
from uuid import uuid4
import requests
from textbooks import TEXTBOOKS, QUESTION_TYPES_INFO

# ============================================================================
# 페이지 설정
# ============================================================================
st.set_page_config(
    page_title="교과서 기반 영어 퀴즈 생성기",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================
# Firebase Auth REST API (이메일/비밀번호 로그인)
# =====================
import requests
FIREBASE_WEB_API_KEY = st.secrets.get("FIREBASE_WEB_API_KEY") or os.getenv("FIREBASE_WEB_API_KEY") or ""
FIREBASE_AUTH_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"

def firebase_email_login(email, password):
    try:
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        resp = requests.post(FIREBASE_AUTH_URL, json=payload)
        resp.raise_for_status()
        return resp.json()  # idToken 등 포함
    except Exception as e:
        return {"error": str(e)}

# =====================
# 메인 진입 화면: 학생/교사 선택
# =====================
if "main_mode" not in st.session_state:
    st.session_state.main_mode = None  # None, "student", "teacher"
if "teacher_logged_in" not in st.session_state:
    st.session_state.teacher_logged_in = False
if "teacher_email" not in st.session_state:
    st.session_state.teacher_email = ""
if "teacher_login_error" not in st.session_state:
    st.session_state.teacher_login_error = ""

def get_all_results():
    """Firestore에서 모든 학생 결과 조회"""
    try:
        db = firestore.client()
        docs = db.collection("results").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        st.error(f"❌ 결과 조회 오류: {str(e)}")
        return []

def show_entry_buttons():
    st.title("교과서 기반 영어 퀴즈 생성기")
    st.write("역할을 선택하세요:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("학생 입장", use_container_width=True):
            st.session_state.main_mode = "student"
    with col2:
        if st.button("교사 입장", use_container_width=True):
            st.session_state.main_mode = "teacher"

def show_teacher_login():
    st.title("교사 로그인")
    email = st.text_input("이메일", value=st.session_state.teacher_email, key="teacher_email_input")
    password = st.text_input("비밀번호", type="password", key="teacher_pw_input")
    login_btn = st.button("로그인", use_container_width=True)
    if login_btn:
        result = firebase_email_login(email, password)
        if "idToken" in result:
            st.session_state.teacher_logged_in = True
            st.session_state.teacher_email = email
            st.session_state.teacher_login_error = ""
        else:
            st.session_state.teacher_login_error = "로그인 실패: 이메일 또는 비밀번호를 확인하세요."
    if st.session_state.teacher_login_error:
        st.error(st.session_state.teacher_login_error)
    st.button("← 뒤로", on_click=lambda: st.session_state.update({"main_mode": None, "teacher_login_error": ""}), use_container_width=True)

def show_teacher_dashboard():
    st.header(f"👨‍🏫 교사 대시보드 ({st.session_state.teacher_email})")
    st.button("로그아웃", on_click=lambda: st.session_state.update({"main_mode": None, "teacher_logged_in": False, "teacher_email": ""}), use_container_width=True)
    tab1, tab2 = st.tabs(["📝 지문/퀴즈 생성", "📊 학생 결과 대시보드"])
    with tab1:
        st.subheader("1. 지문 난이도 결정 및 퀴즈 생성")
        # 기존 퀴즈 생성 UI (지문 선택, 난이도, 변환, 문제 생성 등) 복사
        col1, col2 = st.columns(2)
        with col1:
            textbook_list = list(TEXTBOOKS.keys())
            selected_textbook = st.selectbox(
                "📖 교과서 선택",
                textbook_list,
                key="teacher_textbook_select"
            )
            st.session_state.selected_textbook = selected_textbook
        with col2:
            if st.session_state.selected_textbook:
                chapter_list = list(TEXTBOOKS[st.session_state.selected_textbook].keys())
                selected_chapter = st.selectbox(
                    "📄 단원 선택",
                    chapter_list,
                    key="teacher_chapter_select"
                )
                st.session_state.selected_chapter = selected_chapter
        if st.session_state.selected_textbook and st.session_state.selected_chapter:
            original_passage = TEXTBOOKS[st.session_state.selected_textbook][st.session_state.selected_chapter]["original_passage"]
            st.info("📖 **원본 지문** (읽기 전용)")
            st.text_area(
                "원본 지문",
                value=original_passage,
                height=150,
                disabled=True,
                label_visibility="collapsed",
                key="teacher_original_passage_view"
            )
            difficulty_options = ["쉬움 (Easy)", "보통 (Original)", "어려움 (Hard)"]
            selected_passage_difficulty = st.selectbox(
                "📚 지문 난이도 선택 (Lexile 기준으로 조정됨)",
                difficulty_options,
                key="teacher_passage_difficulty_select",
                help="쉬움: Lexile 1000-1200\n보통: 원본 유지\n어려움: Lexile 1300-1500"
            )
            st.session_state.selected_passage_difficulty = selected_passage_difficulty
            st.write("")
            col_convert, col_space = st.columns([1, 3])
            with col_convert:
                if st.button("🔄 지문 변환하기", use_container_width=True, type="primary", key="teacher_convert_passage_btn"):
                    with st.spinner("🤖 AI가 지문을 변환 중입니다..."):
                        try:
                            api_key = st.session_state.openai_api_key
                            rewritten_passage = rewrite_passage_with_openai(
                                api_key=api_key,
                                original_passage=original_passage,
                                difficulty=st.session_state.selected_passage_difficulty
                            )
                            st.session_state.current_passage = rewritten_passage
                            st.session_state.step1_completed = True
                            st.success("✅ 지문 변환 완료!")
                        except Exception as e:
                            st.error(f"❌ 오류 발생: {str(e)}")
            if st.session_state.step1_completed and st.session_state.current_passage:
                st.divider()
                st.info("✏️ **변환된 지문** (필요시 편집 가능)")
                edited_passage = st.text_area(
                    "변환된 지문",
                    value=st.session_state.current_passage,
                    height=200,
                    label_visibility="collapsed",
                    key="teacher_edited_passage"
                )
                if edited_passage != st.session_state.current_passage:
                    st.session_state.current_passage = edited_passage
            if st.session_state.step1_completed and st.session_state.current_passage:
                st.divider()
                st.subheader("📋 Step 2: 문제 생성")
                st.write("**문제에 포함할 문제 유형을 선택하세요:**")
                st.caption("📌 질문 유형 설명")
                cols = st.columns(len(QUESTION_TYPES_INFO))
                for i, (qtype, description) in enumerate(QUESTION_TYPES_INFO.items()):
                    with cols[i % len(cols)]:
                        st.caption(f"**{qtype}**\n{description}")
                selected_types = st.multiselect(
                    "문제 유형 선택",
                    list(QUESTION_TYPES_INFO.keys()),
                    default=list(QUESTION_TYPES_INFO.keys())[:3],
                    key="teacher_question_types_select",
                    label_visibility="collapsed"
                )
                st.session_state.selected_question_types = selected_types if selected_types else list(QUESTION_TYPES_INFO.keys())[:3]
                st.write("")
                col_generate, col_space2 = st.columns([1, 3])
                with col_generate:
                    if st.button("🤖 문제 생성하기", use_container_width=True, type="primary", key="teacher_generate_quiz_btn"):
                        if not st.session_state.selected_question_types:
                            st.error("❌ 최소 1개 이상의 문제 유형을 선택해주세요")
                        else:
                            with st.spinner("🤖 AI가 문제를 생성 중입니다..."):
                                try:
                                    api_key = st.session_state.openai_api_key
                                    quiz_data = generate_quiz_with_openai(
                                        api_key=api_key,
                                        passage=st.session_state.current_passage,
                                        question_types=st.session_state.selected_question_types
                                    )
                                    st.session_state.generated_quiz = quiz_data
                                    st.success("✅ 문제 생성 완료!")
                                except Exception as e:
                                    st.error(f"❌ 오류 발생: {str(e)}")
                if "generated_quiz" in st.session_state and st.session_state.generated_quiz:
                    st.divider()
                    st.info("✅ **생성된 문제 미리보기**")
                    quiz_data = st.session_state.generated_quiz
                    for i, question in enumerate(quiz_data.get("questions", []), 1):
                        st.write(f"**문제 {i}:** {question.get('question_text', '')}")
                        if "options" in question:
                            for j, option in enumerate(question['options'], 1):
                                st.write(f"  {chr(64+j)}. {option}")
                        if "explanation" in question:
                            st.caption(f"💡 해설: {question['explanation']}")
                        st.write("")
                    col_save, col_discard = st.columns(2)
                    with col_save:
                        if st.button("💾 저장하기", use_container_width=True, type="primary", key="teacher_save_quiz_btn"):
                            try:
                                save_quiz_to_firestore(
                                    textbook_name=st.session_state.selected_textbook,
                                    chapter=st.session_state.selected_chapter,
                                    difficulty=st.session_state.selected_passage_difficulty,
                                    question_types=st.session_state.selected_question_types,
                                    original_passage=TEXTBOOKS[st.session_state.selected_textbook][st.session_state.selected_chapter]["original_passage"],
                                    rewritten_passage=st.session_state.current_passage,
                                    questions=quiz_data.get("questions", [])
                                )
                                st.success("✅ 퀴즈가 성공적으로 저장되었습니다!")
                                st.session_state.step1_completed = False
                                st.session_state.current_passage = ""
                                st.session_state.generated_quiz = None
                            except Exception as e:
                                st.error(f"❌ 저장 오류: {str(e)}")
                    with col_discard:
                        if st.button("🗑️ 초기화", use_container_width=True, key="teacher_reset_quiz_btn"):
                            st.session_state.step1_completed = False
                            st.session_state.current_passage = ""
                            st.session_state.generated_quiz = None
                            st.rerun()
    with tab2:
        st.subheader("2. 학생 결과 대시보드")
        results = get_all_results()
        import pandas as pd
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df)
            st.bar_chart(df['score'])
        else:
            st.info("아직 제출된 결과가 없습니다.")

# 진입 분기
if st.session_state.main_mode is None:
    show_entry_buttons()
    st.stop()
elif st.session_state.main_mode == "teacher":
    if not st.session_state.teacher_logged_in:
        show_teacher_login()
        st.stop()
    else:
        show_teacher_dashboard()
        st.stop()
elif st.session_state.main_mode == "student":
    pass  # 아래 기존 학생/선생님 분기 코드로 진행



# ============================================================================
# OPENAI 초기화 (캐시됨 - 한 번만 실행)
# ============================================================================
@st.cache_resource
def get_openai_api_key():
    """st.secrets 또는 환경 변수에서 OpenAI API 키 가져오기 (캐시됨)"""
    try:
        # st.secrets에서 먼저 API 키를 가져오고, 없으면 환경 변수 사용
        api_key = st.secrets.get("OPENAI_API_KEY") if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OpenAI API 키를 찾을 수 없습니다! .streamlit/secrets.toml 파일에 OPENAI_API_KEY를 설정해주세요")
        
        # API 키 형식 확인 (sk-로 시작해야 함)
        if not api_key.startswith("sk-"):
            raise ValueError(f"OpenAI API 키 형식이 올바르지 않습니다! API 키는 'sk-'로 시작해야 합니다 (현재: {api_key[:10]}...)")
        
        return api_key
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ {error_msg}")
        st.stop()

# ============================================================================
# FIRESTORE 데이터베이스 함수
# ============================================================================
def save_quiz_to_firestore(textbook_name: str, chapter: str, difficulty: str, question_types: list, 
                           original_passage: str, rewritten_passage: str, questions: list):
    """생성된 퀴즈를 Firestore에 저장"""
    try:
        db = firestore.client()
        quiz_id = str(uuid4())
        quiz_data = {
            "id": quiz_id,
            "textbook_name": textbook_name,
            "chapter": chapter,
            "difficulty": difficulty,
            "question_types": question_types,
            "original_passage": original_passage,
            "rewritten_passage": rewritten_passage,
            "questions": questions,
            "created_at": datetime.now()
        }
        db.collection("quizzes").document(quiz_id).set(quiz_data)
        return quiz_id
    except Exception as e:
        st.error(f"❌ 퀴즈 저장 오류: {str(e)}")
        return None

def get_latest_quiz():
    """Firestore에서 최신 퀴즈 조회"""
    try:
        db = firestore.client()
        docs = db.collection("quizzes").order_by("created_at", direction=firestore.Query.DESCENDING).limit(1).stream()
        
        quiz_list = [doc.to_dict() for doc in docs]
        return quiz_list[0] if quiz_list else None
    except Exception as e:
        st.error(f"❌ 퀴즈 조회 오류: {str(e)}")
        return None

def save_result_to_firestore(quiz_id: str, student_name: str, score: int, total_questions: int):
    """학생 결과를 Firestore results 컬렉션에 저장"""
    try:
        db = firestore.client()
        result_id = str(uuid4())
        result_data = {
            "id": result_id,
            "quiz_id": quiz_id,
            "student_name": student_name,
            "score": score,
            "total_questions": total_questions,
            "timestamp": datetime.now()
        }
        db.collection("results").document(result_id).set(result_data)
        return result_id
    except Exception as e:
        st.error(f"❌ 결과 저장 오류: {str(e)}")
        return None


# ============================================================================
# 지문 재작성 함수 (Step 1)
# ============================================================================
def rewrite_passage_with_openai(api_key: str, original_passage: str, difficulty: str):
    """지문을 선택된 난이도 수준으로 재작성"""
    try:
        # "보통 (Original)"이면 원본 반환 (API 호출 없음)
        if difficulty == "보통 (Original)":
            return original_passage
        
        difficulty_map = {
            "쉬움 (Easy)": "easy (초등학교 수준의 단어와 간단한 문장 사용, Lexile 600-800)",
            "어려움 (Hard)": "hard (대학 수준의 어휘와 복잡한 문장 구조, Lexile 1200+)"
        }
        
        difficulty_level = difficulty_map.get(difficulty, "original")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""당신은 영어 교육 전문가입니다. 다음 작업을 수행하세요:

원본 지문:
{original_passage}

작업:
주어진 지문을 {difficulty_level} 수준으로 재작성하세요.
- 주요 내용과 의미는 유지하세요
- 단어와 문장 구조만 변경하세요
- 재작성된 지문의 길이는 200-350단어 정도여야 합니다

재작성된 지문만 반환하세요 (다른 설명 없음)."""
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "당신은 영어 교육 전문가로서 텍스트 난이도를 조정하는 데 능숙합니다."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 800
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" not in result:
            st.error(f"❌ OpenAI API 오류: {result.get('error', {}).get('message', '알 수 없는 오류')}")
            return None
        
        rewritten_text = result["choices"][0]["message"]["content"].strip()
        return rewritten_text
            
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.json() if hasattr(e.response, 'json') else str(e)
        st.error(f"❌ OpenAI API 오류: {error_detail}")
        return None
    except Exception as e:
        st.error(f"❌ 지문 변환 오류: {str(e)}")
        return None

# ============================================================================
# AI 퀴즈 생성 함수 (Step 2)
# ============================================================================
def generate_quiz_with_openai(api_key: str, passage: str, question_types: list):
    """Step 2: 주어진 지문을 기반으로 퀴즈 생성"""
    try:
        question_types_str = ", ".join(question_types)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""당신은 한국 고등학교 영어 교사입니다. 다음 작업을 수행하세요:

지문:
{passage}

작업:
위 지문을 기반으로 다음 질문 유형으로 정확히 {len(question_types)}개의 객관식 문제를 생성하세요:
- 요청된 질문 유형: {question_types_str}

질문 유형 설명:
- 주제 추론: 지문의 주제나 주요 내용을 파악하는 문제
- 제목 추론: 지문에 가장 적합한 제목을 선택하는 문제
- 빈칸 추론: 지문의 빈칸에 들어갈 가장 적절한 단어/구를 선택하는 문제
- 요지 추론: 지문의 요점이나 결론을 파악하는 문제
- 문단 요약: 특정 문단의 내용을 가장 잘 요약한 것을 선택하는 문제

다음의 정확한 JSON 형식으로 응답하세요 (다른 텍스트는 없음):
{{
    "questions": [
        {{
            "question_text": "문제 텍스트",
            "type": "질문 유형",
            "options": ["선택지 1", "선택지 2", "선택지 3", "선택지 4"],
            "correct_answer": 0
        }}
    ]
}}

주의:
- 각 문제는 정확히 4개의 선택지를 가져야 합니다
- correct_answer는 정답의 인덱스 (0-3)입니다
- 빈칸 추론 문제의 경우, 지문의 원문을 참고하여 지문 내에서 빈칸을 명시하지 마세요
- JSON만 반환하세요"""
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "당신은 한국 고등학교 영어 교사로서 지문 기반 퀴즈를 만드는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" not in result:
            st.error(f"❌ OpenAI API 오류: {result.get('error', {}).get('message', '알 수 없는 오류')}")
            return None
        
        response_text = result["choices"][0]["message"]["content"].strip()
        
        # JSON 추출
        try:
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            quiz_data = json.loads(response_text)
            return quiz_data
        except json.JSONDecodeError:
            st.error("❌ OpenAI 응답을 JSON으로 파싱하는 데 실패했습니다")
            st.write("수신된 응답:", response_text[:300])
            return None
            
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.json() if hasattr(e.response, 'json') else str(e)
        st.error(f"❌ OpenAI API 오류: {error_detail}")
        return None
    except Exception as e:
        st.error(f"❌ 퀴즈 생성 오류: {str(e)}")
        return None

# ============================================================================
# STREAMLIT 세션 상태 초기화
# ============================================================================
if "firebase_initialized" not in st.session_state:
    st.session_state.firebase_initialized = False

if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = None

if "mode" not in st.session_state:
    st.session_state.mode = "선생님 모드"

if "selected_textbook" not in st.session_state:
    st.session_state.selected_textbook = None

if "selected_chapter" not in st.session_state:
    st.session_state.selected_chapter = None

if "selected_passage_difficulty" not in st.session_state:
    st.session_state.selected_passage_difficulty = None

if "current_passage" not in st.session_state:
    st.session_state.current_passage = None

if "step1_completed" not in st.session_state:
    st.session_state.step1_completed = False

if "selected_question_types" not in st.session_state:
    st.session_state.selected_question_types = []

if "quiz_generated" not in st.session_state:
    st.session_state.quiz_generated = None

if "student_name" not in st.session_state:
    st.session_state.student_name = ""

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

# ============================================================================
# OPENAI 초기화
# ============================================================================
if not st.session_state.openai_api_key:
    st.session_state.openai_api_key = get_openai_api_key()

# =====================

# 학생 모드 함수
def run_student_mode():
    st.title("📚 교과서 기반 영어 퀴즈 생성기")
    st.write("한국 고등학교 교과서를 기반으로 AI가 생성한 맞춤형 영어 퀴즈")
    st.header("👨‍🎓 학생 퀴즈 포털")
    # 학생 로그인
    student_name = st.text_input(
        "학생 이름",
        value=st.session_state.student_name,
        placeholder="학생 이름을 입력하세요"
    )
    st.session_state.student_name = student_name
    if not student_name.strip():
        st.warning("⚠️ 계속하려면 이름을 입력해주세요")
        return
    # 최신 퀴즈 로드
    st.subheader("📖 퀴즈 풀기")
    if st.button("📥 최신 퀴즈 불러오기", use_container_width=True, type="primary"):
        with st.spinner("퀴즈 로드 중..."):
            quiz = get_latest_quiz()
            if quiz:
                st.session_state.current_quiz = quiz
                st.success("✅ 퀴즈가 성공적으로 로드되었습니다!")
            else:
                st.error("❌ 사용 가능한 퀴즈가 없습니다")
    # 퀴즈 표시 및 풀기
    if "current_quiz" in st.session_state and st.session_state.current_quiz:
        quiz = st.session_state.current_quiz
        st.info(f"📚 **{quiz.get('textbook_name', '알 수 없음')}** - {quiz.get('chapter', '알 수 없음')} | 난이도: {quiz.get('difficulty', '')}")
        st.subheader("지문")
        st.write(quiz.get("rewritten_passage", ""))
        st.subheader("문제")
        with st.form(key="quiz_form"):
            answers = {}
            questions = quiz.get("questions", [])
            for i, q in enumerate(questions):
                st.write(f"**문제 {i+1}** [{q.get('type', '')}]")
                st.write(q.get('question_text', ''))
                options = q.get("options", [])
                selected = st.radio(
                    label=f"문제 {i+1}의 답변을 선택하세요",
                    options=list(range(len(options))),
                    format_func=lambda x: f"{chr(64+x)}. {options[x]}",
                    key=f"q_{i}",
                    label_visibility="collapsed"
                )
                answers[i] = selected
                st.divider()
            submit_button = st.form_submit_button(
                "✅ 퀴즈 제출",
                use_container_width=True,
                type="primary"
            )
            if submit_button:
                score = 0
                for i, q in enumerate(questions):
                    if answers.get(i) == q.get("correct_answer"):
                        score += 1
                result_id = save_result_to_firestore(
                    quiz.get("id", "unknown"),
                    student_name,
                    score,
                    len(questions)
                )
                if result_id:
                    st.session_state.quiz_answers = answers
                    st.session_state.quiz_submitted = True
        if st.session_state.get("quiz_submitted", False):
            st.subheader("📊 당신의 결과")
            questions = quiz.get("questions", [])
            answers = st.session_state.quiz_answers
            score = sum(1 for i, q in enumerate(questions) if answers.get(i) == q.get("correct_answer"))
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("점수", f"{score}/{len(questions)}")
            with col2:
                st.metric("정답 수", score)
            with col3:
                percentage = (score / len(questions) * 100) if len(questions) > 0 else 0
                st.metric("정답률", f"{percentage:.1f}%")
            st.write("")
            for i, q in enumerate(questions):
                user_answer = answers.get(i)
                correct = user_answer == q.get("correct_answer")
                st.write(f"**문제 {i+1}**: {'🟢 정답' if correct else '🔴 오답'}")
                st.write(f"내 답: {chr(65+user_answer)} | 정답: {chr(65+q.get('correct_answer',0))}")
                st.write("")

# =====================
# 학생 모드 진입 분기
# =====================
if st.session_state.main_mode == "student":
    run_student_mode()

    # (중복 학생 모드 코드 완전 삭제)
st.write("**문제에 포함할 문제 유형을 선택하세요:**")
st.caption("📌 질문 유형 설명")
cols = st.columns(len(QUESTION_TYPES_INFO))
for i, (qtype, description) in enumerate(QUESTION_TYPES_INFO.items()):
    with cols[i % len(cols)]:
        st.caption(f"**{qtype}**\n{description}")

selected_types = st.multiselect(
    "문제 유형 선택",
    list(QUESTION_TYPES_INFO.keys()),
    default=list(QUESTION_TYPES_INFO.keys())[:3],
    key="question_types_select",
    label_visibility="collapsed"
)
st.session_state.selected_question_types = selected_types if selected_types else list(QUESTION_TYPES_INFO.keys())[:3]

# Step 2: 문제 생성 버튼
st.write("")
col_generate, col_space2 = st.columns([1, 3])
with col_generate:
    if st.button("🤖 문제 생성하기", use_container_width=True, type="primary", key="generate_quiz_btn"):
        if not st.session_state.selected_question_types:
            st.error("❌ 최소 1개 이상의 문제 유형을 선택해주세요")
        else:
            with st.spinner("🤖 AI가 문제를 생성 중입니다..."):
                try:
                    api_key = st.session_state.openai_api_key
                    quiz_data = generate_quiz_with_openai(
                        api_key=api_key,
                        passage=st.session_state.current_passage,
                        question_types=st.session_state.selected_question_types
                    )
                    st.session_state.generated_quiz = quiz_data
                    st.success("✅ 문제 생성 완료!")
                except Exception as e:
                    st.error(f"❌ 오류 발생: {str(e)}")

# 생성된 문제 표시 및 저장
if "generated_quiz" in st.session_state and st.session_state.generated_quiz:
    st.divider()
    st.info("✅ **생성된 문제 미리보기**")
    quiz_data = st.session_state.generated_quiz
    for i, question in enumerate(quiz_data.get("questions", []), 1):
        st.write(f"**문제 {i}:** {question.get('question_text', '')}")
        if "options" in question:
            for j, option in enumerate(question['options'], 1):
                st.write(f"  {chr(64+j)}. {option}")
        if "explanation" in question:
            st.caption(f"💡 해설: {question['explanation']}")
        st.write("")
    # 저장 버튼
    col_save, col_discard = st.columns(2)
    with col_save:
        if st.button("💾 저장하기", use_container_width=True, type="primary", key="save_quiz_btn"):
            try:
                save_quiz_to_firestore(
                    textbook_name=st.session_state.selected_textbook,
                    chapter=st.session_state.selected_chapter,
                    difficulty=st.session_state.selected_passage_difficulty,
                    question_types=st.session_state.selected_question_types,
                    original_passage=TEXTBOOKS[st.session_state.selected_textbook][st.session_state.selected_chapter]["original_passage"],
                    rewritten_passage=st.session_state.current_passage,
                    questions=quiz_data.get("questions", [])
                )
                st.success("✅ 퀴즈가 성공적으로 저장되었습니다!")
                # 저장 후 상태 초기화
                st.session_state.step1_completed = False
                st.session_state.current_passage = ""
                st.session_state.generated_quiz = None
            except Exception as e:
                st.error(f"❌ 저장 오류: {str(e)}")
    with col_discard:
        if st.button("🗑️ 초기화", use_container_width=True, key="reset_quiz_btn"):
            st.session_state.step1_completed = False
            st.session_state.current_passage = ""
            st.session_state.generated_quiz = None
            st.rerun()

    
    # 학생 결과 대시보드
    st.divider()
    st.subheader("📊 학생 결과 대시보드")
    
    if st.button("📈 결과 불러오기", use_container_width=True):
        results = get_all_results()
        
        if results:
            st.write(f"총 제출 현황: **{len(results)}명**")
            
            # 요약 테이블
            summary_data = []
            for result in results:
                summary_data.append({
                    "학생 이름": result.get("student_name", "알 수 없음"),
                    "점수": result.get("score", 0),
                    "전체 문제": result.get("total_questions", 0),
                    "정답률": f"{(result.get('score', 0) / max(result.get('total_questions', 1), 1) * 100):.1f}%",
                    "제출 시간": result.get("timestamp", "")
                })
            
            st.dataframe(summary_data, use_container_width=True)
            
            # 통계
            col1, col2, col3, col4 = st.columns(4)
            
            total_submissions = len(results)
            avg_score = sum(r.get("score", 0) for r in results) / max(total_submissions, 1)
            max_score = max((r.get("score", 0) for r in results), default=0)
            min_score = min((r.get("score", 0) for r in results), default=0)
            
            with col1:
                st.metric("총 제출 수", total_submissions)
            with col2:
                st.metric("평균 점수", f"{avg_score:.1f}")
            with col3:
                st.metric("최고 점수", max_score)
            with col4:
                st.metric("최저 점수", min_score)
        else:
            st.info("ℹ️ 아직 제출된 결과가 없습니다")

    # (함수 밖 학생 모드 코드 완전 삭제)

# ============================================================================
# 푸터
# ============================================================================
st.divider()
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8em;'>"
    "교과서 기반 영어 퀴즈 생성기 | Streamlit & Firebase 기반"
    "</p>",
    unsafe_allow_html=True
)

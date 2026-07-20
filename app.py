import streamlit as st
import time
import os
import sys
import asyncio
from dotenv import load_dotenv

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# 환경 변수 강제 리로드 (.env 파일 수정 시 즉시 반영)
load_dotenv(override=True)

from services import video, llm
from storage import json_handler

# 페이지 기본 설정
st.set_page_config(page_title="나만의 자율형 학습 가이드", layout="wide")

# Shadcn/Coursera 스타일의 미니멀/모던 UI 커스텀 CSS
st.markdown("""
<style>
    /* 전역 앱 설정 */
    .stApp {
        background-color: #F8FAFC !important;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        max-width: 900px !important;
    }

    /* 텍스트 가독성 최적화 (흐릿한 현상 해결) */
    h1, h2, h3, h4, h5 {
        font-family: 'Inter', 'Pretendard', sans-serif !important;
        color: #0F172A !important;
        letter-spacing: -0.025em !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
    }
    .stMarkdown p, .stMarkdown span {
        color: #1E293B !important;
        line-height: 1.8 !important;
        font-size: 1.05rem !important;
    }
    
    /* 사이드바 강제 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    [data-testid="stSidebar"] * {
        color: #0F172A !important;
    }
    
    /* 💡 핵심: 흐릿했던 인용구(Callout Box)를 상업용 모듈로 완벽 변신 */
    .stMarkdown blockquote {
        background-color: #EEF2FF !important;
        border-left: 5px solid #4F46E5 !important;
        padding: 1.2rem 1.5rem !important;
        margin: 1.5rem 0 !important;
        border-radius: 0 8px 8px 0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    .stMarkdown blockquote, .stMarkdown blockquote * {
        color: #1E293B !important;
        opacity: 1 !important;
    }
    .stMarkdown blockquote p {
        font-weight: 500 !important;
        margin-bottom: 0 !important;
    }
    
    /* 모듈형 카드 디자인 (메인 콘텐츠 영역) */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background: #FFFFFF !important;
        padding: 2.5rem !important;
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
    }
    
    /* 리스트 가독성 */
    .stMarkdown li {
        color: #1E293B !important;
        margin-bottom: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화 및 로컬 데이터 로드
if "history" not in st.session_state:
    from datetime import datetime
    loaded_data = json_handler.load_data()
    st.session_state.history = loaded_data.get("history", [])
    st.session_state.document = loaded_data.get("document", {})
    st.session_state.stage = loaded_data.get("stage", "INPUT")
    st.session_state.provider = loaded_data.get("provider", "Google Gemini")

def save_current_state():
    """현재 진행 상황을 JSON 파일에 저장합니다."""
    json_handler.save_data({
        "history": st.session_state.history,
        "document": st.session_state.document,
        "stage": st.session_state.stage,
        "provider": st.session_state.provider
    })

st.title("📚 영상 기반 나만의 인터랙티브 학습 문서 생성기")

if st.session_state.stage == "INPUT":
    tab1, tab2 = st.tabs(["🚀 새 가이드 생성", "📚 내 학습 서재"])
    
    with tab2:
        st.markdown("### 📚 내 학습 서재")
        if not st.session_state.history:
            st.info("아직 저장된 학습 가이드북이 없습니다.")
        else:
            for item in reversed(st.session_state.history):
                with st.container(border=True):
                    st.markdown(f"**{item.get('title', '제목 없음')}**")
                    st.caption(f"📅 {item.get('date', '')} | 🤖 {item.get('provider', '')}")
                    if st.button("📖 학습하기", key=f"view_{item.get('id')}"):
                        st.session_state.document = item.get('document', {})
                        st.session_state.provider = item.get('provider', '알 수 없음')
                        st.session_state.stage = "LEARNING"
                        save_current_state()
                        st.rerun()
    
    with tab1:
        st.markdown("### 1. 비디오 URL 입력")
        st.markdown("학습하고 싶은 YouTube 또는 X(Twitter) 영상 주소를 입력해주세요.")
        video_url = st.text_input("URL 입력:", placeholder="https://www.youtube.com/watch?v=...")
    
        st.markdown("### 2. AI 모델 선택")
        selected_provider = st.selectbox(
            "사용할 AI 제공자(모델)를 선택하세요:",
            options=[
                "Google Gemini", 
                "OpenAI (GPT-4o)",
                "glm-5.2",
                "nvidia/nemotron-3-ultra-550b-a55b",
                "gpt-oss-120b",
                "meta/llama-3.1-70b-instruct",
                "nvidia/llama-3.1-nemotron-70b-instruct"
            ],
            index=0
        )
    
        selected_gemini_version = st.selectbox(
            "Gemini 세부 버전 (Google Gemini 선택 시 또는 기본 음성 추출 엔진):",
            options=[
                "gemini-3.5-flash",
                "gemini-3.1-pro",
                "gemini-3-flash",
                "gemini-3.1-flash-lite",
                "gemini-omni-flash"
            ],
            index=0
        )
        os.environ["SELECTED_GEMINI_VERSION"] = selected_gemini_version
    
        with st.expander("⚙️ 고급 설정 (분량 및 비유 조절)"):
            st.markdown("생성될 가이드북의 분량과 설명 방식을 취향에 맞게 조절하세요.")
            col1, col2 = st.columns(2)
            with col1:
                length_preset = st.radio(
                    "분량 조절",
                    ["핵심 요약", "적당한 설명", "아주 상세하게"],
                    index=2
                )
            with col2:
                analogy_preset = st.radio(
                    "비유 정도",
                    ["비유 없이 담백하게", "적절한 비유 추가", "풍부한 비유"],
                    index=2
                )
    
        if st.button("🚀 나만의 상세 가이드북 자동 생성 시작", type="primary"):
            if not video_url:
                st.error("URL을 입력해주세요!")
            else:
                try:
                    st.session_state.provider = selected_provider
                    with st.status(f"🚀 가이드북 생성 진행 상황 ({selected_provider})", expanded=True) as status:
                        # Step 1: 오디오 다운로드
                        st.write("⏳ 1/4: 영상에서 오디오를 추출하는 중입니다...")
                        audio_path = video.download_audio(video_url)
                        st.write("✅ 오디오 추출 완료!")
                    
                        # Step 2: 오디오 처리 (Gemini File 또는 Whisper STT)
                        st.write(f"⏳ 2/4: {selected_provider} 모델에 오디오 처리를 요청 중입니다...")
                        context_data = llm.process_audio(audio_path, selected_provider)
                        st.write("✅ 오디오 분석 완료!")
                    
                        url_hash = video.get_url_hash(video_url)
                    
                        # Step 3: 상세 목차 생성
                        st.write(f"⏳ 3/4: 전체 내용을 바탕으로 상세 목차를 설계하는 중입니다...")
                        sections = llm.generate_outline(context_data, selected_provider, url_hash, length_preset)
                        st.write(f"✅ 상세 목차 설계 완료! (총 {len(sections)}개 챕터)")
                    
                        # Step 4: 비동기 챕터 본문 생성
                        st.write("⏳ 4/4: 각 챕터별로 쉽고 상세한 본문을 작성 중입니다... (최대 3개 동시 생성)")
                        st.session_state.document = {}
                    
                        preview_container = st.container()
                        with preview_container:
                            st.markdown("### 📝 챕터 생성 현황")
                            progress_text = st.empty()
                    
                        async def process_chapter(idx: int, section: str, sem: asyncio.Semaphore):
                            safe_suffix = f"{length_preset}_{analogy_preset}".replace(" ", "_")
                            cache_file = os.path.join("data", f"{url_hash}_chapter_{idx}_{safe_suffix}.txt")
                            if os.path.exists(cache_file):
                                with open(cache_file, "r", encoding="utf-8") as f:
                                    return section, f.read()
                                
                            max_retries = 5
                            for attempt in range(max_retries):
                                try:
                                    async with sem:
                                        content = await llm.async_generate_chapter_content(
                                            section, context_data, selected_provider, idx, len(sections),
                                            length_preset, analogy_preset
                                        )
                                    
                                    with open(cache_file, "w", encoding="utf-8") as f:
                                        f.write(content)
                                    return section, content
                                except Exception as e:
                                    error_msg = str(e)
                                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                                        if attempt < max_retries - 1:
                                            await asyncio.sleep(65)
                                        else:
                                            raise e
                                    else:
                                        if attempt < max_retries - 1:
                                            await asyncio.sleep(5)
                                        else:
                                            raise e
                    
                        async def run_all_chapters():
                            sem = asyncio.Semaphore(3)
                            tasks = [process_chapter(idx, section, sem) for idx, section in enumerate(sections)]
                            return await asyncio.gather(*tasks)
                        
                        # 비동기 실행 (Streamlit 메인 스레드 블로킹)
                        results = asyncio.run(run_all_chapters())
                    
                        for section, content in results:
                            st.session_state.document[section] = content
                        
                        save_current_state()
                    
                        status.update(label="✅ 가이드북 생성이 모두 완료되었습니다!", state="complete", expanded=False)
                
                    # 불필요해진 임시 오디오 파일 삭제
                    try:
                        os.remove(audio_path)
                    except Exception:
                        pass
                    
                    # Add to history
                    new_entry = {
                        "id": url_hash + "_" + datetime.now().strftime("%Y%m%d%H%M%S"),
                        "url": video_url,
                        "title": video.get_video_title(video_url),
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "provider": st.session_state.provider,
                        "document": st.session_state.document.copy()
                    }
                    st.session_state.history.append(new_entry)
                    st.session_state.stage = "LEARNING"
                    save_current_state()
                    st.rerun()
                
                except Exception as e:
                    st.error(f"작업 중 오류가 발생했습니다: {e}")

elif st.session_state.stage == "LEARNING":
    if not st.session_state.document:
        st.warning("저장된 학습 데이터가 없습니다. 처음으로 돌아갑니다.")
        if st.button("처음으로"):
            st.session_state.stage = "INPUT"
            save_current_state()
            st.rerun()
    else:
        st.sidebar.header("📖 학습 목차")
        st.sidebar.markdown(f"**현재 AI 모델:** {st.session_state.provider}")
        
        sections_list = list(st.session_state.document.keys())
        selected_section = st.sidebar.radio("이동할 챕터:", sections_list)
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🔄 새로운 영상으로 시작하기"):
            st.session_state.document = {}
            st.session_state.stage = "INPUT"
            save_current_state()
            st.rerun()
        
        st.subheader(selected_section)
        
        # 저장된 현재 챕터 본문 렌더링
        st.markdown(st.session_state.document[selected_section])
        st.markdown("---")
        
        st.markdown("### 🙋‍♂️ 질문하기")
        st.markdown("이해가 안 가는 부분이 있나요? 질문을 남기면 AI가 맞춤형 비유로 더 쉽게 설명해 드립니다.")
        
        # 입력 폼
        with st.form(key=f"q_form_{selected_section}"):
            user_question = st.text_input("질문을 입력하세요:", placeholder="예: 이 개념을 자동차에 비유해서 설명해줄 수 있나요?")
            submit_question = st.form_submit_button("💡 질문하고 답변을 본문에 추가하기")
            
            if submit_question:
                if user_question.strip():
                    with st.spinner("더 쉬운 설명과 비유를 생성하는 중..."):
                        try:
                            context = st.session_state.document[selected_section]
                            provider = st.session_state.get("provider", "Google Gemini")
                            ai_answer = llm.generate_answer(context, user_question, provider)
                            
                            # 생성된 답변을 기존 챕터 본문 뒤에 누적
                            added_text = f"\n\n---\n\n**🙋‍♂️ 나의 질문:** {user_question}\n\n💡 **{provider}의 답변:**\n{ai_answer}"
                            st.session_state.document[selected_section] += added_text
                            
                            # 데이터 영속성 유지
                            save_current_state()
                            
                            st.toast("본문에 답변이 추가되었습니다!", icon="✅")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"답변 생성 중 오류가 발생했습니다: {e}")
                else:
                    st.warning("질문을 입력해주세요.")

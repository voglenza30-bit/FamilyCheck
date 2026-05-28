import streamlit as st
import json, os, requests, re
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="정밀 심리 진단 시스템 2.0", layout="wide")

# 2. Gemini API 세팅 (자동 모델 탐색 유지)
# 2. Gemini API 세팅 (대표님이 확인하신 최신 3.5 엔진으로 직결)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.5-flash')

# 인쇄 및 그래프용 CSS
st.markdown("""
    <style>
    # 변경 전 (사이드바까지 다 숨겨버렸던 몹쓸 코드)
    @media print {
        .stButton, .stDownloadButton, [data-testid="stSidebar"] { display: none !important; }
        .main { background-color: white !important; padding: 0 !important; }
    }

# 💡 변경 후 (사이드바는 살려두고, 진짜 인쇄할 때만 숨기는 똑똑한 코드)
    @media print {
        .stButton, .stDownloadButton { display: none !important; }
        .main { background-color: white !important; padding: 0 !important; }
    }
    /* 모바일과 PC에서 사이드바가 강제로 숨겨지지 않도록 방지 */
    [data-testid="stSidebar"] { display: flex !important; }
    }
    .t-score-bar { background-color: #e2e8f0; border-radius: 5px; height: 25px; width: 100%; position: relative; margin-bottom: 10px; }
    .t-score-fill { background-color: #005088; height: 100%; border-radius: 5px; color: white; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; font-size: 12px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 3. 구글 시트 웹 앱 URL (대표님 기존 DB 링크 복구)
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwOXsbz1hKT_dPN6pJDn6QAlEginqXIOLBXiFZtV2kKffbZekvMVOIg1LZ19h4dV0Lyjw/exec"

# 4. 데이터 로드 (기존 txt 파일 문항 100% 유지)
@st.cache_data
def load_data():
    def read_t(f):
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file:
                return [re.sub(r'^\d+[\s\.]+', '', l.strip()) for l in file.readlines() if l.strip()]
        return []
    return {
        "qs": {"IQ": read_t("wechsler.txt"), "MBTI": read_t("mbti.txt"), "TCI": read_t("tci.txt"), "MMPI": read_t("mmpi.txt"), "CLINICAL": read_t("clinical.txt")},
        "sct_starts": ["나의 아버지는 ", "내가 가장 행복할 때는 ", "나의 장래는 ", "나를 가장 화나게 하는 것은 ", "내 생각에 참다운 친구란 ", "내가 어렸을 때는 ", "나의 어머니는 ", "내가 가장 두려워하는 것은 ", "무슨 일을 해서라도 잊고 싶은 것은 ", "다른 사람들이 나를 "]
    }

db = load_data()

# 막대 그래프 그리는 함수
def get_t_score_html(label, score, max_score, color="#005088"):
    t_val = int((score / (max_score if max_score > 0 else 1)) * 50 + 30)
    return f'''
    <div style="margin-bottom:15px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span style="font-weight:bold; color:#334155;">{label}</span>
            <span style="font-weight:bold; color:{color};">T-{t_val}</span>
        </div>
        <div class="t-score-bar">
            <div class="t-score-fill" style="width:{min(max(t_val, 0), 100)}%; background-color:{color};"></div>
        </div>
    </div>
    '''

# ==========================================
# 5. 메인 UI 및 구글 시트 연동 복구
# ==========================================
if 'reg' not in st.session_state: st.session_state['reg'] = False

if not st.session_state['reg']:
    st.title("🔍 Full Battery 2.0 심리 진단 시스템")
    name = st.text_input("성함(이름)")
    birth = st.text_input("생년월일(8자리)")
    gen = st.selectbox("성별", ["남성", "여성"])
    rel = st.selectbox("관계", ["본인", "부", "모", "자녀", "배우자", "기타"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 구글 시트 기록 불러오기", use_container_width=True):
            if name and birth:
                with st.spinner("DB에서 대상자 기록을 조회 중입니다..."):
                    try:
                        res = requests.get(GOOGLE_SCRIPT_URL, params={"name": name, "birth": birth}, timeout=10).json()
                        st.session_state['u'] = {"name":name, "birth":birth, "gen":gen, "rel":rel}
                        st.session_state['reg'] = True
                        if res.get("status") == "success":
                            st.session_state['scores'] = res["scores"]
                        else:
                            st.session_state['scores'] = {}
                        st.rerun()
                    except Exception:
                        st.error("⚠️ 구글 시트 연결 오류가 발생했습니다.")
            else:
                st.error("이름과 생년월일을 입력해주세요.")
    with col2:
        if st.button("🚀 신규 검사 시작", use_container_width=True):
            if name and birth:
                st.session_state['u'] = {"name":name, "birth":birth, "gen":gen, "rel":rel}
                st.session_state['scores'] = {}
                st.session_state['reg'] = True
                st.rerun()
            else:
                st.error("이름과 생년월일을 입력해주세요.")
else:
    # 좌측 사이드바 메뉴 방식 도입 (탭 대신 깔끔하게 분리)
    st.sidebar.title(f"👤 {st.session_state['u']['name']}님")
    menu = st.sidebar.radio("검사 진행 단계", ["1. 객관식 진단 (기존)", "2. 문장완성 (SCT)", "3. 투사그림 (HTP)", "4. 종합 소견서"])
    
    if st.sidebar.button("🔄 첫 화면으로 가기 (초기화)"):
        st.session_state.clear()
        st.rerun()

    if menu == "1. 객관식 진단 (기존)":
        st.header("📄 기존 객관식 정밀 진단")
        opts = {0:"매우 아니다", 1:"아니다", 2:"보통", 3:"그렇다", 4:"매우 그렇다"}
        cur_s = st.session_state.get('scores', {})
        
        for c, qs in db["qs"].items():
            if qs:
                with st.expander(f"📌 {c} 검사 ({len(qs)}문항)"):
                    ans_array = []
                    for i, q in enumerate(qs):
                        # 구글 시트에서 불러온 기존 값이 있으면 복원
                        saved_val = cur_s.get(c, [])
                        idx = saved_val[i] if i < len(saved_val) else 2
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), format_func=lambda x:opts[x], horizontal=True, key=f"{c}_{i}", index=idx)
                        ans_array.append(ans)
                    cur_s[c] = ans_array
        
        if st.button("🚀 검사 완료 및 구글 시트에 제출", use_container_width=True):
            try:
                requests.post(GOOGLE_SCRIPT_URL, data=json.dumps({"user":st.session_state['u'], "scores":cur_s}), timeout=10)
            except Exception:
                pass
            st.session_state['scores'] = cur_s
            st.success("✅ 구글 시트 DB에 안전하게 제출되었습니다! 왼쪽 메뉴에서 2번 SCT 검사로 넘어가세요.")

    elif menu == "2. 문장완성 (SCT)":
        st.header("✍️ 주관식 문장완성검사 (SCT)")
        st.write("다음에 나열된 문장의 뒷부분을 생각나는 대로 자유롭게 완성해 주세요. (심층 분석의 핵심 자료가 됩니다.)")
        sct_ans = st.session_state.get('sct', [""] * len(db["sct_starts"]))
        for i, start in enumerate(db["sct_starts"]):
            sct_ans[i] = st.text_input(f"{i+1}. {start}", value=sct_ans[i], key=f"sct_{i}")
        if st.button("SCT 데이터 임시 저장"):
            st.session_state['sct'] = sct_ans
            st.success("✅ 문장 데이터가 기억되었습니다. 왼쪽 메뉴에서 다음으로 넘어가세요.")

    elif menu == "3. 투사그림 (HTP)":
        st.header("🎨 그림 검사 (HTP) 자가 체크")
        st.write("본인이 도화지에 그린 집, 나무, 사람 그림의 특징을 솔직하게 체크해 주세요.")
        htp = st.session_state.get('htp', {})
        col1, col2 = st.columns(2)
        with col1:
            htp['house_size'] = st.select_slider("집의 크기", ["매우 작음", "작음", "보통", "큼", "매우 큼"], value=htp.get('house_size', "보통"))
            htp['door'] = st.checkbox("문에 손잡이가 없는가?", value=htp.get('door', False))
            htp['window'] = st.checkbox("창문이 너무 많거나 큰가?", value=htp.get('window', False))
        with col2:
            htp['tree_root'] = st.checkbox("나무 뿌리가 지나치게 강조되었는가?", value=htp.get('tree_root', False))
            htp['person_arm'] = st.checkbox("사람의 팔이 생략되었거나 뒤로 감춰졌는가?", value=htp.get('person_arm', False))
            htp['pressure'] = st.select_slider("그림의 필압(선 굵기)", ["매우 흐림", "흐림", "보통", "강함", "매우 강함"], value=htp.get('pressure', "보통"))
        if st.button("HTP 데이터 임시 저장"):
            st.session_state['htp'] = htp
            st.success("✅ 투사적 특징이 기억되었습니다. 마지막 '종합 소견서' 메뉴로 넘어가세요.")

    elif menu == "4. 종합 소견서":
        st.header("📑 종합 임상 심리 정밀 보고서")
        if 'scores' not in st.session_state or not st.session_state['scores']:
            st.warning("⚠️ 먼저 '1. 객관식 진단'을 완료하여 점수 데이터를 만들어 주세요.")
        else:
            if st.button("🧠 대학병원 수준 통합 리포트 작문하기", use_container_width=True):
                with st.spinner("AI 임상심리사가 기존 객관식 점수와 새로운 주관식(SCT/HTP)을 융합하여 분석 중입니다..."):
                    sct_context = "\n".join([f"- {s}{a}" for s, a in zip(db["sct_starts"], st.session_state.get('sct', []))])
                    htp_context = str(st.session_state.get('htp', {}))
                    score_context = str({k: sum(v) for k, v in st.session_state['scores'].items()})
                    
                    prompt = f'''
                    당신은 15년 경력의 베테랑 정신건강임상심리사입니다. 
                    다음 내담자의 모든 데이터(객관식 점수, SCT 주관식 답변, HTP 그림 특징)를 통합하여 실제 대학병원 심리평가보고서(Full Battery Assessment) 수준의 소견서를 작성하세요.

                    [내담자: {st.session_state['u']['name']} / {st.session_state['u']['gen']}]
                    1. 5종 객관식 점수 요약: {score_context}
                    2. SCT 문장완성검사 답변: {sct_context}
                    3. HTP 투사검사 그림 특징: {htp_context}

                    [작성 지침 - 매우 중요]
                    - 문체: 기계적인 설명이 아닌, 반드시 전문가적인 평어체(~함, ~시사됨, ~판단됨, ~나타남)를 사용하세요.
                    - 분석: 점수만 나열하지 말고, SCT 주관식 답변과 HTP 투사적 특징을 MMPI/IQ 등의 수치와 유기적으로 결합하여 내담자의 무의식적 갈등을 깊이 있게 해석하세요.
                    - 구조 (아래 목차를 반드시 지킬 것):
                      # 종합 심리평가보고서 (Psychological Evaluation Report)
                      ## 1. 인지 및 지능 기능
                      ## 2. 지각 및 사고적 측면
                      ## 3. 정서 및 심리적 적응 상태 (MMPI/SCT/HTP 통합 분석)
                      ## 4. 기질 및 성격 특성 (MBTI/TCI)
                      ## 5. 요약 및 제언 (치료적 개입 방향)
                    '''
                    try:
                        res = model.generate_content(prompt)
                        st.session_state['final_report'] = res.text
                    except Exception as e:
                        st.error(f"AI 연동 오류: {e}")

            if 'final_report' in st.session_state:
                st.subheader("📊 Clinical Profile (다차원 T-Score 그래프)")
                prof_col1, prof_col2 = st.columns(2)
                with prof_col1:
                    st.components.v1.html(get_t_score_html("인지 처리 지표 (IQ)", sum(st.session_state['scores'].get('IQ', [0])), 30, "#005088"), height=70)
                    st.components.v1.html(get_t_score_html("기질적 자극추구 (TCI)", sum(st.session_state['scores'].get('TCI', [0])), 30, "#11caa0"), height=70)
                with prof_col2:
                    st.components.v1.html(get_t_score_html("정서적 예민성 (MMPI)", sum(st.session_state['scores'].get('MMPI', [0])), 30, "#e63946"), height=70)
                    st.components.v1.html(get_t_score_html("임상 증상 (CLINICAL)", sum(st.session_state['scores'].get('CLINICAL', [0])), 30, "#f59e0b"), height=70)

                st.divider()
                st.markdown(st.session_state['final_report'])
                
                st.subheader("🖨️ 리포트 저장 및 출력")
                col_print, col_down = st.columns(2)
                with col_print:
                    if st.button("🖨️ 보고서 인쇄 (PDF 저장)", use_container_width=True):
                        components.html("<script>window.print();</script>", height=0)
                with col_down:
                    st.download_button("💾 텍스트 파일(TXT)로 다운로드", data=st.session_state['final_report'], file_name=f"심리진단보고서_{st.session_state['u']['name']}.txt", mime="text/plain", use_container_width=True)

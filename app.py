import streamlit as st
import json, os, requests, re
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="정밀 심리 진단 시스템", layout="wide")

# 2. Gemini API 키 설정 및 AI 모델 준비 (404 에러 방지를 위해 latest 버전 명시)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
# 변경 전 (에러 나는 코드)
model = genai.GenerativeModel('gemini-1.5-flash')

# 💡 변경 후 (무조건 작동하는 기본 안정화 모델)
model = genai.GenerativeModel('gemini-pro')

# 사이드바 및 버튼 등 인쇄 시 불필요한 요소 숨기는 CSS
hide_elements = """
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    @media print {
        .stButton, .stDownloadButton, .stTabs [data-baseweb="tab-list"] { display: none !important; }
        .main { background-color: white !important; }
        section[data-testid="stSidebar"] { display: none !important; }
    }
    </style>
"""
st.markdown(hide_elements, unsafe_allow_html=True)

# 3. 구글 웹 앱 URL 설정
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwOXsbz1hKT_dPN6pJDn6QAlEginqXIOLBXiFZtV2kKffbZekvMVOIg1LZ19h4dV0Lyjw/exec"

@st.cache_data
def load_data():
    def read_t(f):
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file:
                return [re.sub(r'^\d+[\s\.]+', '', l.strip()) for l in file.readlines() if l.strip()]
        return []
    return {
        "qs": {"IQ": read_t("wechsler.txt"), "MBTI": read_t("mbti.txt"), "TCI": read_t("tci.txt"), "MMPI": read_t("mmpi.txt"), "CLINICAL": read_t("clinical.txt")}
    }

data_db = load_data()

# ==========================================
# [데이터 전처리 엔진] : AI에게 넘겨줄 1차 분석 데이터 생성
# ==========================================
def get_raw_analysis(cat, score_data, t_q):
    if isinstance(score_data, list):
        total = sum(score_data); ans_list = score_data
    else:
        total = score_data; ans_list = []
        
    m_s = t_q * 4 if t_q > 0 else 1
    
    title = ""; summary = ""
    
    if cat == "IQ":
        val = int((total/m_s)*60+80)
        title = f"추정 FSIQ: {val}"
        if val >= 120: summary = "최우수 수준: 뛰어난 인지 자원과 정보 처리 속도"
        elif val >= 110: summary = "평균 상 수준: 안정적인 논리적 추론 및 응용력"
        else: summary = "평균 수준: 경험 기반의 안정적 문제 해결 능력"

    elif cat == "MBTI":
        if ans_list and t_q > 0:
            dims = [0, 0, 0, 0]
            for idx, a in enumerate(ans_list): dims[idx % 4] += a
            mid = (t_q / 4) * 2
            res_type = ""
            res_type += "I" if dims[0] < mid else "E"
            res_type += "S" if dims[1] < mid else "N"
            res_type += "T" if dims[2] < mid else "F"
            res_type += "J" if dims[3] < mid else "P"
        else: res_type = "INFJ"
        title = f"성격 유형: {res_type}"
        summary = "관련 성향 및 기질적 특성 발현"

    elif cat == "TCI":
        val = int(((total-(t_q*2))/t_q)*10+50)
        title = f"기질 T-Score: {val}"
        if val >= 60: summary = "높음: 뚜렷한 개성, 주도성, 외부 자극에 대한 민감성"
        elif val >= 41: summary = "보통: 유연한 대처, 감정적 안정감"
        else: summary = "낮음: 억제된 감정 표현, 독립적 태도, 냉담함"

    elif cat == "MMPI":
        val = int((total/m_s)*100)
        title = f"적응 지수: {val}"
        if val >= 65: summary = "상승(위험): 방어기제 활성화, 심리적 피로감 및 예민성 높음"
        else: summary = "정상: 건강한 자아강도, 유연한 스트레스 적응"

    elif cat == "CLINICAL":
        val = int((total/m_s)*100)
        title = f"임상 증상 지수: {val}"
        if val >= 65: summary = "위험: 우울/불안/소진(번아웃) 증상 감지, 신체화 징후 가능성"
        else: summary = "안정: 정서적 안정 및 일상 적응 양호"

    return f"[{cat}] {title} - {summary}"

# ==========================================
# 메인 UI 로직
# ==========================================
if 'reg' not in st.session_state: st.session_state['reg'] = False

if not st.session_state['reg']:
    st.title("🔍 정밀 심리 진단 시스템")
    name = st.text_input("성함(이름)")
    birth = st.text_input("생년월일(8자리)")
    gen = st.selectbox("성별", ["남성", "여성"])
    rel = st.selectbox("관계", ["본인", "부", "모", "자녀", "배우자", "기타"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 확인 및 기록 불러오기", use_container_width=True):
            if name and birth:
                with st.spinner("서버에서 대상자 기록을 조회 중입니다..."):
                    try:
                        res = requests.get(GOOGLE_SCRIPT_URL, params={"name": name, "birth": birth}, timeout=10).json()
                        st.session_state['u'] = {"name":name, "birth":birth, "gen":gen, "rel":rel}
                        st.session_state['reg'] = True
                        if res.get("status") == "success":
                            st.session_state['final_results'] = res["scores"]
                            st.rerun()
                        else:
                            st.rerun()
                    except Exception as e:
                        st.error("⚠️ 구글 시트 연결 오류가 발생했습니다.")
            else:
                st.error("이름과 생년월일을 모두 입력해주세요.")
    with col2:
        if st.button("🚀 신규 검사 바로 시작 (불러오기 생략)", use_container_width=True):
            if name and birth:
                st.session_state['u'] = {"name":name, "birth":birth, "gen":gen, "rel":rel}
                st.session_state['reg'] = True
                st.rerun()
            else:
                st.error("이름과 생년월일을 모두 입력해주세요.")
                
else:
    st.title("📊 종합 임상 심리 정밀 보고서")
    st.info(f"👤 성명: {st.session_state['u']['name']} | 연령: {st.session_state['u']['birth']} | 관계: {st.session_state['u']['rel']}")
    if st.button("🔄 대상자 변경"): 
        st.session_state.clear()
        st.rerun()
        
    t1, t2 = st.tabs(["📄 온라인 진단지", "📑 종합 소견서"])
    
    with t1:
        st.write("각 문항을 신중히 읽고, 평소의 자신과 가장 일치하는 항목을 선택해 주십시오.")
        cur_s = {}
        opts = {0:"매우 아니다", 1:"아니다", 2:"보통", 3:"그렇다", 4:"매우 그렇다"}
        for c, qs in data_db["qs"].items():
            if qs:
                with st.expander(f"📌 {c} 검사 ({len(qs)}문항)"):
                    ans_array = []
                    for i, q in enumerate(qs):
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), format_func=lambda x:opts[x], horizontal=True, key=f"{c}_{i}", index=2)
                        ans_array.append(ans)
                    cur_s[c] = ans_array
                    
        if st.button("🚀 검사 완료 및 제출", use_container_width=True):
            try:
                requests.post(GOOGLE_SCRIPT_URL, data=json.dumps({"user":st.session_state['u'], "scores":cur_s}), timeout=10)
            except Exception as e:
                pass
            st.session_state['final_results'] = cur_s
            st.success("제출 완료! [종합 소견서] 탭으로 이동하세요.")
            st.rerun()

    with t2:
        if 'final_results' in st.session_state:
            st.markdown("### ✨ [AI 통합 심리평가보고서 생성]")
            st.caption("실제 대학병원 심리평가보고서(Full Battery Assessment) 형식으로 통합 분석합니다.")
            
            if st.button("🧠 전문 임상심리사 소견서 생성하기", use_container_width=True):
                with st.spinner("AI가 각 지표 간의 연관성을 심층 분석하여 전문가용 보고서를 작성 중입니다... (약 15~30초 소요)"):
                    try:
                        # 1. AI에게 던져줄 1차 전처리 데이터 조립
                        raw_data_context = ""
                        for c, s in st.session_state['final_results'].items():
                            t_q = len(data_db["qs"].get(c, []))
                            if t_q > 0:
                                raw_data_context += get_raw_analysis(c, s, t_q) + "\n"
                        
                        # 2. 강력한 임상심리사 프롬프트
                        prompt = f"""
                        당신은 10년 이상의 경력을 가진 최고 수준의 정신건강임상심리사입니다.
                        내담자의 심리검사(IQ, MBTI, TCI, MMPI, 임상증상) 요약 데이터를 바탕으로,
                        실제 대학병원 심리평가보고서(Full Battery Assessment) 수준의 심층적이고 유기적인 종합 소견서를 작성해 주세요.
                        
                        [내담자 정보]
                        - 성명: {st.session_state['u']['name']}
                        - 연령: {st.session_state['u']['birth']}
                        
                        [1차 분석 원점수 데이터]
                        {raw_data_context}
                        
                        [작성 지침 - 매우 중요]
                        1. 기계적으로 점수만 나열하지 마세요. 각 검사 결과가 서로 어떻게 연결되고 내담자의 삶에 어떤 영향을 미치는지 통합적(Integrative)으로 서술하세요.
                           (예: "임상 지수가 높은 상태가 내담자의 완벽주의적 성격(MBTI J)과 결합되어 번아웃으로 나타난 것으로 시사된다" 등)
                        2. 문체는 반드시 전문가적이고 객관적인 평어체(~이다, ~함, ~것으로 시사됨, ~판단됨)를 사용하세요.
                        3. 보고서는 아래의 목차 구조를 정확히 지켜주세요:
                           # 종합 심리평가보고서 (Psychological Evaluation Report)
                           
                           ## 1. 인지 및 지적 기능 (IQ)
                           ## 2. 지각 및 사고적 측면
                           ## 3. 기질 및 성격 특성 (MBTI, TCI)
                           ## 4. 정서 및 심리적 적응 상태 (MMPI, CLINICAL)
                           ## 5. 요약 및 제언 (치료적 개입 방향 포함)
                        """
                        
                        response = model.generate_content(prompt)
                        st.session_state['ai_generated_report'] = response.text
                        st.success("✅ 정밀 분석 보고서 작성이 완료되었습니다.")
                    except Exception as e:
                        st.error(f"AI 연동 중 에러가 발생했습니다: {e}")

            # 리포트가 생성되어 있으면 화면에 출력
            if 'ai_generated_report' in st.session_state:
                st.divider()
                st.markdown(st.session_state['ai_generated_report'])
                st.divider()
                
                # 인쇄 및 저장 버튼
                st.subheader("🖨️ 리포트 저장 및 인쇄")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🖨️ 리포트 즉시 인쇄하기 (PDF 저장 가능)", use_container_width=True):
                        components.html("<script>window.print();</script>", height=0)
                
                with col2:
                    st.download_button(
                        label="💾 리포트 텍스트(TXT) 다운로드",
                        data=st.session_state['ai_generated_report'],
                        file_name=f"심리진단보고서_{st.session_state['u']['name']}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
        else:
            st.warning("분석할 데이터가 없습니다. [온라인 진단지] 탭에서 먼저 검사를 진행해 주십시오.")

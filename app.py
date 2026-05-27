import streamlit as st
import json, os, requests, re
import streamlit.components.v1 as components
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="정밀 심리 진단 시스템", layout="wide")

# 2. Gemini API 키 설정 및 AI 모델 준비 (Plain Text 연결)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-pro')

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
# [MBTI 전문가 데이터베이스]
# ==========================================
EXPERT_DB = {
    "ESTJ": {"title": "엄격한 관리자 (ESTJ)", "summary": "사실과 경험을 바탕으로 체계를 잡고 프로젝트를 추진하는 탁월한 리더입니다.", "f": ["현실적이고 실용적인 문제 해결", "명확한 규칙과 프로세스 선호"], "s": ["뛰어난 조직 관리 및 추진력", "책임감이 강하고 약속을 철저히 이행함"], "w": ["타인의 감정에 둔감할 수 있음", "예측 불가능한 변화에 스트레스를 받음"]},
    "ENTJ": {"title": "대담한 통솔자 (ENTJ)", "summary": "비전을 세우고 조직을 이끌어가는 데 천부적인 재능이 있는 전략가입니다.", "f": ["장기적인 비전 수립", "논리적이고 객관적인 상황 분석"], "s": ["복잡한 문제를 해결하는 지적 능력", "카리스마 있는 리더십"], "w": ["비효율과 우유부단함을 참지 못함", "타인의 감정적 호소를 비합리적이라 여길 수 있음"]},
    "ESFJ": {"title": "사교적인 외교관 (ESFJ)", "summary": "타인에 대한 깊은 배려와 책임감으로 주변을 조화롭게 이끄는 조력자입니다.", "f": ["화목한 분위기와 협력 중시", "구체적이고 실질적인 도움 제공"], "s": ["조직의 융화와 안정감을 가져옴", "타인의 필요를 빠르게 파악함"], "w": ["비판에 매우 민감하게 반응함", "갈등 상황에서 극심한 스트레스 경험"]},
    "ENFJ": {"title": "정의로운 사회운동가 (ENFJ)", "summary": "타인의 성장을 돕고 공동체의 비전을 이끌어내는 카리스마 있는 멘토입니다.", "f": ["진정성 있는 소통과 공감", "공동체의 성장과 화합 중시"], "s": ["타인에게 영감을 주는 탁월한 리더십", "개인의 잠재력을 이끌어내는 능력"], "w": ["타인의 문제를 자신의 것처럼 짊어지려 함", "과도한 헌신으로 인한 번아웃 위험"]},
    "ESTP": {"title": "모험을 즐기는 사업가 (ESTP)", "summary": "위기 상황에서 빠른 판단력으로 문제를 해결하는 에너지 넘치는 행동파입니다.", "f": ["즉흥적이고 유연한 대처", "현재 순간의 자극과 즐거움 추구"], "s": ["위기 상황에서의 뛰어난 문제 해결력", "사람들을 이끄는 친화력"], "w": ["장기적인 계획 수립에 약함", "지루하고 반복적인 업무를 견디기 어려워함"]},
    "ESFP": {"title": "자유로운 영혼의 연예인 (ESFP)", "summary": "뛰어난 적응력과 사교성으로 분위기를 주도하는 에너자이저입니다.", "f": ["긍정적이고 사교적인 태도", "미적 감각과 오감의 즐거움 중시"], "s": ["어떤 환경에서도 빠르게 적응하는 유연성", "타인을 즐겁게 해주는 매력"], "w": ["진지하고 심각한 갈등 상황 회피", "충동적인 결정 가능성"]},
    "ENTP": {"title": "뜨거운 논쟁을 즐기는 변론가 (ENTP)", "summary": "기존의 틀을 깨고 새로운 가능성을 탐구하는 혁신적인 아이디어 뱅크입니다.", "f": ["새로운 아이디어와 가능성 탐구", "지적인 토론과 논쟁 즐김"], "s": ["기존 시스템의 문제점을 파악하는 통찰력", "창의적이고 혁신적인 해결책 제시"], "w": ["아이디어 실행 마무리가 부족할 수 있음", "세부적인 디테일 관리에 소홀함"]},
    "ENFP": {"title": "재기발랄한 활동가 (ENFP)", "summary": "풍부한 상상력과 열정으로 타인에게 영감을 주는 창조적인 자유인입니다.", "f": ["상상력이 풍부하고 직관에 의존", "타인과의 정서적 교류 중시"], "s": ["사람들에게 영감을 주고 동기를 부여함", "틀에 박히지 않은 창의적 접근"], "w": ["반복되는 일상에 쉽게 싫증을 느낌", "엄격한 통제나 규율을 견디기 힘들어함"]},
    "ISTJ": {"title": "청렴결백한 논리주의자 (ISTJ)", "summary": "책임감이 강하고 사실에 입각하여 일을 끝까지 완수하는 믿음직한 기둥입니다.", "f": ["사실과 데이터 기반의 논리적 사고", "구조화된 환경과 질서 선호"], "s": ["한 번 맡은 일은 끝까지 해내는 강한 책임감", "정확하고 꼼꼼한 일 처리"], "w": ["새롭고 검증되지 않은 아이디어에 대한 배타성", "갑작스러운 변화에 대한 스트레스"]},
    "ISFJ": {"title": "용감한 수호자 (ISFJ)", "summary": "조용하고 헌신적으로 타인을 보호하고 지원하는 따뜻한 관리자입니다.", "f": ["타인의 감정을 배려하는 세심함", "전통과 안정을 중시"], "s": ["보이지 않는 곳에서 조직을 지탱하는 헌신성", "탁월한 기억력과 디테일"], "w": ["스스로의 감정이나 요구를 잘 표현하지 못함", "불편한 변화를 극도로 회피하려 함"]},
    "INTJ": {"title": "용의주도한 전략가 (INTJ)", "summary": "통찰력과 논리력으로 시스템을 설계하고 미래를 계획하는 마스터마인드입니다.", "f": ["독립적이고 전략적인 사고", "비효율성을 개선하려는 강한 의지"], "s": ["복잡한 시스템을 분석하고 설계하는 능력", "장기적인 안목과 목표 지향성"], "w": ["비논리적인 사람들과의 소통에 어려움", "자신만의 기준이 너무 높아 타인에게 엄격함"]},
    "INFJ": {"title": "통찰력 있는 선지자 (INFJ)", "summary": "타인에게 의욕을 불어넣으며 그들의 잠재력을 바라보고 발휘하도록 돕는 성향입니다.", "f": ["타인의 감정과 의도를 읽는 통찰력", "강한 가치관과 내면의 신념"], "s": ["사람들의 숨은 잠재력을 이끌어내는 멘토링", "목표의 의미가 분명할 때의 강한 추진력"], "w": ["타인의 감정을 지나치게 흡수하여 번아웃 발생", "높은 이상으로 인한 실행 지연"]},
    "ISTP": {"title": "만능 재주꾼 (ISTP)", "summary": "논리적이고 뛰어난 상황 적응력으로 실질적인 문제를 빠르게 해결하는 해결사입니다.", "f": ["논리적 분석과 뛰어난 상황 적응력", "개인의 자율성과 프라이버시 중시"], "s": ["위급 상황에서의 차분하고 효율적인 대처", "실질적인 도구 활용 및 기술적 문제 해결력"], "w": ["감정적인 공감이나 표현이 서툴 수 있음", "지나친 간섭이나 엄격한 통제를 거부함"]},
    "ISFP": {"title": "호기심 많은 예술가 (ISFP)", "summary": "현재의 순간을 즐기며 온화하고 수용적인 태도로 조화를 이루는 평화주의자입니다.", "f": ["미적 감각과 오감의 즐거움 추구", "갈등을 회피하고 조화를 중시"], "s": ["타인을 있는 그대로 수용하는 따뜻함", "환경에 대한 뛰어난 적응력과 유연성"], "w": ["엄격한 마감 기한이나 규율에 약함", "미래에 대한 장기적 계획 수립을 어려워함"]},
    "INTP": {"title": "논리적인 사색가 (INTP)", "summary": "복잡한 이론과 논리를 탐구하며 지적 호기심을 충족시키는 철학자입니다.", "f": ["지적 호기심과 이론 탐구", "독립적이고 자율적인 연구 선호"], "s": ["기존의 틀을 깨는 혁신적이고 논리적인 분석력", "복잡한 문제의 근본 원인을 파악하는 통찰력"], "w": ["타인의 감정적 반응을 이해하기 어려워함", "실생활의 반복적인 행정 업무를 매우 귀찮아함"]},
    "INFP": {"title": "열정적인 중재자 (INFP)", "summary": "본인만의 깊은 가치관을 바탕으로 타인에 대한 깊은 공감 능력을 지닌 이상주의자입니다.", "f": ["개인적인 의미와 가치 중시", "창의적 표현과 진정성 있는 관계 추구"], "s": ["타인의 아픔에 깊이 공감하는 능력", "가치가 부여된 일에 대한 무한한 열정"], "w": ["비판이나 거절에 매우 취약함", "현실적인 제약(시간, 돈)을 고려하는 데 약함"]}
}

# ==========================================
# [하이브리드 분석 엔진] 
# ==========================================
def get_blended_report(cat, score_data, t_q):
    if isinstance(score_data, list):
        total = sum(score_data)
        ans_list = score_data
    else:
        total = score_data
        ans_list = []
        
    m_s = t_q * 4 if t_q > 0 else 1
    ratio = total / m_s
    
    metric = ""; title = ""; summary = ""
    features = []; strengths = []; weaknesses = []
    
    if cat == "IQ":
        val = int((total/m_s)*60+80); metric = f"추정 FSIQ: {val}"
        if val >= 120:
            title = "최우수 수준 (Superior / IQ 120 이상)"
            summary = "매우 뛰어난 인지적 자원과 정보 처리 속도를 보유하고 있습니다."
            features = ["뛰어난 직관력과 패턴 인식 능력", "복잡한 추상적 개념을 빠르게 이해하고 응용"]
            strengths = ["어려운 문제를 다차원적으로 분석하여 해결책 도출", "새로운 지식 습득 속도가 타의 추종을 불허함"]
            weaknesses = ["단순 반복 업무에서 쉽게 지루함을 느낄 수 있음", "타인의 느린 처리 속도에 답답함을 느낄 우려"]
        elif val >= 110:
            title = "평균 상 수준 (High Average / IQ 110 ~ 119)"
            summary = "우수한 인지적 자원을 바탕으로 복잡한 과제를 체계적으로 수행할 수 있는 안정적인 능력을 갖추고 있습니다."
            features = ["실무적 통찰과 뛰어난 논리적 추론 능력", "목표 지향적인 과제 수행에서 높은 몰입도 유지"]
            strengths = ["체계적인 업무 구조화 및 실행 능력", "새로운 기술을 현장에 안정적으로 적용하는 응용력"]
            weaknesses = ["비정형적인 변화에 대한 유연성이 일시적으로 저하될 수 있음", "높은 수행 기준을 스스로에게 부여하여 심리적 압박 증가"]
        else:
            title = "평균 수준 (Average / IQ 90 ~ 109)"
            summary = "경험과 훈련을 통해 실무 능력을 탄탄하게 쌓아 올리며 일상 과제를 훌륭히 수행합니다."
            features = ["경험에 기반한 안정적인 문제 해결", "주어진 매뉴얼과 절차를 정확히 숙지하고 이행"]
            strengths = ["반복적인 실무에서 극도의 안정감과 효율성 발휘", "현실적이고 상식적인 판단 능력"]
            weaknesses = ["완전히 낯선 이론적 과제 앞에서는 초기 적응 시간이 필요함"]

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
        
        metric = f"도출 유형: {res_type}"
        info = EXPERT_DB.get(res_type, EXPERT_DB["INFJ"])
        title = info["title"]
        summary = info["summary"]
        features = info["f"]
        strengths = info["s"]
        weaknesses = info["w"]

    elif cat == "TCI":
        val = int(((total-(t_q*2))/t_q)*10+50); metric = f"T-Score: {val}"
        if val >= 60:
            title = "높음 (High / T점수 60 이상)"
            summary = "특정 기질적 특성이 매우 뚜렷하게 발현되어 강한 개성과 주도성을 보입니다."
            features = ["외부 자극에 대한 민감한 반응성", "강한 목표 지향성 및 추진력"]
            strengths = ["위기 상황이나 새로운 과제 앞에서 폭발적인 에너지 발휘", "타인을 이끌고 환경을 주도하는 리더십"]
            weaknesses = ["감정 기복이나 충동성이 나타날 수 있음", "타인과의 타협 및 양보에 어려움을 겪을 수 있음"]
        elif val >= 41:
            title = "보통 (Moderate / T점수 41 ~ 59)"
            summary = "기질적 특성이 평균적인 범주 내에 있어 극단적으로 치우치지 않으며, 상황에 따라 유연한 대처가 가능합니다."
            features = ["상황적 유연성과 감정적 안정감", "적절한 수용성과 합리적인 판단 능력"]
            strengths = ["모나지 않은 성향으로 갈등 없이 원만한 대인관계 유지", "급격한 감정 기복 없이 일관된 태도로 업무 수행"]
            weaknesses = ["뚜렷한 개성이 부족하여 강렬한 인상을 남기기 어려움", "정체된 환경에서 안일함에 빠질 우려"]
        else:
            title = "낮음 (Low / T점수 40 이하)"
            summary = "외부 자극에 크게 동요하지 않으며, 매우 독립적이고 신중한 태도를 유지합니다."
            features = ["차분하고 억제된 감정 표현", "타인의 인정보다 자신의 내면적 기준을 중시"]
            strengths = ["스트레스 상황에서도 흔들리지 않는 평정심", "독립적인 작업 환경에서 고도의 집중력 발휘"]
            weaknesses = ["대인관계에서 다소 냉담하거나 무심해 보일 수 있음", "변화와 도전을 지나치게 회피할 가능성"]

    elif cat == "MMPI":
        val = int((total/m_s)*100); metric = f"성격/적응 지수: {val}/100"
        if val >= 65:
            title = "임상적 주의 요망 (Elevated)"
            summary = "현재 대인관계나 환경적 압박에 대해 방어기제가 강하게 작동하고 있습니다."
            features = ["타인의 피드백에 대한 높은 예민성", "심리적 피로감 누적 및 방어적 태도"]
            strengths = ["위험을 빠르게 감지하고 자신을 보호하려는 생존 본능"]
            weaknesses = ["사소한 오해로 인한 대인관계 갈등 발생 가능성", "타인의 의도를 부정적으로 해석할 우려"]
        else:
            title = "정서적 안녕 상태 (Normal)"
            summary = "심리적 건강도가 우수하며, 외부 비판에 쉽게 흔들리지 않는 건강한 자아강도를 지니고 있습니다."
            features = ["외부 비판에 흔들리지 않는 자아존중감", "타인과의 협력적인 팀플레이 선호"]
            strengths = ["스트레스 상황에 유연하게 적응하는 탄력성", "논리적이고 건설적인 피드백 수용 능력"]
            weaknesses = ["명분 없는 갈등이나 뒷담화를 극도로 피곤해함", "자신의 기준과 다를 때 타인을 설득하려는 경향"]

    elif cat == "CLINICAL":
        val = int((total/m_s)*100); metric = f"임상 증상 지수: {val}/100"
        if val >= 65:
            title = "스트레스/소진 경고 (High Risk)"
            summary = "일상적인 수준을 넘어서는 우울, 불안, 혹은 번아웃 증상이 감지됩니다."
            features = ["수면 불규칙, 피로감 등 신체화 증상 발현 가능성", "에너지 고갈로 인한 업무 효율 저하"]
            strengths = ["본인의 한계를 인식하고 휴식을 취할 수 있는 기회"]
            weaknesses = ["지속될 경우 심리적 무기력증으로 발전할 우려", "적절한 스트레스 해소 창구 부재"]
        else:
            title = "스트레스 관리 양호 (Healthy)"
            summary = "현재 급성 스트레스나 소진(번아웃) 징후 없이 멘탈이 잘 관리되고 있습니다."
            features = ["적절한 스트레스 해소 루틴 보유", "일과 삶의 균형(워라밸) 유지 상태 양호"]
            strengths = ["정신적 에너지가 충만하여 새로운 과제에 도전할 수 있는 여력 존재", "건강한 수면 및 생활 리듬 유지"]
            weaknesses = ["갑작스러운 위기 상황 시 멘탈 붕괴를 막을 매뉴얼 사전 점검 필요"]

    return total, m_s, ratio, metric, title, summary, features, strengths, weaknesses

# 4. 메인 UI 로직
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
                            st.session_state['is_old_user'] = True
                            st.rerun()
                        else:
                            st.session_state['is_old_user'] = False
                            st.rerun()
                    except Exception as e:
                        st.error("⚠️ 구글 시트 연결 오류가 발생했습니다! (URL을 확인해주세요)")
            else:
                st.error("이름과 생년월일을 모두 입력해주세요.")
    with col2:
        if st.button("🚀 신규 검사 바로 시작 (불러오기 생략)", use_container_width=True):
            if name and birth:
                st.session_state['u'] = {"name":name, "birth":birth, "gen":gen, "rel":rel}
                st.session_state['is_old_user'] = False
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
                    
        if st.button("🚀 검사 완료 및 전문 분석 요청", use_container_width=True):
            try:
                requests.post(GOOGLE_SCRIPT_URL, data=json.dumps({"user":st.session_state['u'], "scores":cur_s}), timeout=10)
            except Exception as e:
                st.warning("데이터는 저장되었으나 서버(Google Apps Script) 전송에 실패했습니다.")
                
            st.session_state['final_results'] = cur_s
            st.session_state['is_old_user'] = True
            st.success("분석이 완료되었습니다.")
            st.rerun()

    with t2:
        if 'final_results' in st.session_state:
            # 텍스트 다운로드를 위한 변수
            report_text = f"==========================================\n"
            report_text += f" 종합 임상 심리 정밀 보고서 \n"
            report_text += f"==========================================\n\n"
            report_text += f"[1. 피검자 정보]\n"
            report_text += f"- 성명: {st.session_state['u']['name']} | 연령: {st.session_state['u']['birth']} | 관계: {st.session_state['u']['rel']}\n\n"
            
            # 1. [지표 요약] 섹션
            st.markdown("### 📊 [지표 요약]")
            st.divider()
            
            report_text += f"[2. 지표 요약]\n------------------------------------------\n"
            
            for c, s in st.session_state['final_results'].items():
                t_q = len(data_db["qs"].get(c, []))
                if t_q > 0:
                    total, m_s, ratio, metric, title, summary, f, sth, w = get_blended_report(c, s, t_q)
                    pct = min(int(ratio * 100), 100)
                    col1, col2, col3 = st.columns([1, 2, 4])
                    with col1: st.markdown(f"**{c}**")
                    with col2: st.markdown(f"{total} / {m_s}")
                    with col3: st.progress(ratio if ratio <= 1.0 else 1.0)
                    report_text += f"{c:<10} | {total:>3} / {m_s:>3} | {pct}%\n"
            
            report_text += f"------------------------------------------\n\n"
            st.write("")
            st.write("")
            
            # 2. [정밀 분석 결과] 섹션
            st.markdown("### 📋 [정밀 분석 결과]")
            st.divider()
            report_text += f"[3. 정밀 분석 결과]\n==========================================\n"
            
            for c, s in st.session_state['final_results'].items():
                t_q = len(data_db["qs"].get(c, []))
                if t_q > 0:
                    total, m_s, ratio, metric, title, summary, features, strengths, weaknesses = get_blended_report(c, s, t_q)
                    
                    st.markdown(f"#### ▶ {c} 분석")
                    st.markdown(f"**- 결과:** <span style='color:#1f77b4;'>**{title}**</span> ({metric})", unsafe_allow_html=True)
                    st.markdown(f"> *\"{summary}\"*")
                    
                    report_text += f"▶ {c} 분석\n"
                    report_text += f" - 결과: {title} ({metric})\n"
                    report_text += f"   \"{summary}\"\n\n"
                    
                    if features:
                        st.markdown("**[주요 특징]**")
                        report_text += f" [주요 특징]\n"
                        for feat in features: 
                            st.markdown(f"· {feat}")
                            report_text += f"  · {feat}\n"
                    if strengths:
                        st.markdown("**[핵심 강점]**")
                        report_text += f"\n [핵심 강점]\n"
                        for sth in strengths: 
                            st.markdown(f"· {sth}")
                            report_text += f"  · {sth}\n"
                    if weaknesses:
                        st.markdown("**[주의 및 보완점]**")
                        report_text += f"\n [주의 및 보완점]\n"
                        for weak in weaknesses: 
                            st.markdown(f"· {weak}")
                            report_text += f"  · {weak}\n"
                    
                    st.write("")
                    st.divider()
                    report_text += f"\n------------------------------------------\n\n"
            
            st.caption("※ 위 분석은 알고리즘 기반 추정치로, 전문 상담가의 자문을 권장합니다.")
            
            # 3. [인쇄 및 저장 버튼 구역]
            st.subheader("🖨️ 리포트 저장 및 인쇄")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🖨️ 리포트 즉시 인쇄하기 (PDF 저장 가능)", use_container_width=True):
                    components.html("<script>window.print();</script>", height=0)
            
            with col2:
                st.download_button(
                    label="💾 리포트 텍스트(TXT) 다운로드",
                    data=report_text,
                    file_name=f"심리진단보고서_{st.session_state['u']['name']}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
            # 4. [AI 정밀 종합 심리 소견서 구역]
            st.divider()
            st.markdown("### ✨ [AI 임상 심리 정밀 소견 분석]")
            
            if st.button("🧠 임상심리사 버전 종합 소견서 생성하기", use_container_width=True):
                with st.spinner("AI 임상심리사가 데이터를 종합 분석하여 고유 소견서를 작성 중입니다... (약 10~20초 소요)"):
                    try:
                        user_data_text = f"이름: {st.session_state['u']['name']}, 연령: {st.session_state['u']['birth']}, 점수 데이터: {st.session_state['final_results']}"
                        
                        prompt = f"""
                        당신은 10년 차 전문 정신건강임상심리사입니다. 
                        다음 내담자의 심리검사 데이터를 바탕으로, 각 항목이 분절되지 않고 
                        하나의 스토리로 자연스럽게 이어지는 깊이 있는 종합 심리 평가 보고서를 작성해 주세요.
                        기계적인 분석이 아닌, 실제 임상 현장의 보고서처럼 원인과 결과를 유기적으로 엮어 전문적인 심리학 용어를 사용해 주세요.
                        
                        [내담자 데이터]
                        {user_data_text}
                        """
                        
                        response = model.generate_content(prompt)
                        st.success("AI 정밀 소견서 작성이 완료되었습니다.")
                        st.info("📊 전문 임상 분석 소견")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"AI 연동 중 에러가 발생했습니다: {e}")
        else:
            st.warning("분석할 데이터가 없습니다. [온라인 진단지] 탭에서 먼저 검사를 진행해 주십시오.")

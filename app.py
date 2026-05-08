import streamlit as st
import json, os, requests, re

# 1. 환경 설정
st.set_page_config(page_title="정밀 심리 진단 시스템", layout="wide")
st.markdown("<style>#MainMenu, footer, header {visibility: hidden;}</style>", unsafe_allow_html=True)

# 🚨 [매우 중요] 아래 따옴표 안에 본인의 구글 웹 앱 주소(exec로 끝나는 주소)를 넣으세요!
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
# [하이브리드 분석 엔진] V46.0 양식 + 최신 로직
# ==========================================
def get_blended_report(cat, score_data, t_q):
    if isinstance(score_data, list):
        total = sum(score_data); ans_list = score_data
    else:
        total = score_data; ans_list = []
        
    m_s = t_q * 4 if t_q > 0 else 1
    ratio = total / m_s
    
    metric = ""; title = ""; summary = ""; 
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
        else: res_type = "INFJ" # 배열 데이터가 없을 경우 기본값을 박준우님 원래 결과로 임시 세팅
        
        metric = f"도출 유형: {res_type}"
        if res_type == "INFJ":
            title = "차분한 비전가이자 이상주의자 (INFJ)"
            summary = "타인에게 의욕을 불어넣으며 그들의 잠재력을 바라보고 발휘하도록 돕는 성향을 가지고 있습니다."
            features = ["타인의 감정과 의도를 읽는 공감과 통찰력", "세상을 더 나은 방향으로 바꾸고자 하는 강한 가치관", "표면적 관계보다 진솔하고 깊이 있는 이해 중시"]
            strengths = ["상대의 감정을 조율하고 중재하는 탁월한 능력", "목표의 의미가 분명할 때 발휘되는 흔들림 없는 추진력", "논리보다 사람의 감정과 가치를 우선하는 따뜻한 리더십"]
            weaknesses = ["타인의 감정을 지나치게 흡수하여 발생할 수 있는 정서적 과부하", "높은 이상과 완벽주의로 인한 실행 지연", "갈등을 회피하다가 스트레스가 누적될 우려"]
        else:
            title = f"성격 유형 지표 ({res_type})"
            summary = "본인만의 고유한 성향을 바탕으로 세상과 상호작용합니다. (상세 DB 업데이트 예정)"
            features = ["유형 고유의 정보 수집 및 판단 방식 활용", "특정 환경에서 에너지를 얻고 소비하는 패턴 형성"]
            strengths = ["본인 유형에 맞는 환경이 주어질 때 탁월한 성과 발휘"]
            weaknesses = ["반대 성향의 환경에서 스트레스 취약성 존재"]

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
        val = int((total/m_s)*100); metric = f"위험 지수: {val}/100"
        if val >= 65:
            title = "임상적 주의 요망 (Elevated)"
            summary = "현재 대인관계나 환경적 압박에 대해 방어기제가 강하게 작동하고 있습니다."
            features = ["타인의 피드백에 대한 높은 예민성", "심리적 피로감 누적 및 방어적 태도"]
            strengths = ["위험을 빠르게 감지하고 자신을 보호하려는 생존 본능"]
            weaknesses = ["사소한 오해로 인한 대인관계 갈등 발생 가능성", "타인의 의도를 부정적으로 해석할 우려"]
        else:
            title = "정서적 안녕 상태 (Normal / 위험 지수 65 미만)"
            summary = "심리적 건강도가 우수하며, 외부 압박에 대해 유연하고 효과적으로 대응할 수 있는 상태입니다."
            features = ["높은 자기 효능감과 능동적인 대처 능력", "타인과의 경계를 적절히 유지하는 건강한 대인관계"]
            strengths = ["실패를 배움의 기회로 삼는 강력한 회복 탄력성", "안정을 바탕으로 주변에 긍정적 영향을 주는 정서적 리더십"]
            weaknesses = ["현재의 안정감이 자만으로 이어지지 않도록 예방 관리 필요", "일상의 지루함을 막기 위한 새로운 지적 자극 필요"]

    elif cat == "CLINICAL":
        val = int((total/m_s)*100); metric = f"위험 지수: {val}/100"
        if val >= 65:
            title = "스트레스/소진 경고 (High Risk)"
            summary = "일상적인 수준을 넘어서는 우울, 불안, 혹은 번아웃 증상이 감지됩니다."
            features = ["수면 불규칙, 피로감 등 신체화 증상 발현 가능성", "에너지 고갈로 인한 업무 효율 저하"]
            strengths = ["본인의 한계를 인식하고 휴식을 취할 수 있는 기회"]
            weaknesses = ["지속될 경우 임상적 우울증이나 무기력증으로 발전할 우려", "적절한 스트레스 해소 창구 부재"]
        else:
            title = "스트레스 관리 양호 (Healthy)"
            summary = "현재 급성 스트레스나 소진(번아웃) 징후 없이 멘탈이 잘 관리되고 있습니다."
            features = ["적절한 스트레스 해소 루틴 보유", "일과 삶의 균형(워라밸) 유지 상태 양호"]
            strengths = ["정신적 에너지가 충만하여 새로운 과제에 도전할 수 있는 여력 존재", "건강한 수면 및 식욕 유지"]
            weaknesses = ["갑작스러운 위기 상황 시 대처 매뉴얼 사전 점검 필요"]

    return total, m_s, ratio, metric, title, summary, features, strengths, weaknesses

# 3. 메인 UI 로직
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
                        st.error("⚠️ 구글 시트 연결 오류가 발생했습니다!")
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
    st.title("📊 종합 임상 심리 정밀 보고서 (V4.0)")
    st.info(f"👤 성명: {st.session_state['u']['name']} | 연령: {st.session_state['u']['birth']} | 관계: {st.session_state['u']['rel']}")
    if st.button("🔄 대상자 변경"): st.session_state.clear(); st.rerun()
        
    d_tab = 1 if st.session_state.get('is_old_user') else 0
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
            requests.post(GOOGLE_SCRIPT_URL, data=json.dumps({"user":st.session_state['u'], "scores":cur_s}))
            st.session_state['final_results'] = cur_s
            st.session_state['is_old_user'] = True
            st.success("데이터가 안전하게 전송되었습니다."); st.rerun()

    with t2:
        if 'final_results' in st.session_state:
            # 1. [지표 요약] 섹션 추가 (V46.0 스타일 대시보드)
            st.markdown("### 📊 [지표 요약]")
            st.divider()
            
            for c, s in st.session_state['final_results'].items():
                t_q = len(data_db["qs"].get(c, []))
                if t_q > 0:
                    total, m_s, ratio, metric, title, summary, f, sth, w = get_blended_report(c, s, t_q)
                    pct = min(int(ratio * 100), 100)
                    col1, col2, col3 = st.columns([1, 2, 4])
                    with col1: st.markdown(f"**{c}**")
                    with col2: st.markdown(f"{total} / {m_s}")
                    with col3: 
                        st.progress(ratio if ratio <= 1.0 else 1.0)
            
            st.write("")
            st.write("")
            
            # 2. [정밀 분석 결과] 섹션 (V46.0 디테일 텍스트)
            st.markdown("### 📋 [정밀 분석 결과]")
            st.divider()
            
            for c, s in st.session_state['final_results'].items():
                t_q = len(data_db["qs"].get(c, []))
                if t_q > 0:
                    total, m_s, ratio, metric, title, summary, features, strengths, weaknesses = get_blended_report(c, s, t_q)
                    
                    st.markdown(f"#### ▶ {c} 분석")
                    st.markdown(f"**- 결과:** <span style='color:#1f77b4;'>**{title}**</span> ({metric})", unsafe_allow_html=True)
                    st.markdown(f"> *\"{summary}\"*")
                    
                    if features:
                        st.markdown("**[주요 특징]**")
                        for feat in features: st.markdown(f"· {feat}")
                    if strengths:
                        st.markdown("**[핵심 강점]**")
                        for sth in strengths: st.markdown(f"· {sth}")
                    if weaknesses:
                        st.markdown("**[주의 및 보완점]**")
                        for weak in weaknesses: st.markdown(f"· {weak}")
                    
                    st.write("")
                    st.divider()
            
            st.caption("※ 위 분석은 알고리즘 기반 추정치로, 절대적인 의학적 진단을 대신할 수 없습니다.")
        else:
            st.warning("분석할 데이터가 없습니다. [온라인 진단지] 탭에서 먼저 검사를 진행해 주십시오.")

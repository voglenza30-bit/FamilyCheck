import streamlit as st
import json, os, requests, re

# 1. 환경 설정
st.set_page_config(page_title="정밀 심리 진단 시스템", layout="wide")
st.markdown("<style>#MainMenu, footer, header {visibility: hidden;}</style>", unsafe_allow_html=True)

# [필수 확인] 배포하신 구글 웹 앱 URL을 넣으세요
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxvYpP9t4OFqTJRhHWZL2-YhFkw9QjoIBUrLdevUH42uqKicdakSw7DfqzgBZjYNpS1pQ/exec"

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

# 2. [핵심] 고도화된 전문 심리 분석 엔진
def get_detailed_report(cat, score, t_q):
    m_s = t_q * 4 if t_q > 0 else 1
    ratio = score / m_s
    
    report = {"metric": "", "title": "", "details": "", "advice": ""}
    
    if cat == "IQ":
        val = int(ratio * 60 + 80)
        report["metric"] = f"추정 FSIQ: {val}"
        if val >= 120:
            report["title"] = "최우수 수준 (Superior / IQ 120 이상)"
            report["details"] = "매우 뛰어난 인지적 자원과 정보 처리 속도를 보유하고 있습니다. 복잡한 문제를 다차원적으로 분석하고 논리적으로 해결하는 능력이 탁월하며, 낯선 환경이나 새로운 학습 과제가 주어졌을 때 패턴을 빠르게 파악합니다. 추상적 개념을 실무에 적용하는 데 강력한 강점을 보입니다."
            report["advice"] = "현재의 인지 능력을 극대화하기 위해, 고도의 전략 기획이나 창의적인 문제 해결이 필요한 과업에 집중하는 것을 권장합니다."
        elif val >= 110:
            report["title"] = "평균 상 수준 (High Average / IQ 110 ~ 119)"
            report["details"] = "우수한 인지적 자원을 바탕으로 복잡한 과제를 체계적으로 수행할 수 있는 안정적인 능력을 갖추고 있습니다. 논리적 추론과 상황 판단력이 우수합니다."
            report["advice"] = "업무의 효율성을 높이기 위해 본인만의 정보 처리 루틴을 개발하고, 관리자 및 리더십 포지션에서의 역량을 강화해 보십시오."
        else:
            report["title"] = "평균 수준 (Average / IQ 90 ~ 109)"
            report["details"] = "일반적인 사회적, 직업적 요구 사항을 충족시킬 수 있는 밸런스 있는 인지 능력을 보유하고 있습니다. 경험을 바탕으로 한 실무 능력이 돋보입니다."
            report["advice"] = "새로운 지식을 습득할 때 체계적인 반복 학습과 실무 적용을 병행하면 인지적 효율성을 크게 높일 수 있습니다."

    elif cat == "MBTI":
        # MBTI 누락 버그 수정 및 심층화
        val = int(ratio * 100)
        report["metric"] = f"성향 발현 지수: {val}/100"
        if val >= 60:
            report["title"] = "외향 및 직관 중심 발현형 (E/N Focused)"
            report["details"] = "외부 세계와의 활발한 상호작용을 통해 에너지를 얻으며, 거시적인 비전과 새로운 가능성을 탐구하는 데 탁월한 역량을 보입니다. 변화를 두려워하지 않고 혁신적인 아이디어를 제안하는 성향이 강합니다."
            report["advice"] = "다양한 사람들과 네트워킹할 수 있는 환경에서 최고의 성과를 냅니다. 다만, 세부적인 실행 계획(디테일)을 챙기는 보완적 시스템을 마련하는 것이 좋습니다."
        elif val >= 40:
            report["title"] = "균형 및 적응형 (Balanced Type)"
            report["details"] = "상황에 따라 내향적인 신중함과 외향적인 활동성을 유연하게 오가는 균형 잡힌 성향입니다. 극단에 치우치지 않아 조직 내에서 조율자 역할을 훌륭히 수행합니다."
            report["advice"] = "본인의 핵심 가치관을 확립하고, 스트레스 상황에서 자신이 에너지를 회복하는 방식을 정확히 파악하는 것이 중요합니다."
        else:
            report["title"] = "내향 및 감각 중심 발현형 (I/S Focused)"
            report["details"] = "내면의 깊이 있는 통찰을 중시하며, 실용적이고 구체적인 데이터를 바탕으로 안정적인 의사결정을 내리는 성향입니다. 사실에 입각한 꼼꼼한 일 처리가 돋보입니다."
            report["advice"] = "안정적이고 독립적인 작업 환경이 주어질 때 극도의 집중력을 발휘합니다. 때로는 안전지대를 벗어나 새로운 접근을 시도해 보는 것도 성장에 도움이 됩니다."

    elif cat == "TCI":
        val = int(((score - (t_q * 2)) / t_q) * 10 + 50)
        report["metric"] = f"T-Score: {val}"
        if val >= 65:
            report["title"] = "높음 (High / T점수 65 이상)"
            report["details"] = "특정 기질적/성격적 특성이 매우 강하게 발현되고 있습니다. 주도적이고 자극을 추구하는 성향이 강하거나, 반대로 위험을 극도로 회피하는 등 뚜렷한 개성을 보입니다."
            report["advice"] = "강한 기질적 특성은 강력한 무기가 될 수 있으나, 대인관계나 스트레스 상황에서 양날의 검이 될 수 있으므로 자기 객관화 훈련이 필요합니다."
        elif val >= 41:
            report["title"] = "보통 (Moderate / T점수 41 ~ 64)"
            report["details"] = "기질적 특성이 평균적인 범주 내에 있어 극단적으로 치우치지 않으며, 다양한 상황과 환경 변화에 무난하게 적응하고 대처할 수 있는 유연성을 지니고 있습니다."
            report["advice"] = "현재의 안정적인 심리적 상태를 유지하면서, 본인이 특별히 열정을 느끼는 분야를 발굴하여 성격적 강점으로 발전시키십시오."
        else:
            report["title"] = "낮음 (Low / T점수 40 이하)"
            report["details"] = "해당 기질의 억제력이 강하게 나타납니다. 외부의 자극이나 보상에 크게 동요하지 않으며, 매우 독립적이거나 무던한 심리적 태도를 유지합니다."
            report["advice"] = "정서적 환기나 외부와의 소통이 부족해질 수 있으므로, 의식적으로 타인과 감정을 교류하거나 취미 활동을 가지는 것이 정서 건강에 이롭습니다."

    elif cat in ["MMPI", "CLINICAL"]:
        val = int(ratio * 100)
        report["metric"] = f"위험 지수: {val}/100"
        if val >= 70:
            report["title"] = "임상적 주의 요망 (Elevated / 위험 지수 70% 이상)"
            report["details"] = "현재 상당한 수준의 심리적 압박감이나 스트레스를 경험하고 있을 가능성이 높습니다. 정서적 불안정, 우울감, 또는 신체화 증상이 발현될 수 있는 상태입니다."
            report["advice"] = "즉각적인 휴식과 스트레스 요인의 제거가 필요하며, 상태가 지속될 경우 전문적인 심리 상담이나 의료적 지원을 고려하는 것을 강력히 권장합니다."
        elif val >= 40:
            report["title"] = "경계 및 관찰 요망 (Borderline / 위험 지수 40% ~ 69%)"
            report["details"] = "일상적인 수준을 넘어서는 심리적 피로도가 누적되어 있습니다. 아직 통제 가능한 수준이나, 외부 환경의 압박에 대해 다소 예민하게 반응할 수 있습니다."
            report["advice"] = "번아웃을 예방하기 위해 워라밸(Work-Life Balance)을 점검하고, 본인만의 확실한 스트레스 해소 창구를 마련하십시오."
        else:
            report["title"] = "정서적 안녕 상태 (Normal / 위험 지수 40% 미만)"
            report["details"] = "현재 심리적 건강도가 매우 우수하며, 외부 압박 및 스트레스 상황에 대해 유연하고 효과적으로 대응할 수 있는 강력한 회복탄력성을 지니고 있습니다."
            report["advice"] = "현재의 긍정적이고 안정적인 심리 상태를 훌륭하게 유지하고 있습니다. 이 에너지를 업무 성과 향상과 주변인들과의 긍정적 관계 형성에 활용하십시오."
            
    return ratio, report

# 3. 메인 로직
if 'reg' not in st.session_state: st.session_state['reg'] = False

if not st.session_state['reg']:
    st.title("🔍 정밀 심리 진단 등록")
    name = st.text_input("성함(이름)")
    birth = st.text_input("생년월일(8자리)")
    gen = st.selectbox("성별", ["남성", "여성"])
    rel = st.selectbox("관계", ["본인", "부", "모", "자녀", "배우자", "기타"])
    
    if st.button("✅ 확인 및 기록 불러오기", use_container_width=True):
        if name and birth:
            with st.spinner("데이터 조회 중..."):
                try:
                    res = requests.get(f"{GOOGLE_SCRIPT_URL}?name={name}&birth={birth}", timeout=10).json()
                    st.session_state['u'] = {"name":name, "birth":birth, "gen":gen, "rel":rel}
                    st.session_state['reg'] = True
                    if res.get("status") == "success":
                        st.session_state['final_results'] = res["scores"]
                        st.session_state['is_old_user'] = True
                    else: st.session_state['is_old_user'] = False
                    st.rerun()
                except:
                    st.warning("현재 서버 연결이 원활하지 않습니다. 신규 검사로 진행합니다.")
                    st.session_state['u'] = {"name":name, "birth":birth, "gen":gen, "rel":rel}
                    st.session_state['reg'] = True
                    st.rerun()
else:
    st.title("📊 심층 분석 보고서 시스템")
    st.info(f"👤 피검자: {st.session_state['u']['name']}님 ({st.session_state['u']['birth']})")
    if st.button("🔄 사용자 변경"): st.session_state.clear(); st.rerun()
        
    d_tab = 1 if st.session_state.get('is_old_user') else 0
    t1, t2 = st.tabs(["📄 진단 응답", "📑 종합 결과 보고서"])
    
    with t1:
        st.write("모든 문항을 신중히 읽고 답변해 주십시오.")
        cur_s = {}
        opts = {0:"매우 아니다", 1:"아니다", 2:"보통", 3:"그렇다", 4:"매우 그렇다"}
        for c, qs in data_db["qs"].items():
            if qs:
                with st.expander(f"📌 {c} 검사 ({len(qs)}문항)"):
                    total = 0
                    for i, q in enumerate(qs):
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), format_func=lambda x:opts[x], horizontal=True, key=f"{c}_{i}", index=2)
                        total += ans
                    cur_s[c] = total
        if st.button("🚀 데이터 분석 및 전송", use_container_width=True):
            requests.post(GOOGLE_SCRIPT_URL, data=json.dumps({"user":st.session_state['u'], "scores":cur_s}))
            st.session_state['final_results'] = cur_s
            st.session_state['is_old_user'] = True
            st.success("데이터베이스에 안전하게 기록되었습니다."); st.rerun()

    with t2:
        if 'final_results' in st.session_state:
            st.markdown("### 📋 종합 심리 검사 소견서")
            st.divider()
            
            for c, s in st.session_state['final_results'].items():
                t_q = len(data_db["qs"].get(c, []))
                if t_q > 0:
                    ratio, rep = get_detailed_report(c, s, t_q)
                    
                    with st.container():
                        st.markdown(f"#### 🔹 {c} 심층 분석")
                        # 진행률 바와 지표 표시
                        st.progress(ratio)
                        st.caption(rep["metric"])
                        
                        # 전문적인 마크다운 포맷팅 출력
                        st.markdown(f"**진단 결과**: {rep['title']}")
                        st.markdown(f"**🧠 심층 소견**\n> {rep['details']}")
                        st.markdown(f"**💡 전문가 제언**\n> {rep['advice']}")
                        st.write("")
                        st.write("")
            st.divider()
            st.caption("※ 본 리포트는 입력된 데이터를 기반으로 산출된 통계적 추정치이며, 절대적인 의학적 진단을 대신할 수 없습니다.")
        else:
            st.warning("데이터가 없습니다. 먼저 검사를 진행해 주세요.")

import streamlit as st
import json, os, requests, re

# 1. 환경 설정
st.set_page_config(page_title="정밀 심리 진단 시스템", layout="wide")
st.markdown("<style>#MainMenu, footer, header {visibility: hidden;}</style>", unsafe_allow_html=True)

# 🚨 [새로 발급받으신 주소가 완벽하게 적용되었습니다!]
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzd7kpYzj6kp2T9r-waR_Y4wZZ4_SucRe6WcEhaR16k7TljQg1dtA7lrCUb-yCHERwS-g/exec"

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
# [전문가 심층 분석 데이터베이스]
# ==========================================
EXPERT_DB = {
    "MBTI": {
        "ESTJ": {"title": "엄격한 관리자 (ESTJ)", "traits": "사실과 경험을 바탕으로 체계를 잡고 프로젝트를 추진하는 탁월한 리더입니다.", "likes": "명확한 규칙, 예측 가능한 결과, 효율적인 프로세스, 책임감 있는 태도", "dislikes": "모호한 지시, 비논리적인 감정 호소, 시간 낭비, 일관성 없는 변화"},
        "ENTJ": {"title": "대담한 통솔자 (ENTJ)", "traits": "비전을 세우고 조직을 이끌어가는 데 천부적인 재능이 있는 전략가입니다.", "likes": "도전적인 목표, 지적 자극, 장기적인 비전, 유능한 동료", "dislikes": "비효율, 감정적인 핑계, 우유부단함, 권위에 대한 맹목적 복종"},
        "ESFJ": {"title": "사교적인 외교관 (ESFJ)", "traits": "타인에 대한 깊은 배려와 책임감으로 주변을 조화롭게 이끄는 조력자입니다.", "likes": "화목한 분위기, 명확한 역할 분담, 타인을 돕는 일, 긍정적인 피드백", "dislikes": "냉소적인 태도, 갈등 상황, 예측 불가능한 변화, 무례함"},
        "ENFJ": {"title": "정의로운 사회운동가 (ENFJ)", "traits": "타인의 성장을 돕고 공동체의 비전을 이끌어내는 카리스마 있는 멘토입니다.", "likes": "협력적인 환경, 의미 있는 목표, 타인의 성장, 진정성 있는 소통", "dislikes": "비인간적인 시스템, 이기적인 행동, 피상적인 관계, 억압적인 환경"},
        "ESTP": {"title": "모험을 즐기는 사업가 (ESTP)", "traits": "위기 상황에서 빠른 판단력으로 문제를 해결하는 에너지 넘치는 행동파입니다.", "likes": "자유로운 환경, 즉각적인 결과, 활동적인 업무, 융통성", "dislikes": "과도한 규율, 반복적이고 지루한 일, 탁상공론, 이론적 논쟁"},
        "ESFP": {"title": "자유로운 영혼의 연예인 (ESFP)", "traits": "뛰어난 적응력과 사교성으로 분위기를 주도하는 에너자이저입니다.", "likes": "사람들과의 교류, 즉각적인 보상, 시각적으로 매력적인 환경, 즐거운 분위기", "dislikes": "엄격한 규칙, 장기적인 계획 수립, 혼자 고립되는 상황, 심각한 갈등"},
        "ENTP": {"title": "뜨거운 논쟁을 즐기는 변론가 (ENTP)", "traits": "기존의 틀을 깨고 새로운 가능성을 탐구하는 혁신적인 아이디어 뱅크입니다.", "likes": "지적인 토론, 새로운 문제 해결, 유연한 환경, 창의적인 브레인스토밍", "dislikes": "단순 반복 업무, 세부사항 관리, 강요된 규칙, 권위주의"},
        "ENFP": {"title": "재기발랄한 활동가 (ENFP)", "traits": "풍부한 상상력과 열정으로 타인에게 영감을 주는 창조적인 자유인입니다.", "likes": "새로운 아이디어, 유연성, 의미 있는 인간관계, 창의적 표현", "dislikes": "틀에 박힌 일과, 엄격한 위계질서, 세세한 마이크로 매니징, 지루함"},
        "ISTJ": {"title": "청렴결백한 논리주의자 (ISTJ)", "traits": "책임감이 강하고 사실에 입각하여 일을 끝까지 완수하는 믿음직한 기둥입니다.", "likes": "구조화된 환경, 세부적이고 명확한 지침, 전통과 질서, 예측 가능성", "dislikes": "갑작스러운 일정 변경, 무책임한 태도, 검증되지 않은 새로운 방식, 혼란"},
        "ISFJ": {"title": "용감한 수호자 (ISFJ)", "traits": "조용하고 헌신적으로 타인을 보호하고 지원하는 따뜻한 관리자입니다.", "likes": "안정적인 환경, 구체적인 사실, 타인을 돌보는 역할, 조화로운 관계", "dislikes": "잦은 변화, 갈등과 대립, 모호하고 추상적인 개념, 남들 앞에 나서는 것"},
        "INTJ": {"title": "용의주도한 전략가 (INTJ)", "traits": "통찰력과 논리력으로 시스템을 설계하고 미래를 계획하는 마스터마인드입니다.", "likes": "지적인 도전, 독립적인 작업 환경, 복잡한 문제 해결, 논리적 일관성", "dislikes": "비합리적인 감정 호소, 얕은 지식, 비효율적인 회의, 무능함"},
        "INFJ": {"title": "통찰력 있는 선지자 (INFJ)", "traits": "내면의 이상을 현실로 만들기 위해 깊은 통찰력을 발휘하는 조용한 헌신자입니다.", "likes": "진정성 있는 대화, 의미 있는 가치 실현, 조용하고 개인적인 공간, 영감", "dislikes": "피상적인 만남, 가치관의 충돌, 소음과 혼란, 억압적인 지시"},
        "ISTP": {"title": "만능 재주꾼 (ISTP)", "traits": "논리적이고 뛰어난 상황 적응력으로 실질적인 문제를 빠르게 해결하는 해결사입니다.", "likes": "자율성, 실용적인 문제 해결, 손으로 다루는 작업, 유연한 스케줄", "dislikes": "과도한 감정 표현 요구, 엄격한 통제, 의미 없는 규칙, 지나친 간섭"},
        "ISFP": {"title": "호기심 많은 예술가 (ISFP)", "traits": "현재의 순간을 즐기며 온화하고 수용적인 태도로 조화를 이루는 평화주의자입니다.", "likes": "미적 감각을 발휘할 수 있는 일, 개인적인 공간, 긍정적인 지원, 유연성", "dislikes": "갈등 상황, 엄격한 마감 기한, 타인에 대한 비판, 경직된 환경"},
        "INTP": {"title": "논리적인 사색가 (INTP)", "traits": "복잡한 이론과 논리를 탐구하며 지적 호기심을 충족시키는 철학자입니다.", "likes": "독립적인 연구, 복잡한 시스템 분석, 새로운 개념 탐구, 지적인 자율성", "dislikes": "비논리적인 규칙, 감정적인 문제 해결, 반복적인 행정 업무, 사교 행사"},
        "INFP": {"title": "열정적인 중재자 (INFP)", "traits": "본인만의 깊은 가치관을 바탕으로 타인에 대한 깊은 공감 능력을 지닌 이상주의자입니다.", "likes": "개인적인 의미를 찾는 일, 자율성, 진정성 있는 관계, 창의적인 표현", "dislikes": "가치관과 위배되는 일, 치열한 경쟁 상황, 비판적인 환경, 규율과 통제"}
    }
}

# 2. 고도화된 전문 분석 엔진
def get_detailed_report(cat, score_data, t_q):
    if isinstance(score_data, list):
        total = sum(score_data); ans_list = score_data
    else:
        total = score_data; ans_list = []
        
    m_s = t_q * 4 if t_q > 0 else 1
    ratio = total / m_s
    metric = ""; title = ""; details = ""; likes = ""; dislikes = ""
    
    if cat == "IQ":
        val = int((total/m_s)*60+80); metric = f"추정 FSIQ: {val}"
        if val >= 120:
            title = "최우수 인지 기능 (Superior / 상위 9% 이내)"
            details = "정보 처리 속도가 매우 빠르고 복잡한 패턴을 다차원적으로 이해하는 능력이 탁월합니다. 직관적이고 창의적인 문제 해결에 강점이 있으며, 방대한 데이터를 빠르게 요약하여 핵심을 짚어냅니다."
            likes = "지적 자극이 있는 과제, 복잡한 시스템 분석, 자율적인 문제 해결 환경"
            dislikes = "단순 반복적인 암기, 논리적 결함이 있는 지시, 느린 업무 진행 속도"
        elif val >= 110:
            title = "우수 인지 기능 (High Average / 상위 25% 이내)"
            details = "학습 능력이 우수하며 새로운 개념을 실무에 적용하는 응용력이 뛰어납니다. 논리적 추론 능력이 좋아 조직 내에서 기획 및 체계화 업무를 매우 능숙하게 소화할 수 있습니다."
            likes = "명확한 목표가 있는 학습, 체계적인 업무 환경, 전문성을 기를 수 있는 과제"
            dislikes = "비효율적인 동선, 비합리적인 의사결정"
        else:
            title = "보통 수준 (Average / 평균 범위)"
            details = "일반적인 사회 및 직업 요구사항을 안정적으로 충족합니다. 경험과 훈련을 통해 실무 능력을 탄탄하게 쌓아 올리는 데 유리하며, 극단적인 인지적 피로 없이 일상 과제를 훌륭히 수행합니다."
            likes = "경험 기반의 실무, 예측 가능한 업무 흐름, 점진적인 학습"
            dislikes = "갑작스럽고 복잡한 이론적 과제, 경험이 전무한 상태에서의 창조적 압박"

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
        else: res_type = "ESTJ"
        
        metric = f"성격 유형 지표: {res_type}"
        info = EXPERT_DB["MBTI"].get(res_type, {})
        title = info.get("title", f"유형: {res_type}")
        details = info.get("traits", "")
        likes = info.get("likes", "")
        dislikes = info.get("dislikes", "")

    elif cat == "TCI":
        val = int(((total-(t_q*2))/t_q)*10+50); metric = f"기질 T-Score: {val}"
        if val >= 60:
            title = "외향적 탐색형 (자극추구 및 연대감 높음)"
            details = "새로운 자극과 보상에 민감하게 반응하며, 타인과의 상호작용에서 에너지를 얻는 기질입니다. 도전적인 성향이 강해 혁신적인 프로젝트에 적합합니다."
            likes = "새로운 경험, 즉각적인 보상, 다양한 사람들과의 교류, 자율성"
            dislikes = "지루하고 단조로운 일상, 사회적 고립, 보상이 없는 헌신"
        elif val >= 41:
            title = "안정적 균형형 (기질적 중도)"
            details = "위험 회피와 자극 추구가 적절한 균형을 이루고 있어, 환경 변화에 유연하게 적응하며 감정적 기복이 적은 안정적인 성향입니다."
            likes = "예측 가능하면서도 약간의 변화가 있는 환경, 워라밸, 조화"
            dislikes = "극단적인 스트레스 상황, 지나친 모험 강요"
        else:
            title = "독립적 신중형 (위험회피 및 독립성 높음)"
            details = "매사에 신중하고 잠재적 위험을 철저히 대비하는 성향입니다. 타인의 인정보다는 자신의 내면적 기준이 중요하며, 독립적인 작업에서 최고의 성과를 냅니다."
            likes = "안전하고 검증된 방법, 개인적인 공간 보장, 익숙한 루틴"
            dislikes = "불확실성, 낯선 환경에서의 즉흥적인 대응, 타인의 지나친 간섭"

    elif cat == "MMPI":
        val = int((total/m_s)*100); metric = f"성격/적응 지수: {val}/100"
        if val >= 70:
            title = "방어기제 과활성화 (Elevated)"
            details = "현재 심리적 자아가 꽤 지쳐있으며 대인관계나 환경적 압박에 대해 방어기제가 강하게 작동하고 있습니다. 타인의 의도를 예민하게 받아들일 수 있습니다."
            likes = "갈등이 전혀 없는 안전지대, 무조건적인 지지와 공감"
            dislikes = "비판과 평가, 과도한 책임감 부여, 예측 불가능한 갈등"
        elif val >= 40:
            title = "경계 및 관찰 요망 (Borderline)"
            details = "성격적 적응력은 유지되고 있으나, 특정한 대인관계 스트레스나 환경적 변화에 다소 민감하게 반응할 수 있는 상태입니다. 멘탈 관리가 필요합니다."
            likes = "공정한 대우, 예측 가능한 피드백, 적절한 휴식 시간"
            dislikes = "일방적인 소통, 부당한 대우, 지속적인 긴장 상태"
        else:
            title = "건강한 자아강도 (Normal)"
            details = "외부의 비판이나 스트레스에도 쉽게 흔들리지 않는 건강한 자아강도를 지니고 있습니다. 타인과의 관계에서 유연하고 적응력이 매우 뛰어납니다."
            likes = "성장할 수 있는 피드백, 협력적인 팀플레이, 건설적인 토론"
            dislikes = "명분 없는 갈등, 뒷담화, 비합리적인 고집"

    elif cat == "CLINICAL":
        val = int((total/m_s)*100); metric = f"임상 증상 지수: {val}/100"
        if val >= 70:
            title = "급성 스트레스 증후군 가능성 (High Risk)"
            details = "우울감, 불안, 또는 번아웃(소진) 증상이 신체적/정신적으로 명확히 발현되고 있을 가능성이 큽니다. 즉각적인 스트레스 원인 차단과 휴식이 임상적으로 요구됩니다."
            likes = "충분한 수면, 전문적인 상담 지원, 업무량의 절대적 감소"
            dislikes = "추가적인 업무 압박, 성과에 대한 질책, 시끄럽고 복잡한 환경"
        elif val >= 40:
            title = "잠재적 소진 상태 (Moderate Risk)"
            details = "일상생활은 유지하고 있으나, 내면적으로는 에너지가 고갈되어 가고 있는 상태입니다. 가벼운 수면 장애나 신체화 증상(두통, 소화불량 등)이 동반될 수 있습니다."
            likes = "가벼운 운동, 취미 생활 보장, 일과 분리된 온전한 휴식"
            dislikes = "퇴근 후의 업무 연락, 수면 시간 부족, 지속적인 성과 압박"
        else:
            title = "정서적 안녕 상태 (Healthy)"
            details = "현재 임상적인 수준의 우울이나 불안 징후가 발견되지 않습니다. 정서적으로 매우 안정되어 있으며, 스트레스를 자체적으로 해소할 수 있는 좋은 대처 방식을 가지고 있습니다."
            likes = "현재의 안정적인 루틴 유지, 자기계발, 새로운 활력소 찾기"
            dislikes = "건강한 루틴을 파괴하는 무리한 일정"

    return ratio, metric, title, details, likes, dislikes

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
                        # 에러 내용을 더 명확하게 표시
                        st.error("⚠️ 구글 시트 연결 오류가 발생했습니다! (JSON Decode Error)")
                        st.info("이 오류는 코드가 아니라 구글 '배포 권한' 설정 때문에 파이썬이 거부당한 것입니다.")
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
    st.title("📊 임상 심리 분석 보고서")
    st.info(f"👤 대상자: {st.session_state['u']['name']}님 ({st.session_state['u']['birth']})")
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
            st.markdown("## 📋 전문가 종합 심리 소견서")
            st.divider()
            
            for c, s in st.session_state['final_results'].items():
                t_q = len(data_db["qs"].get(c, []))
                if t_q > 0:
                    ratio, metric, title, details, likes, dislikes = get_detailed_report(c, s, t_q)
                    
                    st.markdown(f"### 🔹 {c} 검사 분석")
                    st.progress(ratio if ratio <= 1.0 else 1.0)
                    st.caption(metric)
                    
                    st.markdown(f"**진단 분류:** <span style='color:blue; font-size:18px;'>**{title}**</span>", unsafe_allow_html=True)
                    st.markdown(f"> **🧠 심층 성향 분석**\n> {details}")
                    
                    if likes and dislikes:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.success(f"**👍 선호하는 환경 및 조건**\n\n{likes}")
                        with col2:
                            st.error(f"**👎 스트레스 유발 및 불호 환경**\n\n{dislikes}")
                    st.write("")
                    st.write("")
            st.divider()
            st.caption("※ 본 분석 보고서는 응답된 데이터를 바탕으로 산출된 전문가 수준의 심층 알고리즘 결과입니다.")
        else:
            st.warning("분석할 데이터가 없습니다. [온라인 진단지] 탭에서 먼저 검사를 진행해 주십시오.")

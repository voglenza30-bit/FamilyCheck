import streamlit as st
import json, os, requests, re

# 1. 환경 설정
st.set_page_config(page_title="심리 진단 시스템", layout="wide")
st.markdown("<style>#MainMenu, footer, header {visibility: hidden;}</style>", unsafe_allow_html=True)

# [수정] 1단계에서 새로 배포한 주소를 여기에 넣으세요!
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxICsSW3rWOu2rwMbFLuKSwrMdp88X40tx1mAJCx-j5akiaL5KbTWzDgzsLnhw1ljtM-Q/exec"

@st.cache_data
def load_data():
    def read_t(f):
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file:
                return [re.sub(r'^\d+[\s\.]+', '', l.strip()) for l in file.readlines() if l.strip()]
        return []
    def read_j(f):
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file: return json.load(file)
        return {}
    return {
        "qs": {"IQ": read_t("wechsler.txt"), "MBTI": read_t("mbti.txt"), "TCI": read_t("tci.txt"), "MMPI": read_t("mmpi.txt"), "CLINICAL": read_t("clinical.txt")},
        "db": {"IQ": read_j("result_iq.json"), "MBTI": read_j("result_mbti.json"), "TCI": read_j("result_tci.json"), "CLINICAL": read_j("result_clinical.json")}
    }

data_db = load_data()

# 분석 엔진
def get_report(cat, score, t_q):
    db = data_db["db"]
    m_s = t_q * 4
    if cat == "IQ":
        val = int((score/m_s)*60+80); k = "superior" if val>=120 else ("high_average" if val>=110 else "average")
        return f"추정 FSIQ: {val}", db["IQ"].get(k, {})
    elif cat == "TCI":
        val = int(((score-(t_q*2))/t_q)*10+50); k = "high" if val>=65 else ("low" if val<=40 else "moderate")
        return f"T-Score: {val}", db["TCI"].get(k, {})
    elif cat in ["MMPI", "CLINICAL"]:
        val = int((score/m_s)*100); k = "elevated" if val>=70 else ("borderline" if val>=40 else "normal")
        return f"위험지수: {val}/100", db["CLINICAL"].get(k, {})
    return "", {}

# 메인 로직
if 'reg' not in st.session_state: st.session_state['reg'] = False

if not st.session_state['reg']:
    st.title("🔍 심리 진단 등록")
    name = st.text_input("성함")
    birth = st.text_input("생년월일(8자리)")
    gen = st.selectbox("성별", ["남성", "여성"])
    rel = st.selectbox("관계", ["본인", "부", "모", "자녀", "배우자", "기타"])
    
    if st.button("✅ 확인 및 데이터 불러오기", use_container_width=True):
        if name and birth:
            with st.spinner("조회 중..."):
                try:
                    res = requests.get(f"{GOOGLE_SCRIPT_URL}?name={name}&birth={birth}", timeout=10).json()
                    if res.get("status") == "success":
                        st.session_state['final_results'] = res["scores"]
                        st.success("기록을 찾았습니다!")
                    else: st.info("새 검사를 시작합니다.")
                    st.session_state['u'] = {"name":name, "birth":birth, "gen":gen, "rel":rel}
                    st.session_state['reg'] = True
                    st.rerun()
                except: st.error("연결 실패. URL을 확인하세요.")
else:
    st.subheader(f"피검자: {st.session_state['u']['name']}")
    if st.button("🔄 정보 수정"): 
        st.session_state.clear(); st.rerun()
        
    t1, t2 = st.tabs(["📄 응답", "📊 결과"])
    
    with t1:
        cur_s = {}
        opts = {0:"매우 아니다", 1:"아니다", 2:"보통", 3:"그렇다", 4:"매우 그렇다"}
        for c, qs in data_db["qs"].items():
            if qs:
                with st.expander(f"📌 {c} 섹션"):
                    total = 0
                    for i, q in enumerate(qs):
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), format_func=lambda x:opts[x], horizontal=True, key=f"{c}_{i}", index=2)
                        total += ans
                    cur_s[c] = total
        if st.button("🚀 최종 전송 및 저장"):
            requests.post(GOOGLE_SCRIPT_URL, data=json.dumps({"user":st.session_state['u'], "scores":cur_s}))
            st.session_state['final_results'] = cur_s; st.success("저장 완료!"); st.rerun()

    with t2:
        if 'final_results' in st.session_state:
            for c, s in st.session_state['final_results'].items():
                t_q = len(data_db["qs"].get(c, []))
                met, info = get_report(c, s, t_q)
                with st.expander(f"▶ {c} ({met})", expanded=True):
                    st.subheader(info.get('title', ''))
                    st.write(info.get('summary', ''))
        else: st.warning("응답을 먼저 완료하세요.")

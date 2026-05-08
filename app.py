import streamlit as st
import json, os, requests, re

# 1. 페이지 설정 및 상단 메뉴 숨기기
st.set_page_config(page_title="가족 심리 진단 시스템", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebarNav"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

# [필수 확인] 새로 배포하신 구글 웹 앱 URL을 여기에 꼭 넣으세요!
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby3JW6E2Te8DtDS6WXBAEiMXwwh0XTNTNWi40vhApQ_ymBsTVMzqwsEE23A9leYo8nU6Q/exec"

@st.cache_data
def load_data():
    def read_t(f):
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file:
                # 번호 중복 방지 및 기호 정제
                return [re.sub(r'^\d+[\s\.]+', '', l.strip().replace('"', '')) for l in file.readlines() if l.strip()]
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

# 정밀 분석 엔진
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

# 메인 로직 시작
if 'reg' not in st.session_state: st.session_state['reg'] = False

# 등록 화면
if not st.session_state['reg']:
    st.title("🔍 심리 진단 시스템")
    with st.container():
        st.subheader("📋 피검자 정보 등록")
        name = st.text_input("성함(이름)")
        birth = st.text_input("생년월일(8자리)", placeholder="예: 19800101")
        col1, col2 = st.columns(2)
        with col1: gen = st.selectbox("성별", ["남성", "여성"])
        with col2: rel = st.selectbox("관계", ["본인", "부", "모", "자녀", "배우자", "기타"])
        
        st.divider()
        if st.button("✅ 확인 및 기록 불러오기", use_container_width=True):
            if name and birth:
                with st.spinner("구글 시트에서 데이터를 찾는 중..."):
                    try:
                        # 구글 시트에서 doGet 호출하여 데이터 가져오기
                        res = requests.get(f"{GOOGLE_SCRIPT_URL}?name={name}&birth={birth}", timeout=10).json()
                        if res.get("status") == "success":
                            st.session_state['final_results'] = res["scores"]
                            st.session_state['view_report'] = True
                            st.success(f"✅ {name}님의 이전 기록을 성공적으로 불러왔습니다!")
                        else:
                            st.info("새로운 검사를 시작합니다.")
                            st.session_state['view_report'] = False
                        
                        st.session_state['u'] = {"name":name, "birth":birth, "gen":gen, "rel":rel}
                        st.session_state['reg'] = True
                        st.rerun()
                    except:
                        st.error("구글 시트 연결에 실패했습니다. URL을 확인해주세요.")
            else:
                st.error("이름과 생년월일을 입력해주세요.")

# 검사 및 결과 화면
else:
    st.subheader(f"피검자: {st.session_state['u']['name']}님")
    if st.button("🔄 정보 수정 / 처음으로"):
        st.session_state.clear(); st.rerun()
        
    t1, t2 = st.tabs(["📄 진단 응답", "📊 결과 보고서"])
    
    with t1:
        st.info("문항 답변 후 하단의 '결과 전송' 버튼을 눌러주세요. (기본값은 '보통'입니다)")
        cur_s = {}
        opts = {0:"매우 아니다", 1:"아니다", 2:"보통", 3:"그렇다", 4:"매우 그렇다"}
        for c, qs in data_db["qs"].items():
            if qs:
                with st.expander(f"📌 {c} 섹션 ({len(qs)}문항)"):
                    total = 0
                    for i, q in enumerate(qs):
                        # 라디오 버튼 초기값은 2(보통)로 설정
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), 
                                       format_func=lambda x:opts[x], horizontal=True, key=f"{c}_{i}", index=2)
                        total += ans
                    cur_s[c] = total
        
        if st.button("🚀 검사 결과 최종 전송 및 저장", use_container_width=True):
            try:
                requests.post(GOOGLE_SCRIPT_URL, data=json.dumps({"user":st.session_state['u'], "scores":cur_s}))
                st.session_state['final_results'] = cur_s
                st.session_state['view_report'] = True
                st.success("데이터가 안전하게 저장되었습니다!")
                st.rerun()
            except:
                st.error("저장 중 오류가 발생했습니다.")

    with t2:
        if 'final_results' in st.session_state:
            res_data = st.session_state['final_results']
            for c, s in res_data.items():
                t_q = len(data_db["qs"].get(c, []))
                if t_q > 0:
                    met, info = get_report(c, s, t_q)
                    with st.expander(f"▶ {c} 분석 결과 ({met})", expanded=True):
                        st.subheader(info.get('title', '분석 결과'))
                        st.write(info.get('summary', '내용을 불러오는 중...'))
        else:
            st.warning("먼저 '진단 응답'을 완료하거나 기존 데이터를 불러와주세요.")

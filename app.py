import streamlit as st
import json, os, requests, re

# 1. 환경 설정
st.set_page_config(page_title="정밀 심리 진단 시스템", layout="wide")
st.markdown("<style>#MainMenu, footer, header {visibility: hidden;}</style>", unsafe_allow_html=True)

# [필수 확인] 배포하신 구글 웹 앱 URL
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxvYpP9t4OFqTJRhHWZL2-YhFkw9QjoIBUrLdevUH42uqKicdakSw7DfqzgBZjYNpS1pQ/exec
"

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

# 2. [핵심] 원본 JSON 파일 데이터와 MBTI 계산기 연동
def get_detailed_report(cat, score_data, t_q):
    db = data_db["db"]
    
    # 하위 호환성 (과거 총점 데이터 vs 현재 문항별 배열 데이터)
    if isinstance(score_data, list):
        total = sum(score_data)
        ans_list = score_data
    else:
        total = score_data
        ans_list = [] # 과거 데이터는 배열이 없음
        
    m_s = t_q * 4 if t_q > 0 else 1
    ratio = total / m_s
    
    metric = ""
    info = {}
    
    if cat == "IQ":
        val = int((total/m_s)*60+80)
        metric = f"추정 FSIQ: {val}"
        k = "superior" if val>=120 else ("high_average" if val>=110 else "average")
        info = db["IQ"].get(k, f"IQ {val}에 대한 원본 분석 내용이 파일에 없습니다.")
        
    elif cat == "MBTI":
        if ans_list and t_q > 0:
            # 16가지 MBTI 유형 정확도 계산 로직
            dims = [0, 0, 0, 0] # [E/I, S/N, T/F, J/P]
            for idx, a in enumerate(ans_list):
                dims[idx % 4] += a
            mid = (t_q / 4) * 2 # 차원별 중간값
            res_type = ""
            res_type += "I" if dims[0] < mid else "E"
            res_type += "S" if dims[1] < mid else "N"
            res_type += "T" if dims[2] < mid else "F"
            res_type += "J" if dims[3] < mid else "P"
        else:
            res_type = "ESTJ" # 과거 데이터 기본값 처리
            
        metric = f"MBTI 유형: {res_type}"
        info = db["MBTI"].get(res_type, f"MBTI {res_type}에 대한 상세 내용이 result_mbti.json 파일에 없습니다.")
        
    elif cat == "TCI":
        val = int(((total-(t_q*2))/t_q)*10+50)
        metric = f"T-Score: {val}"
        k = "high" if val>=65 else ("low" if val<=40 else "moderate")
        info = db["TCI"].get(k, f"TCI {k}에 대한 원본 분석 내용이 파일에 없습니다.")
        
    elif cat in ["MMPI", "CLINICAL"]:
        val = int((total/m_s)*100)
        metric = f"위험지수: {val}/100"
        k = "elevated" if val>=70 else ("borderline" if val>=40 else "normal")
        info = db["CLINICAL"].get(k, f"임상 {k} 지표에 대한 원본 분석 내용이 파일에 없습니다.")
        
    return ratio, metric, info

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
                    # [핵심] 총점이 아닌 "배열" 단위로 점수를 수집 (MBTI 계산을 위해 필수)
                    ans_array = []
                    for i, q in enumerate(qs):
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), format_func=lambda x:opts[x], horizontal=True, key=f"{c}_{i}", index=2)
                        ans_array.append(ans)
                    cur_s[c] = ans_array # 배열 자체를 저장
                    
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
                    ratio, metric, info = get_detailed_report(c, s, t_q)
                    
                    with st.container():
                        st.markdown(f"#### 🔹 {c} 분석")
                        st.progress(ratio if ratio <= 1.0 else 1.0)
                        st.caption(metric)
                        
                        # JSON 형태에 맞춘 강력한 텍스트 출력기
                        if isinstance(info, str):
                            st.write(info)
                        else:
                            st.markdown(f"**{info.get('title', '')}**")
                            st.write(info.get('summary', info.get('details', str(info))))
                        st.write("")
            st.divider()
            st.caption("※ 본 리포트는 입력된 데이터를 기반으로 산출된 통계적 추정치입니다.")
        else:
            st.warning("데이터가 없습니다. 먼저 검사를 진행해 주세요.")

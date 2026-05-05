import streamlit as st
import json
import os
import requests
import pandas as pd
import re

# 1. 페이지 설정 및 상단 메뉴 숨기기
st.set_page_config(page_title="가족 심리 진단 시스템 V2.4", layout="wide")
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            /* 사이드바 화살표 완전 제거 */
            [data-testid="stSidebarNav"] {display: none;}
            section[data-testid="stSidebar"] {display: none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# [필수] 박준우님의 구글 웹 앱 URL을 따옴표 안에 넣어주세요
GOOGLE_SCRIPT_URL = "여기에_복사한_웹앱_URL을_넣으세요"

# 2. 데이터 로드 로직
@st.cache_data
def load_data():
    def read_txt(file):
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                return [re.sub(r'^\d+[\s\.]+', '', l.strip()) for l in lines if l.strip()]
        return []
    def read_json(file):
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f: return json.load(f)
        return {}
    return {
        "questions": {
            "IQ": read_txt("wechsler.txt"), "MBTI": read_txt("mbti.txt"),
            "TCI": read_txt("tci.txt"), "MMPI": read_txt("mmpi.txt"),
            "CLINICAL": read_txt("clinical.txt")
        },
        "results_db": {
            "IQ": read_json("result_iq.json"), "MBTI": read_json("result_mbti.json"),
            "TCI": read_json("result_tci.json"), "CLINICAL": read_json("result_clinical.json")
        }
    }

db = load_data()

# 3. 메인 화면: 피검자 정보 등록 (사이드바 대신 메인에 배치)
st.title("🔍 정밀 심리 진단 시스템")

# 세션 상태 초기화
if 'user_registered' not in st.session_state:
    st.session_state['user_registered'] = False

# 등록 정보 컨테이너
if not st.session_state['user_registered']:
    with st.container():
        st.subheader("📋 피검자 정보 등록")
        u_name = st.text_input("성함(이름)", placeholder="성함을 입력하세요")
        u_birth = st.text_input("생년월일(8자리)", placeholder="예: 19800101")
        
        col1, col2 = st.columns(2)
        with col1:
            u_gender = st.selectbox("성별", ["남성", "여성"])
        with col2:
            u_rel = st.selectbox("관계", ["본인", "부", "모", "자녀", "남편", "아내", "기타"])
        
        st.divider()
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("✅ 정보 확인 및 검사 시작", use_container_width=True):
                if u_name and u_birth:
                    st.session_state['u_info'] = {"name": u_name, "birth": u_birth, "gender": u_gender, "rel": u_rel}
                    st.session_state['user_registered'] = True
                    st.rerun()
                else:
                    st.error("성함과 생년월일을 입력해주세요.")
        
        with btn_col2:
            # 불러오기 기능
            if u_name and u_birth:
                file_path = f"result_{u_name}_{u_birth}.json"
                if os.path.exists(file_path):
                    if st.button("💾 기존 기록 불러오기", use_container_width=True):
                        with open(file_path, "r", encoding="utf-8") as f:
                            saved_data = json.load(f)
                            st.session_state['u_info'] = {"name": u_name, "birth": u_birth, "gender": u_gender, "rel": u_rel}
                            st.session_state['scores_state'] = saved_data.get('scores', {})
                            st.session_state['final_results'] = saved_data.get('scores', {})
                            st.session_state['user_registered'] = True
                            st.rerun()

# 4. 검사 진행 및 리포트 화면
else:
    u = st.session_state['u_info']
    st.success(f"피검자: {u['name']} ({u['birth']}) - {u['rel']}")
    if st.button("🔄 정보 수정하기"):
        st.session_state['user_registered'] = False
        st.rerun()

    tab1, tab2 = st.tabs(["📄 진단 응답", "📊 결과 보고서"])
    
    with tab1:
        st.info("문항 답변 후 하단의 '결과 최종 전송' 버튼을 눌러주세요.")
        current_scores = {}
        opts = {0: "매우 아니다", 1: "아니다", 2: "보통이다", 3: "그렇다", 4: "매우 그렇다"}
        
        for cat, qs in db["questions"].items():
            if qs:
                with st.expander(f"📌 {cat} 검사 섹션 ({len(qs)}문항)"):
                    cat_total = 0
                    saved_val = st.session_state.get('scores_state', {}).get(cat, 0)
                    for i, q in enumerate(qs):
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), 
                                       format_func=lambda x: opts[x], horizontal=True, key=f"{cat}_{i}")
                        cat_total += ans
                    current_scores[cat] = cat_total

        if st.button("🚀 검사 결과 최종 전송 (저장)", use_container_width=True):
            payload = {"user": u, "scores": current_scores}
            st.session_state['final_results'] = current_scores
            try:
                requests.post(GOOGLE_SCRIPT_URL, data=json.dumps(payload), timeout=5)
                st.success("✅ 저장이 완료되었습니다!")
                st.balloons()
            except:
                st.info("ℹ️ 결과 보고서가 생성되었습니다.")

    with tab2:
        if 'final_results' in st.session_state:
            res = st.session_state['final_results']
            def analyze(cat, score, t_q):
                db_r = db["results_db"]
                m_s = t_q * 4
                if cat == "IQ":
                    f = int((score / m_s) * 60 + 80)
                    k = "superior" if f >= 120 else ("high_average" if f >= 110 else "average")
                    return f"추정 FSIQ: {f}", db_r["IQ"].get(k, {})
                elif cat == "TCI":
                    t = int(((score - (t_q * 2)) / t_q) * 10 + 50)
                    k = "high" if t >= 65 else ("low" if t <= 40 else "moderate")
                    return f"T-Score: {t}", db_r["TCI"].get(k, {})
                elif cat in ["MMPI", "CLINICAL"]:
                    r = score / m_s
                    k = "elevated" if r >= 0.7 else ("borderline" if r >= 0.4 else "normal")
                    return f"위험 지수: {int(r*100)}/100", db_r["CLINICAL"].get(k, {})
                return "", {}

            for cat, score in res.items():
                t_q = len(db["questions"][cat])
                metric, info = analyze(cat, score, t_q)
                with st.expander(f"▶ {cat} 지표 ({metric})", expanded=True):
                    if info:
                        st.subheader(info.get('title', ''))
                        st.write(info.get('summary', ''))
        else:
            st.warning("진단 응답을 완료해주세요.")

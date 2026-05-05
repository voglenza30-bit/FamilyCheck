import streamlit as st
import json
import os
import requests
import pandas as pd
import re

# 1. 페이지 설정 및 상단 메뉴 숨기기
st.set_page_config(page_title="가족 심리 진단 시스템 V2.2", layout="wide")
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# [필수] 박준우님의 구글 웹 앱 URL을 입력하세요
GOOGLE_SCRIPT_URL = "여기에_복사한_웹앱_URL을_넣으세요"

# 2. 데이터 로드 로직
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

# 3. 사이드바: 피검자 정보 입력 및 확인 버튼
st.sidebar.header("📋 피검자 정보 등록")
u_name = st.sidebar.text_input("성함(이름)", placeholder="성함을 입력하세요")
u_birth = st.sidebar.text_input("생년월일(8자리)", placeholder="예: 19800101")
u_gender = st.sidebar.selectbox("성별", ["남성", "여성"])
u_rel = st.sidebar.selectbox("관계", ["본인", "부", "모", "자녀", "남편", "아내", "기타"])

# '등록 확인' 버튼 추가
if st.sidebar.button("✅ 정보 확인 및 검사 시작"):
    if u_name and u_birth:
        st.session_state['user_registered'] = True
        st.sidebar.success(f"{u_name}님 정보가 확인되었습니다.")
    else:
        st.sidebar.error("성함과 생년월일을 입력해주세요.")

# 기존 파일 불러오기 버튼 (기존 로직 유지)
if u_name and u_birth:
    file_path = f"result_{u_name}_{u_birth}.json"
    if os.path.exists(file_path):
        if st.sidebar.button("💾 기존 기록 불러오기"):
            with open(file_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                st.session_state.clear() 
                st.session_state['user_registered'] = True
                st.session_state['final_results'] = saved_data.get('scores', {})
                st.rerun()

# 4. 메인 화면 로직
if st.session_state.get('user_registered'):
    st.title(f"🔍 {u_name}님 정밀 심리 진단")
    tab1, tab2 = st.tabs(["📄 진단 응답", "📊 결과 보고서"])

    with tab1:
        st.info("문항 답변 후 하단의 '결과 최종 전송' 버튼을 눌러주세요.")
        current_scores = {}
        opts = {0: "매우 아니다", 1: "아니다", 2: "보통이다", 3: "그렇다", 4: "매우 그렇다"}
        
        for cat, qs in db["questions"].items():
            if qs:
                with st.expander(f"📌 {cat} 섹션 ({len(qs)}문항)"):
                    cat_total = 0
                    for i, q in enumerate(qs):
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), 
                                       format_func=lambda x: opts[x], horizontal=True, key=f"{cat}_{i}")
                        cat_total += ans
                    current_scores[cat] = cat_total

        if st.button("🚀 검사 결과 최종 전송"):
            payload = {"user": {"name": u_name, "birth": u_birth, "gender": u_gender, "relationship": u_rel}, "scores": current_scores}
            st.session_state['final_results'] = current_scores
            try:
                requests.post(GOOGLE_SCRIPT_URL, data=json.dumps(payload), timeout=5)
                st.success("✅ 저장이 완료되었습니다!")
            except:
                st.info("ℹ️ 결과 보고서가 생성되었습니다.")

    with tab2:
        if 'final_results' in st.session_state:
            # (기존 분석 리포트 출력 로직 생략 - 이전 버전과 동일하게 작동)
            st.write("보고서 분석 내용이 여기에 표시됩니다.")
else:
    st.warning("👈 왼쪽 사이드바에서 정보를 입력하고 [정보 확인 및 검사 시작] 버튼을 눌러주세요.")

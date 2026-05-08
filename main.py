import streamlit as st
import json
import os
import requests
import pandas as pd
import re

# 1. 페이지 설정 및 상단 메뉴 숨기기
st.set_page_config(page_title="가족 심리 진단 시스템 V2.6", layout="wide")
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            [data-testid="stSidebarNav"] {display: none;}
            section[data-testid="stSidebar"] {display: none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# [필수] 박준우님의 구글 웹 앱 URL (배포된 URL)
GOOGLE_SCRIPT_URL = "여기에_복사한_웹앱_URL을_넣으세요"

# 2. 데이터 로드 로직
@st.cache_data
def load_data():
    def read_txt(file):
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                return [re.sub(r'^\d+[\s\.]+', '', l.strip()) for l in f.readlines() if l.strip()]
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

# 3. 구글 시트에서 데이터 가져오는 함수
def fetch_from_sheet(name, birth):
    try:
        # 구글 앱스 스크립트에 GET 요청을 보내 데이터를 가져옵니다.
        # (구글 앱스 스크립트 쪽에 doGet 함수 설정이 필요합니다)
        response = requests.get(f"{GOOGLE_SCRIPT_URL}?name={name}&birth={birth}", timeout=10)
        if response.status_code == 200:
            return response.json() # 점수 데이터 반환
    except:
        return None
    return None

# 4. 메인 화면: 등록 및 자동 불러오기
st.title("🔍 정밀 심리 진단 시스템")

if 'user_registered' not in st.session_state:
    st.session_state['user_registered'] = False

if not st.session_state['user_registered']:
    with st.container():
        st.subheader("📋 피검자 정보 등록")
        u_name = st.text_input("성함(이름)", placeholder="성함을 입력하세요")
        u_birth = st.text_input("생년월일(8자리)", placeholder="예: 19800101")
        col1, col2 = st.columns(2)
        with col1: u_gender = st.selectbox("성별", ["남성", "여성"])
        with col2: u_rel = st.selectbox("관계", ["본인", "부", "모", "자녀", "남편", "아내", "기타"])
        
        if st.button("🚀 정보 확인 및 기존 기록 불러오기", use_container_width=True):
            if u_name and u_birth:
                with st.spinner('기존 기록을 조회 중입니다...'):
                    # 구글 시트에서 데이터 조회 시도
                    sheet_data = fetch_from_sheet(u_name, u_birth)
                    
                    st.session_state['u_info'] = {"name": u_name, "birth": u_birth, "gender": u_gender, "rel": u_rel}
                    st.session_state['user_registered'] = True
                    
                    if sheet_data and 'scores' in sheet_data:
                        st.session_state['final_results'] = sheet_data['scores']
                        st.success(f"✅ {u_name}님의 이전 검사 결과를 불러왔습니다!")
                    else:
                        st.info("새로운 검사를 시작합니다.")
                    st.rerun()
            else:
                st.error("이름과 생년월일을 입력해주세요.")

# 5. 검사 및 리포트 화면 (이하 로직 동일)
# ... [생략: 이전 버전의 검사 및 리포트 탭 로직] ...

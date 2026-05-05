import streamlit as st
import json
import os
import requests
import pandas as pd
import re

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="가족 심리 진단 시스템 V2.5", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebarNav"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

GOOGLE_SCRIPT_URL = "여기에_복사한_웹앱_URL을_넣으세요"

# 2. 데이터 로드 (캐시 적용으로 속도 향상)
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

# 3. 메인 화면: 정보 등록 및 불러오기
st.title("🔍 정밀 심리 진단 시스템")

if 'user_registered' not in st.session_state:
    st.session_state['user_registered'] = False
if 'temp_scores' not in st.session_state:
    st.session_state['temp_scores'] = {}

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
            if st.button("✅ 새 검사 시작", use_container_width=True):
                if u_name and u_birth:
                    st.session_state['u_info'] = {"name": u_name, "birth": u_birth, "gender": u_gender, "rel": u_rel}
                    st.session_state['user_registered'] = True
                    st.rerun()
                else:
                    st.error("성함과 생년월일을 입력해주세요.")
        
        with btn_col2:
            # [기능 강화] 기존 파일이 있으면 버튼 노출 및 데이터 복구
            if u_name and u_birth:
                file_path = f"result_{u_name}_{u_birth}.json"
                if os.path.exists(file_path):
                    if st.button("💾 중단된 기록 불러오기", use_container_width=True):
                        with open(file_path, "r", encoding="utf-8") as f:
                            saved_data = json.load(f)
                            # 1. 기본 정보 복구
                            st.session_state['u_info'] = {"name": u_name, "birth": u_birth, "gender": u_gender, "rel": u_rel}
                            # 2. 개별 문항 응답 데이터(raw_responses) 복구
                            st.session_state['temp_scores'] = saved_data.get('raw_responses', {})
                            # 3. 합산 점수 복구
                            st.session_state['scores_state'] = saved_data.get('scores', {})
                            st.session_state['user_registered'] = True
                            st.success("데이터를 성공적으로 복구했습니다!")
                            st.rerun()

# 4. 검사 진행 화면
else:
    u = st.session_state['u_info']
    st.success(f"피검자: {u['name']} ({u['birth']}) - {u['rel']}")
    
    tab1, tab2 = st.tabs(["📄 진단 응답", "📊 결과 보고서"])
    
    with tab1:
        st.info("이전에 답변한 내용은 자동으로 선택되어 있습니다. 마저 진행해주세요.")
        current_scores = {}
        # 각 문항의 개별 응답을 저장할 딕셔너리
        raw_responses = st.session_state.get('temp_scores', {})
        
        opts = {0: "매우 아니다", 1: "아니다", 2: "보통이다", 3: "그렇다", 4: "매우 그렇다"}
        
        for cat, qs in db["questions"].items():
            if qs:
                with st.expander(f"📌 {cat} 섹션 ({len(qs)}문항)"):
                    cat_total = 0
                    for i, q in enumerate(qs):
                        # [핵심] 저장된 개별 응답이 있다면 불러오고, 없으면 기본값(0)
                        key_name = f"{cat}_{i}"
                        default_val = raw_responses.get(key_name, 0)
                        
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), 
                                       index=default_val, # 복구된 값을 인덱스로 설정
                                       format_func=lambda x: opts[x], horizontal=True, key=key_name)
                        
                        # 실시간으로 응답 저장
                        raw_responses[key_name] = ans
                        cat_total += ans
                    current_scores[cat] = cat_total

        if st.button("🚀 검사 완료 및 최종 전송", use_container_width=True):
            # 전송 시 개별 문항 응답(raw_responses)도 함께 저장하여 나중에 불러올 수 있게 함
            payload = {
                "user": u, 
                "scores": current_scores, 
                "raw_responses": raw_responses
            }
            st.session_state['final_results'] = current_scores
            try:
                requests.post(GOOGLE_SCRIPT_URL, data=json.dumps(payload), timeout=5)
                st.success("✅ 저장이 완료되었습니다!")
                # 중간 기록 파일 업데이트 (서버 파일 시스템에 저장)
                file_name = f"result_{u['name']}_{u['birth']}.json"
                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=4)
            except:
                st.info("보고서가 생성되었습니다.")

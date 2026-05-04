import streamlit as st
import json
import os
import requests
import pandas as pd
import re

# 페이지 설정
st.set_page_config(page_title="가족 심리 진단 시스템 V2.1", layout="wide")

# [필수] 박준우님의 구글 웹 앱 URL을 따옴표 안에 꼭 넣어주세요
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbygBHnEGI0lfKX1jWkKHy9o4CHc-MiyfsqzEhRVPdzWDOdtOd31xbaQNIFwd_2rJy0YPA/exec"

# 1. 데이터 로드 로직
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

# 2. 정밀 분석 엔진 (점수 기반 리포트 생성)
def analyze_result(category, score, total_q):
    res_db = db["results_db"]
    max_score = total_q * 4
    if category == "IQ":
        fsiq = int((score / max_score) * 60 + 80)
        key = "superior" if fsiq >= 120 else ("high_average" if fsiq >= 110 else "average")
        return f"추정 FSIQ: {fsiq}", res_db["IQ"].get(key, {})
    elif category == "TCI":
        t_score = int(((score - (total_q * 2)) / total_q) * 10 + 50)
        key = "high" if t_score >= 65 else ("low" if t_score <= 40 else "moderate")
        return f"T-Score: {t_score}", res_db["TCI"].get(key, {})
    elif category in ["MMPI", "CLINICAL"]:
        ratio = score / max_score
        key = "elevated" if ratio >= 0.7 else ("borderline" if ratio >= 0.4 else "normal")
        return f"위험 지수: {int(ratio*100)}/100", res_db["CLINICAL"].get(key, {})
    return "", {}

# 3. 사이드바: 피검자 등록
st.sidebar.header("📋 피검자 등록")
user_name = st.sidebar.text_input("성함(이름)", value="", placeholder="성함을 입력하세요")
user_birth = st.sidebar.text_input("생년월일(8자리)", value="", placeholder="예: 19800101")
user_gender = st.sidebar.selectbox("성별 선택", ["남성", "여성"])
user_rel = st.sidebar.selectbox("검사자와의 관계", ["본인", "부", "모", "자녀", "남편", "아내", "기타"])

# [개선] 기존 파일 불러오기 및 데이터 강제 주입
if user_name and user_birth:
    file_path = f"result_{user_name}_{user_birth}.json"
    if os.path.exists(file_path):
        st.sidebar.success(f"✅ {user_name}님의 기록을 찾았습니다.")
        if st.sidebar.button("💾 기존 데이터 불러오기"):
            with open(file_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                # 세션 데이터 초기화 후 강제 주입
                st.session_state.clear() 
                st.session_state['scores_state'] = saved_data.get('scores', {})
                st.session_state['final_results'] = saved_data.get('scores', {})
                # 강제 재실행을 유도하여 데이터 반영
                st.rerun()

# 4. 메인 화면
if user_name and user_birth:
    st.title(f"🔍 {user_name}님 정밀 심리 진단")
    
    # 탭 구성
    tab1, tab2 = st.tabs(["📄 진단 응답", "📊 결과 보고서"])

    with tab1:
        st.info("문항 답변 후 하단의 '결과 최종 전송' 버튼을 눌러주세요.")
        current_scores = {}
        opts = {0: "매우 아니다", 1: "아니다", 2: "보통이다", 3: "그렇다", 4: "매우 그렇다"}
        
        for cat, qs in db["questions"].items():
            if qs:
                with st.expander(f"📌 {cat} 검사 섹션 ({len(qs)}문항)"):
                    cat_total = 0
                    # 불러온 값이 세션에 있으면 반영
                    saved_val = st.session_state.get('scores_state', {}).get(cat, 0)
                    for i, q in enumerate(qs):
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), 
                                       format_func=lambda x: opts[x], horizontal=True, key=f"{cat}_{i}")
                        cat_total += ans
                    current_scores[cat] = cat_total

        if st.button("🚀 검사 결과 최종 전송 (구글 시트 저장)"):
            payload = {
                "user": {"name": user_name, "birth": user_birth, "gender": user_gender, "relationship": user_rel},
                "scores": current_scores
            }
            st.session_state['final_results'] = current_scores
            try:
                requests.post(GOOGLE_SCRIPT_URL, data=json.dumps(payload), timeout=5)
                st.success("✅ 구글 시트 저장 성공!")
                st.balloons()
            except:
                st.info("ℹ️ 시트 기록 지연 중입니다. 리포트는 즉시 확인 가능합니다.")

    with tab2:
        # final_results가 세션에 있는 경우에만 리포트 출력
        if 'final_results' in st.session_state:
            res = st.session_state['final_results']
            for cat, score in res.items():
                total_q = len(db["questions"][cat])
                metric, info = analyze_result(cat, score, total_q)
                with st.expander(f"▶ {cat} 지표 ({metric})", expanded=True):
                    if info:
                        st.subheader(info.get('title', '분석 결과'))
                        st.write(info.get('summary', ''))
        else:
            st.warning("먼저 '진단 응답'을 완료하거나 사이드바에서 기존 데이터를 불러와주세요.")
else:
    st.warning("👈 왼쪽 사이드바에 검사 정보를 입력하세요.")

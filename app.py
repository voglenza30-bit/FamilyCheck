import streamlit as st
import json
import os
import requests
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="가족 심리 진단 시스템 V1.5", layout="wide")

# [중요] 구글 앱스 스크립트 URL을 여기에 꼭 넣어주세요!
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz7vxzdbiYD9IcueXd8GZAmfRr7_WCwYlRwNudbD_O25HXxWbbF5C-afxMOzyFI8OhqDQ/exec"

# 1. 데이터 로드 로직
def load_data():
    def read_txt(file):
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                return [l.strip() for l in f.readlines() if l.strip()]
        return []
    def read_json(file):
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
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

# 2. 정밀 분석 엔진
def analyze_result(category, score, total_q):
    res_db = db["results_db"]
    if category == "IQ":
        fsiq = int((score / (total_q * 4)) * 60 + 80)
        key = "superior" if fsiq >= 120 else ("high_average" if fsiq >= 110 else "average")
        return f"추정 FSIQ: {fsiq}", res_db["IQ"].get(key, {})
    elif category == "TCI":
        t_score = int(((score - (total_q * 2)) / (total_q)) * 10 + 50)
        key = "high" if t_score >= 65 else ("low" if t_score <= 40 else "moderate")
        return f"T-Score: {t_score}", res_db["TCI"].get(key, {})
    elif category in ["MMPI", "CLINICAL"]:
        ratio = score / total_q
        key = "elevated" if ratio >= 0.7 else ("borderline" if ratio >= 0.4 else "normal")
        return f"위험 지수: {int(ratio*100)}/100", res_db["CLINICAL"].get(key, {})
    return "", {}

# 3. 사이드바: 피검자 정보 및 불러오기
st.sidebar.header("📋 피검자 등록")
user_name = st.sidebar.text_input("성함(이름)", placeholder="박준우")
user_birth = st.sidebar.text_input("생년월일(8자리)", placeholder="19780731")
user_gender = st.sidebar.selectbox("성별 선택", ["남성", "女性"])

# [복구] 기존 파일 불러오기 로직
file_path = f"result_{user_name}_{user_birth}.json"
if user_name and user_birth and os.path.exists(file_path):
    st.sidebar.success("기존 기록을 찾았습니다.")
    if st.sidebar.button("💾 이전 기록 불러오기"):
        with open(file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            st.session_state['scores_state'] = saved_data.get('scores', {})
            st.sidebar.info("데이터 로드 완료!")

# 4. 메인 화면
if user_name and user_birth:
    st.title(f"🔍 {user_name}님 정밀 심리 진단")
    tab1, tab2 = st.tabs(["📄 진단 응답", "📊 결과 보고서"])

    if 'scores_state' not in st.session_state:
        st.session_state['scores_state'] = {}

    with tab1:
        st.info("문항 응답 후 하단의 '최종 전송' 버튼을 꼭 눌러주세요.")
        current_scores = {}
        for cat, qs in db["questions"].items():
            if qs:
                with st.expander(f"📌 {cat} 검사 섹션"):
                    cat_total = 0
                    opts = {0: "아니오", 1: "예"} if cat in ["MMPI", "CLINICAL"] else {0: "전혀 안그럼", 1: "안그럼", 2: "보통", 3: "그럼", 4: "매우 그럼"}
                    
                    # 불러온 값이 있으면 반영
                    saved_val = st.session_state['scores_state'].get(cat, 0)
                    for i, q in enumerate(qs):
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), format_func=lambda x: opts[x], horizontal=True, key=f"{cat}_{i}")
                        cat_total += ans
                    current_scores[cat] = cat_total

        # [저장 및 전송]
        if st.button("🚀 검사 결과 최종 전송 (구글 시트로 저장)"):
            payload = {
                "user": {"name": user_name, "birth": user_birth, "gender": user_gender},
                "scores": current_scores
            }
            try:
                response = requests.post(GOOGLE_SCRIPT_URL, data=json.dumps(payload))
                if response.status_code == 200:
                    st.success("✅ 구글 시트에 안전하게 기록되었습니다!")
                    st.session_state['final_results'] = current_scores
                    st.balloons()
                else:
                    st.warning("시트 전송엔 실패했지만 결과는 아래 탭에서 확인 가능합니다.")
            except:
                st.error("연결 오류가 발생했습니다.")

    with tab2:
        if 'final_results' in st.session_state:
            res = st.session_state['final_results']
            for cat, score in res.items():
                total_q = len(db["questions"][cat])
                metric, data = analyze_result(cat, score, total_q)
                with st.expander(f"▶ {cat} 지표 ({metric})", expanded=True):
                    if data:
                        st.subheader(data.get('title', '분석 중'))
                        st.write(data.get('summary', ''))
        else:
            st.warning("먼저 '진단 응답' 완료 후 전송 버튼을 눌러주세요.")
else:
    st.warning("👈 왼쪽 사이드바에 정보를 입력하세요.")

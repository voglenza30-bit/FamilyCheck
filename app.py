import streamlit as st
import json
import os
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="가족 심리 진단 시스템", layout="wide")

# 1. 데이터 로드 로직 (V45.9/46.0 데이터베이스 계승)
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

# 3. 사이드바: 피검자 정보 입력 및 불러오기
st.sidebar.header("📋 피검자 정보 등록")
user_name = st.sidebar.text_input("성함(이름)", placeholder="예: 홍길동")
user_birth = st.sidebar.text_input("생년월일(8자리)", placeholder="예: 19800101")
user_gender = st.sidebar.selectbox("성별 선택", ["남성", "여성"])
user_rel = st.sidebar.text_input("검사자와의 관계", placeholder="예: 본인, 부, 모")

# [핵심] 기존 데이터 불러오기 기능
file_path = f"result_{user_name}_{user_birth}.json"
load_success = False

if user_name and user_birth and os.path.exists(file_path):
    st.sidebar.info("기존 검사 기록이 있습니다.")
    if st.sidebar.button("💾 이전 기록 불러오기"):
        with open(file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            st.session_state['scores_state'] = saved_data.get('scores', {})
            st.sidebar.success("데이터를 불러왔습니다!")
            load_success = True

# 4. 메인 화면 구성
if user_name and user_birth:
    st.title(f"🔍 {user_name}님 종합 심리 진단")
    tab1, tab2 = st.tabs(["📄 진단 문항 응답", "📊 분석 결과 리포트"])

    # 초기 상태 설정
    if 'scores_state' not in st.session_state:
        st.session_state['scores_state'] = {}

    with tab1:
        st.info("각 섹션을 눌러 검사를 진행하세요. '중간 저장'을 하면 나중에 이어서 할 수 있습니다.")
        
        current_scores = {}
        for cat, qs in db["questions"].items():
            if qs:
                with st.expander(f"📌 {cat} 검사 섹션 ({len(qs)}문항)"):
                    cat_total = 0
                    opts = {0: "아니오", 1: "예"} if cat in ["MMPI", "CLINICAL"] else {0: "전혀 안그럼", 1: "안그럼", 2: "보통", 3: "그럼", 4: "매우 그럼"}
                    
                    # 저장된 값이 있으면 해당 값을 기본값으로 사용
                    saved_cat_score = st.session_state['scores_state'].get(cat, 0)
                    
                    for i, q in enumerate(qs):
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), 
                                       format_func=lambda x: opts[x], horizontal=True, key=f"{cat}_{i}_{user_name}")
                        cat_total += ans
                    current_scores[cat] = cat_total

        # 저장 및 분석 버튼
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 현재까지 내용 중간 저장"):
                save_payload = {
                    "user": {"name": user_name, "birth": user_birth, "gender": user_gender, "rel": user_rel},
                    "scores": current_scores,
                    "date": str(pd.Timestamp.now())
                }
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(save_payload, f, ensure_ascii=False, indent=4)
                st.success("진행 상황이 서버에 저장되었습니다. 나중에 이어서 하실 수 있습니다.")
        
        with col2:
            if st.button("🏁 최종 제출 및 분석 완료"):
                st.session_state['final_results'] = current_scores
                st.balloons()
                st.success("분석이 완료되었습니다! '분석 결과 리포트' 탭을 확인하세요.")

    with tab2:
        if 'final_results' in st.session_state:
            st.header(f"📋 {user_name}님 정밀 분석 보고서")
            res = st.session_state['final_results']
            for cat, score in res.items():
                total_q = len(db["questions"][cat])
                metric, data = analyze_result(cat, score, total_q)
                with st.expander(f"▶ {cat} 지표 분석 ({metric})", expanded=True):
                    if data:
                        st.subheader(data.get('title', '분석 중'))
                        st.write(f"_{data.get('summary', '')}_")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write("**[주요 특징]**")
                            for f in data.get('features', []): st.write(f"- {f}")
                        with c2:
                            st.write("**[핵심 강점]**")
                            for s in data.get('strengths', []): st.write(f"- {s}")
                        st.warning("**[주의 및 보완점]**\n" + "\n".join([f"- {c}" for c in data.get('cautions', [])]))
                    st.divider()
        else:
            st.warning("먼저 검사를 완료하고 '최종 제출' 버튼을 눌러주세요.")
else:
    st.warning("👈 왼쪽 사이드바에 정보를 입력하시면 검사가 시작됩니다.")
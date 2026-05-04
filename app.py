import streamlit as st
import json
import os
import pandas as pd

# 페이지 설정 및 테마
st.set_page_config(page_title="가족 심리 진단 시스템", layout="wide")

# 1. 데이터 로드 로직 (질문지 및 결과 DB)[cite: 3, 4, 5, 8, 9, 10]
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

# 2. 정밀 분석 엔진[cite: 6, 8, 9, 10]
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

# 3. 사이드바: 피검자 정보 입력창 레이아웃 수정[cite: 6, 7]
st.sidebar.header("📋 피검자 정보 등록")
user_name = st.sidebar.text_input("성함(이름)", placeholder="예: 홍길동")
user_birth = st.sidebar.text_input("생년월일(8자리)", placeholder="예: 19800101")
user_gender = st.sidebar.selectbox("성별 선택", ["남성", "여성"])
user_rel = st.sidebar.text_input("검사자와의 관계", placeholder="예: 본인, 부, 모")

# 4. 메인 화면 구성
if user_name and user_birth:
    st.title(f"🔍 {user_name}님 종합 심리 진단 시스템")
    tab1, tab2 = st.tabs(["📄 진단 문항 응답", "📊 분석 결과 리포트"])

    with tab1:
        st.info("모든 문항을 읽고 본인의 평소 모습과 가장 일치하는 항목을 선택해 주세요.")
        all_scores = {}
        
        for cat, qs in db["questions"].items():
            if qs:
                with st.expander(f"📌 {cat} 검사 섹션 ({len(qs)}문항)"):
                    cat_total = 0
                    # 검사 성격별 답변 라벨 최적화
                    if cat in ["MMPI", "CLINICAL"]:
                        opts = {0: "아니오", 1: "예"}
                    else:
                        opts = {0: "전혀 안그럼", 1: "안그럼", 2: "보통", 3: "그럼", 4: "매우 그럼"}
                    
                    for i, q in enumerate(qs):
                        ans = st.radio(f"{i+1}. {q}", options=list(opts.keys()), 
                                       format_func=lambda x: opts[x], horizontal=True, key=f"{cat}_{i}")
                        cat_total += ans
                    all_scores[cat] = cat_total

        # 데이터 저장 버튼 추가[cite: 6, 7]
        if st.button("💾 검사 결과 서버 저장 및 분석 실행"):
            st.session_state['final_results'] = all_scores
            save_payload = {
                "user": {"name": user_name, "birth": user_birth, "gender": user_gender, "rel": user_rel},
                "scores": all_scores,
                "date": str(pd.Timestamp.now())
            }
            # 서버 폴더에 JSON 파일로 영구 저장
            file_path = f"result_{user_name}_{user_birth}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(save_payload, f, ensure_ascii=False, indent=4)
            st.success(f"✅ {user_name}님의 데이터가 서버에 성공적으로 저장되었습니다! '분석 결과 리포트' 탭에서 결과를 확인하세요.")

    with tab2:
        if 'final_results' in st.session_state:
            st.header(f"📋 {user_name}님 정밀 분석 보고서")
            res = st.session_state['final_results']
            
            for cat, score in res.items():
                total_q = len(db["questions"][cat])
                metric, data = analyze_result(cat, score, total_q)
                
                with st.expander(f"▶ {cat} 지표 상세 분석 ({metric})", expanded=True):
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
            st.warning("먼저 '진단 문항 응답' 탭에서 검사를 완료하고 저장 버튼을 눌러주세요.")
else:
    st.warning("👈 왼쪽 사이드바에 피검자 정보를 입력하시면 검사가 시작됩니다.")
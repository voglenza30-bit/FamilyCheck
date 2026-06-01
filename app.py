import streamlit as st
import json, os, requests, re
import numpy as np
from PIL import Image
import streamlit.components.v1 as components
import google.generativeai as genai
from streamlit_drawable_canvas import st_canvas

# =============================================
# 1. 페이지 설정
# =============================================
st.set_page_config(
    page_title="정밀 심리 진단 시스템 4.0",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# 2. Gemini API 세팅
# =============================================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_resource
def get_model():
    candidates = [
        "gemini-3.5-flash",
        "gemini-3.1-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-preview",
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]
    for name in candidates:
        try:
            m = genai.GenerativeModel(name)
            m.generate_content("ok", generation_config={"max_output_tokens": 1})
            return m, name
        except Exception:
            continue
    raise RuntimeError("Gemini 모델 연결 실패. API 키와 모델 접근 권한을 확인해 주세요.")

model, _model_name = get_model()

# =============================================
# 3. 전체 스타일링 (CSS)
# =============================================
st.markdown("""
<style>
@media print {
    .stButton, .stDownloadButton { display: none !important; }
    .main { background-color: white !important; padding: 0 !important; }
}
[data-testid="stSidebar"] { display: flex !important; }

.t-score-bar { background-color: #e2e8f0; border-radius: 6px; height: 28px; width: 100%; position: relative; margin-bottom: 12px; overflow: hidden; }
.t-score-fill { height: 100%; border-radius: 6px; color: white; display: flex; align-items: center; justify-content: flex-end; padding-right: 12px; font-size: 13px; font-weight: bold; }
.report-header { background: linear-gradient(135deg, #005088 0%, #0077cc 100%); color: white; padding: 28px 32px; border-radius: 12px; margin-bottom: 28px; }
.badge { display: inline-block; padding: 3px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-right: 6px; }
.badge-normal  { background: #d1fae5; color: #065f46; }
.badge-caution { background: #fef3c7; color: #92400e; }
.badge-high    { background: #fee2e2; color: #991b1b; }
.score-card { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.score-card .score-val { font-size: 2.2rem; font-weight: bold; color: #005088; }
.score-card .score-label { font-size: 0.8rem; color: #64748b; margin-top: 4px; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwOXsbz1hKT_dPN6pJDn6QAlEginqXIOLBXiFZtV2kKffbZekvMVOIg1LZ19h4dV0Lyjw/exec"

# =============================================
# 4. 데이터 로드 
# =============================================
@st.cache_data
def load_data():
    def read_t(f):
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file:
                return [re.sub(r'^\d+[\s\.]+', '', l.strip()) for l in file if l.strip()]
        return []
    return {
        "qs": {
            "IQ":       read_t("wechsler.txt"),
            "MBTI":     read_t("mbti.txt"),
            "TCI":      read_t("tci.txt"),
            "MMPI":     read_t("mmpi.txt"),
            "CLINICAL": read_t("clinical.txt"),
        },
        "sct_starts": [
            "나의 아버지는 ", "내가 가장 행복할 때는 ", "나의 장래는 ", "나를 가장 화나게 하는 것은 ", "내 생각에 참다운 친구란 ", 
            "내가 어렸을 때는 ", "나의 어머니는 ", "내가 가장 두려워하는 것은 ", "무슨 일을 해서라도 잊고 싶은 것은 ", 
            "다른 사람들이 나를 ", "내가 바라는 이상적인 나는 ", "나에게 가장 힘들었던 경험은 "
        ]
    }
db = load_data()

# =============================================
# 5. UI 렌더링 유틸리티 함수
# =============================================
def t_score_html(label, raw_score, max_possible, color="#005088", description=""):
    ratio = raw_score / max_possible if max_possible > 0 else 0
    t_val = max(30, min(80, int(ratio * 40 + 30)))
    bar_pct = (t_val - 30) / 50 * 100  

    if t_val < 45: level = "낮음"; badge_class = "badge-normal"
    elif t_val < 60: level = "정상"; badge_class = "badge-normal"
    elif t_val < 65: level = "경계"; badge_class = "badge-caution"
    else: level = "높음"; badge_class = "badge-high"

    return f"""
    <div style="margin-bottom:18px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-weight:600; color:#1e293b; font-size:14px;">{label}</span>
            <div>
                <span class="badge {badge_class}">{level}</span>
                <span style="font-weight:bold; color:{color}; font-size:15px;">T-{t_val}</span>
            </div>
        </div>
        <div class="t-score-bar">
            <div class="t-score-fill" style="width:{bar_pct:.1f}%; background-color:{color};">{raw_score}점</div>
        </div>
        <div style="font-size:11px; color:#64748b;">{description}</div>
    </div>
    """

def iq_score_html(label, iq_score, color="#005088", description=""):
    if iq_score >= 120: level = "최우수"; badge_class = "badge-normal"
    elif iq_score >= 110: level = "우수"; badge_class = "badge-normal"
    elif iq_score >= 90: level = "평균"; badge_class = "badge-normal"
    else: level = "경계"; badge_class = "badge-caution"
    
    bar_pct = max(0, min(100, (iq_score - 70) / 70 * 100)) 
    
    return f"""
    <div style="margin-bottom:18px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-weight:600; color:#1e293b; font-size:14px;">{label}</span>
            <div>
                <span class="badge {badge_class}">{level}</span>
                <span style="font-weight:bold; color:{color}; font-size:15px;">IQ {iq_score}</span>
            </div>
        </div>
        <div class="t-score-bar">
            <div class="t-score-fill" style="width:{bar_pct:.1f}%; background-color:{color};">IQ {iq_score}</div>
        </div>
        <div style="font-size:11px; color:#64748b;">{description}</div>
    </div>
    """

def mbti_html(mbti_type, dims, mid):
    axes = [
        ("내향(I)", "외향(E)", dims[0]),
        ("직관(N)", "감각(S)", dims[1]),
        ("감정(F)", "사고(T)", dims[2]),
        ("인식(P)", "판단(J)", dims[3])
    ]
    html = '<div style="margin-bottom:18px;"><div style="font-weight:600; color:#1e293b; font-size:14px; margin-bottom:10px;">성격 유형 (MBTI) 4축 성향 분포</div>'
    for left_lbl, right_lbl, val in axes:
        pct = (val / (mid * 2)) * 100 if mid > 0 else 50
        html += f"""
        <div style="display:flex; align-items:center; font-size:12px; margin-bottom:6px;">
            <div style="width:50px; text-align:right; margin-right:8px; color:#64748b; font-weight:bold;">{left_lbl}</div>
            <div style="flex:1; background-color:#e2e8f0; height:14px; border-radius:7px; position:relative; overflow:hidden;">
                <div style="position:absolute; left:0; top:0; height:100%; width:{pct}%; background-color:#0ea5e9; border-radius:7px;"></div>
                <div style="position:absolute; left:50%; top:0; height:100%; width:2px; background-color:#fff;"></div>
            </div>
            <div style="width:50px; margin-left:8px; color:#64748b; font-weight:bold;">{right_lbl}</div>
        </div>
        """
    html += '<div style="font-size:11px; color:#64748b; margin-top:5px;">막대가 오른쪽(중앙선 이상)으로 치우칠수록 우측 성향(E, S, T, J)이 강함을 의미합니다.</div></div>'
    return html

# 💡 캔버스 사이즈 최적화
def draw_canvas(label, description, key_name):
    st.write(f"**{label}**")
    st.caption(description)
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=3, stroke_color="#000000", background_color="#ffffff",
        height=320, width=420, drawing_mode="freedraw", key=key_name,
    )
    if canvas_result.image_data is not None:
        img = Image.fromarray(canvas_result.image_data.astype('uint8')).convert('RGB')
        if np.sum(np.array(img) < 255) > 500: return img
    return None

SCALE_INFO = {
    "IQ": {"color": "#005088", "label": "인지 기능 (IQ)", "desc": "전반적 인지능력·처리속도 지표", "max_per_item": 4},
    "MBTI": {"color": "#0ea5e9", "label": "성격 유형 (MBTI)", "desc": "16가지 성격 유형 지표", "max_per_item": 4},
    "TCI": {"color": "#11caa0", "label": "기질 및 성격 (TCI)", "desc": "자극추구·위험회피·자율성 등", "max_per_item": 4},
    "MMPI": {"color": "#e63946", "label": "심리적 증상 (MMPI)", "desc": "우울·반사회성·편집·불안 등", "max_per_item": 4},
    "CLINICAL": {"color": "#f59e0b", "label": "임상 증상 (CLINICAL)", "desc": "주요 임상 증상 스크리닝", "max_per_item": 4},
}

def compute_scores(scores_dict):
    result = {}
    for key, answers in scores_dict.items():
        if not answers: continue
        valid_answers = [a for a in answers if a is not None]
        if not valid_answers: continue
        
        info = SCALE_INFO.get(key, {})
        total = sum(valid_answers)
        n = len(valid_answers)
        max_possible = n * info.get("max_per_item", 4)
        
        result_item = {
            "total": total, "max": max_possible, 
            "pct": total / max_possible * 100 if max_possible > 0 else 0
        }
        
        if key == "IQ":
            result_item["iq_val"] = int((total / max_possible) * 70 + 70) if max_possible > 0 else 100
            
        if key == "MBTI" and n > 0:
            dims = [0, 0, 0, 0]
            for idx, a in enumerate(valid_answers):
                dims[idx % 4] += a
            mid = (n / 4) * 2
            m_type = ""
            m_type += "I" if dims[0] < mid else "E"
            m_type += "S" if dims[1] < mid else "N"
            m_type += "T" if dims[2] < mid else "F"
            m_type += "J" if dims[3] < mid else "P"
            result_item["mbti_type"] = m_type
            result_item["mbti_dims"] = dims
            result_item["mbti_mid"] = mid
            
        result[key] = result_item
    return result

# =============================================
# 6. 메인 화면
# =============================================
if 'reg' not in st.session_state: st.session_state['reg'] = False

if not st.session_state['reg']:
    st.markdown("""
    <div style="text-align:center; padding:40px 0 20px;">
        <h1 style="color:#005088;">🧠 Full Battery 4.0 (임상 정석 HTP 분리형)</h1>
        <h3 style="color:#475569; font-weight:400;">정밀 심리 진단 시스템</h3>
    </div>
    """, unsafe_allow_html=True)

    col_form, _ = st.columns([1.2, 1])
    with col_form:
        with st.form("login_form"):
            name  = st.text_input("성함 (이름)")
            birth = st.text_input("생년월일 (8자리)")
            gen   = st.selectbox("성별", ["남성", "여성"])
            rel   = st.selectbox("의뢰 관계", ["본인", "부", "모", "자녀", "배우자", "기타"])
            c1, c2 = st.columns(2)
            with c1: load_btn = st.form_submit_button("📂 기존 기록 불러오기", use_container_width=True)
            with c2: new_btn  = st.form_submit_button("🚀 신규 검사 시작", use_container_width=True, type="primary")

        if (load_btn or new_btn) and name and birth:
            st.session_state['u'] = {"name": name, "birth": birth, "gen": gen, "rel": rel}
            st.session_state['scores'] = {}
            st.session_state['sct'] = [""] * len(db["sct_starts"])
            if load_btn:
                try:
                    res = requests.get(GOOGLE_SCRIPT_URL, params={"name": name, "birth": birth}, timeout=10).json()
                    if res.get("status") == "success": st.session_state['scores'] = res.get("scores", {})
                except Exception: pass
            st.session_state['reg'] = True
            st.rerun()

else:
    u = st.session_state['u']
    st.sidebar.markdown(f"""
    <div style="background:#005088;color:white;padding:16px;border-radius:10px;margin-bottom:16px;">
        <div style="font-size:18px;font-weight:bold;">👤 {u['name']}님</div>
        <div style="font-size:13px;opacity:0.85;">{u['gen']} · {u['rel']} · {u['birth']}</div>
    </div>
    """, unsafe_allow_html=True)

    menu = st.sidebar.radio(
        "검사 단계",
        ["📋 1단계: 객관식 검사", "✍️ 2단계: 문장완성(SCT)", "🎨 3단계: 정밀 투사그림", "📑 4단계: 종합 결과지"],
        label_visibility="collapsed"
    )

    progress_map = {"📋 1단계: 객관식 검사": 0.25, "✍️ 2단계: 문장완성(SCT)": 0.50, "🎨 3단계: 정밀 투사그림": 0.75, "📑 4단계: 종합 결과지": 1.00}
    st.sidebar.progress(progress_map[menu])
    
    st.sidebar.divider()
    st.sidebar.caption(f"🤖 AI 엔진: `{_model_name}`")
    
    # 💡 찌꺼기 데이터 강제 청소 버튼
    if st.sidebar.button("🔄 완전 초기화 (새로 시작)", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # ================= 1단계 =================
    if menu == "📋 1단계: 객관식 검사":
        st.header("📋 객관식 정밀 진단 검사")
        st.info("💡 처음에는 모든 문항이 완전히 비워져 있습니다. 누락된 문항이 없도록 꼼꼼히 체크해 주세요.")
        
        opts = {0: "전혀 아니다", 1: "아니다", 2: "보통", 3: "그렇다", 4: "매우 그렇다"}
        cur_s = st.session_state.get('scores', {})

        for c, qs in db["qs"].items():
            if not qs: continue
            info = SCALE_INFO.get(c, {})
            with st.expander(f"📌 **{info.get('label', c)}** — {len(qs)}문항", expanded=False):
                ans_array = []
                saved = cur_s.get(c, [])
                for i, q in enumerate(qs):
                    # 완전 빈칸 보장 로직
                    default_idx = saved[i] if (i < len(saved) and saved[i] is not None and str(saved[i]).isdigit()) else None
                    
                    ans = st.radio(
                        f"**{i+1}.** {q}", 
                        options=list(opts.keys()), 
                        format_func=lambda x: opts[x], 
                        horizontal=True, 
                        key=f"{c}_{i}", 
                        index=default_idx
                    )
                    ans_array.append(ans)
                cur_s[c] = ans_array

        if st.button("🚀 검사 완료 및 임시 저장", use_container_width=True, type="primary"):
            st.session_state['scores'] = cur_s
            missing_count = sum(1 for arr in cur_s.values() for a in arr if a is None)
            
            if missing_count > 0:
                st.warning(f"⚠️ 아직 체크하지 않은 문항이 **{missing_count}개** 있습니다. 빠짐없이 체크해 주세요!")
            else:
                st.success("✅ 모든 문항 체크 완료! 왼쪽 메뉴에서 2단계(SCT)로 이동하세요.")
                try: requests.post(GOOGLE_SCRIPT_URL, data=json.dumps({"user": u, "scores": cur_s}), timeout=10)
                except Exception: pass

    # ================= 2단계 =================
    elif menu == "✍️ 2단계: 문장완성(SCT)":
        st.header("✍️ 문장완성검사 (SCT)")
        sct_ans = st.session_state.get('sct', [""] * len(db["sct_starts"]))
        for i, start in enumerate(db["sct_starts"]):
            sct_ans[i] = st.text_input(start, value=sct_ans[i], key=f"sct_{i}")
        if st.button("💾 SCT 저장", use_container_width=True, type="primary"):
            st.session_state['sct'] = sct_ans
            st.success("✅ 저장 완료! 3단계 그림 검사로 이동하세요.")

    # ================= 3단계 =================
    elif menu == "🎨 3단계: 정밀 투사그림":
        st.header("🎨 임상 표준 투사 그림 검사 (개별 캔버스)")
        st.info("임상 심리 검사의 정석에 따라, 각 항목을 개별 스케치북에 따로 그려주세요.")

        imgs = {}
        c1, c2 = st.columns(2)
        
        # 💡 [핵심 수정] HTP를 집, 나무, 사람 3개의 캔버스로 완전 분리
        with c1:
            imgs['house'] = draw_canvas("1. 집 (House)", "여백을 활용하여 '집'을 그려주세요.", "cv_house")
            st.divider()
            imgs['person'] = draw_canvas("3. 사람 (Person)", "얼굴뿐만 아니라 '사람의 전신'을 그려주세요.", "cv_person")
            st.divider()
            imgs['kfd'] = draw_canvas("5. 동적 가족화 (KFD)", "본인을 포함한 가족들이 무언가를 하고 있는 모습을 그려주세요.", "cv_kfd")
        
        with c2:
            imgs['tree'] = draw_canvas("2. 나무 (Tree)", "자유롭게 '나무' 한 그루를 그려주세요.", "cv_tree")
            st.divider()
            imgs['pitr'] = draw_canvas("4. 빗속의 사람 (PITR)", "비가 내리는 환경 속에 있는 사람을 그려주세요.", "cv_pitr")

        if st.button("💾 개별 그림 데이터 비전 AI에 전송", use_container_width=True, type="primary"):
            saved_imgs = {k: v for k, v in imgs.items() if v is not None}
            st.session_state['clinical_images'] = saved_imgs
            st.success(f"✅ {len(saved_imgs)}개의 스케치 데이터 저장 완료! 4단계 종합 결과지로 이동하세요.")

    # ================= 4단계 =================
    elif menu == "📑 4단계: 종합 결과지":
        st.header("📑 종합 임상 심리평가보고서")
        
        missing_count = sum(1 for arr in st.session_state.get('scores', {}).values() for a in arr if a is None)
        
        if missing_count > 0:
            st.error(f"⚠️ 1단계 객관식 검사에서 아직 풀지 않은 문항이 **{missing_count}개** 있습니다. 모두 체크해야 점수 산출이 가능합니다.")
        else:
            score_stats = compute_scores(st.session_state.get('scores', {}))

            st.subheader("📊 Clinical Profile — 다차원 임상 지표")
            cols = st.columns(len(score_stats) if score_stats else 1)
            
            for i, (key, stat) in enumerate(score_stats.items()):
                info = SCALE_INFO.get(key, {})
                if key == "IQ" and "iq_val" in stat:
                    val_text = f"{stat['iq_val']}"
                    sub_text = "IQ 추정치"
                elif key == "MBTI" and "mbti_type" in stat:
                    val_text = stat["mbti_type"]
                    sub_text = "16유형 지표"
                else:
                    val_text = str(stat['total'])
                    sub_text = f"{stat['pct']:.0f}%ile"
                    
                with cols[i]:
                    st.markdown(f"""
                    <div class="score-card">
                        <div class="score-val" style="color:{info.get('color','#005088')};">{val_text}</div>
                        <div class="score-label">{info.get('label', key).split('(')[0]}</div>
                        <div style="font-size:11px;color:#94a3b8;">{sub_text}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            for key, stat in score_stats.items():
                info = SCALE_INFO.get(key, {})
                if key == "IQ":
                    components.html(iq_score_html(info.get('label', key), stat['iq_val'], color=info.get('color', '#005088'), description=info.get('desc', '')), height=85)
                elif key == "MBTI":
                    components.html(mbti_html(stat['mbti_type'], stat['mbti_dims'], stat['mbti_mid']), height=135)
                else:
                    components.html(t_score_html(info.get('label', key), stat['total'], stat['max'], color=info.get('color', '#005088'), description=info.get('desc', '')), height=85)

            st.divider()
            if st.button("🧠 AI(Vision+Text) 통합 심리평가보고서 생성", use_container_width=True, type="primary"):
                with st.spinner("AI 임상심리사가 수치 데이터와 그림(Vision)을 통합 분석 중입니다..."):
                    sct_lines = "\n".join([f"- {s}{a}" for s, a in zip(db["sct_starts"], st.session_state.get('sct', []))])
                    
                    score_summary = ""
                    for k, v in score_stats.items():
                        if k == "IQ": score_summary += f"- IQ 추정치: {v['iq_val']}\n"
                        elif k == "MBTI": score_summary += f"- MBTI 성격 유형: {v['mbti_type']}\n"
                        else: score_summary += f"- {k}: 원점수 {v['total']}점\n"

                    prompt = f"""
                    당신은 20년 경력의 대학병원 수석 임상심리사입니다.
                    내담자의 객관식 점수, SCT 답변, 그리고 첨부된 '직접 그린 투사 그림'들을 시각적으로 심층 분석하여 소견서를 작성하세요.

                    [내담자: {u['name']} / {u['gen']}]
                    1. 객관식 지표 (IQ 및 성격유형 포함): \n{score_summary}
                    2. SCT 응답: \n{sct_lines}
                    
                    [그림 분석 및 작성 지침 - 💡 매우 중요]
                    - 내담자는 HTP(집, 나무, 사람)를 한 장이 아닌 각각 독립적인 캔버스에 따로 그렸습니다.
                    - 전달된 이미지들을 확인하여 각 캔버스(화면) 안에서 객체를 얼마나 꽉 차게 그렸는지, 혹은 작게 그렸는지 '공간 활용도(자아 크기)'를 독립적으로 분석하세요.
                    - 반드시 객관적인 전문가 평어체(~함, ~시사됨)를 사용하세요.
                    - 내담자의 지능(IQ), 성격유형(MBTI) 특성과 투사 그림을 유기적으로 연결하여 해석하세요.
                    
                    - 목차:
                      1. 인지 및 지능 기능
                      2. 기질 및 성격 특성 (16유형 중심)
                      3. 정서 및 심리적 적응
                      4. 투사 검사(그림) 정밀 분석 소견 (집, 나무, 사람 개별 해석 포함)
                      5. 치료적 제언
                    """
                    
                    # 💡 AI에게 어떤 이미지가 무슨 그림인지 이름표를 붙여서 전송
                    contents = [prompt]
                    if 'clinical_images' in st.session_state:
                        labels = {
                            'house': "[1번 캔버스: 집 그림]", 
                            'tree': "[2번 캔버스: 나무 그림]", 
                            'person': "[3번 캔버스: 사람 그림]", 
                            'pitr': "[4번 캔버스: 빗속의 사람 그림]", 
                            'kfd': "[5번 캔버스: 동적 가족화 그림]"
                        }
                        for k, img in st.session_state['clinical_images'].items():
                            contents.append(labels.get(k, "[첨부 그림]"))
                            contents.append(img)
                    
                    try:
                        resp = model.generate_content(contents)
                        st.session_state['final_report'] = resp.text
                        st.toast("✅ 보고서 생성 완료!", icon="🧠")
                    except Exception as e:
                        st.error(f"AI 연동 오류: {e}")

            if 'final_report' in st.session_state:
                st.markdown(f"""
                <div class="report-header">
                    <h2 style="margin:0 0 8px;">종합 심리평가보고서</h2>
                    <div style="opacity:0.9; font-size:14px;">
                        내담자: <strong>{u['name']}</strong> &nbsp;|&nbsp; 성별: <strong>{u['gen']}</strong> &nbsp;|&nbsp; 
                        생년월일: <strong>{u['birth']}</strong> &nbsp;|&nbsp; 의뢰: <strong>{u['rel']}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(st.session_state['final_report'])

                st.subheader("🖨️ 보고서 인쇄")
                if st.button("🖨️ 인쇄 / PDF 저장", use_container_width=True):
                    components.html("<script>window.print();</script>", height=0)

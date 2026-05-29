import streamlit as st
import json, os, requests, re
import streamlit.components.v1 as components
import google.generativeai as genai

# =============================================
# 1. 페이지 설정
# =============================================
st.set_page_config(
    page_title="정밀 심리 진단 시스템 2.0",
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
    """Gemini 3.5 Flash (대표님 사용 모델) — 정식명 우선, 순차 폴백"""
    candidates = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-preview-05-20",
        "gemini-2.5-flash-preview",
        "gemini-2.0-flash",
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
# 3. 전체 스타일 (CSS 오류 완전 수정)
# =============================================
st.markdown("""
<style>
/* 인쇄 시 버튼 숨김 (사이드바는 유지) */
@media print {
    .stButton, .stDownloadButton { display: none !important; }
    .main { background-color: white !important; padding: 0 !important; }
}

/* T-Score 바 차트 */
.t-score-bar {
    background-color: #e2e8f0;
    border-radius: 6px;
    height: 28px;
    width: 100%;
    position: relative;
    margin-bottom: 12px;
    overflow: hidden;
}
.t-score-fill {
    height: 100%;
    border-radius: 6px;
    color: white;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 12px;
    font-size: 13px;
    font-weight: bold;
    transition: width 0.5s ease;
}

/* 결과지 전용 스타일 */
.report-header {
    background: linear-gradient(135deg, #005088 0%, #0077cc 100%);
    color: white;
    padding: 28px 32px;
    border-radius: 12px;
    margin-bottom: 28px;
}
.report-section {
    background: #f8faff;
    border-left: 5px solid #005088;
    padding: 20px 24px;
    margin-bottom: 20px;
    border-radius: 0 8px 8px 0;
}
.report-section h3 {
    color: #005088;
    margin-top: 0;
    font-size: 1.1rem;
}
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
    margin-right: 6px;
}
.badge-normal  { background: #d1fae5; color: #065f46; }
.badge-caution { background: #fef3c7; color: #92400e; }
.badge-high    { background: #fee2e2; color: #991b1b; }

/* 점수 카드 */
.score-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.score-card .score-val {
    font-size: 2.2rem;
    font-weight: bold;
    color: #005088;
}
.score-card .score-label {
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 4px;
}
</style>
""", unsafe_allow_html=True)

# =============================================
# 4. 구글 시트 URL
# =============================================
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwOXsbz1hKT_dPN6pJDn6QAlEginqXIOLBXiFZtV2kKffbZekvMVOIg1LZ19h4dV0Lyjw/exec"

# =============================================
# 5. 데이터 로드 (txt 문항 파일)
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
            "나의 아버지는 ",
            "내가 가장 행복할 때는 ",
            "나의 장래는 ",
            "나를 가장 화나게 하는 것은 ",
            "내 생각에 참다운 친구란 ",
            "내가 어렸을 때는 ",
            "나의 어머니는 ",
            "내가 가장 두려워하는 것은 ",
            "무슨 일을 해서라도 잊고 싶은 것은 ",
            "다른 사람들이 나를 ",
            "내가 바라는 이상적인 나는 ",
            "나에게 가장 힘들었던 경험은 ",
        ]
    }

db = load_data()

# =============================================
# 6. 유틸: T-Score 바 HTML 생성
# =============================================
def t_score_html(label, raw_score, max_possible, color="#005088", description=""):
    """원점수 → T점수(평균50, SD10) 변환 후 바 차트 생성"""
    if max_possible > 0:
        ratio = raw_score / max_possible
    else:
        ratio = 0
    t_val = int(ratio * 40 + 30)   # 30(최저) ~ 70(최고) 범위로 스케일
    t_val = max(30, min(80, t_val))
    bar_pct = (t_val - 30) / 50 * 100  # 30~80 → 0%~100%

    if t_val < 45:
        level = "낮음"; badge_class = "badge-normal"
    elif t_val < 60:
        level = "정상"; badge_class = "badge-normal"
    elif t_val < 65:
        level = "경계"; badge_class = "badge-caution"
    else:
        level = "높음"; badge_class = "badge-high"

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
            <div class="t-score-fill" style="width:{bar_pct:.1f}%; background-color:{color};">
                {raw_score}점
            </div>
        </div>
        {f'<div style="font-size:11px; color:#64748b;">{description}</div>' if description else ''}
    </div>
    """

# =============================================
# 7. 검사별 척도 정의 (채점 기준)
# =============================================
SCALE_INFO = {
    "IQ": {
        "color": "#005088",
        "label": "인지 기능 지표 (IQ)",
        "desc": "전반적 인지능력·처리속도·작업기억 복합 지표",
        "max_per_item": 4
    },
    "MBTI": {
        "color": "#0ea5e9",
        "label": "성격 유형 지표 (MBTI)",
        "desc": "E/I·S/N·T/F·J/P 4축 성격 선호도",
        "max_per_item": 4
    },
    "TCI": {
        "color": "#11caa0",
        "label": "기질 및 성격 검사 (TCI)",
        "desc": "자극추구·위험회피·사회적 민감성·자율성·연대감·자기초월",
        "max_per_item": 4
    },
    "MMPI": {
        "color": "#e63946",
        "label": "정서·심리적 증상 지표 (MMPI)",
        "desc": "건강염려·우울·히스테리·반사회성·편집·강박·조현병·조증 척도",
        "max_per_item": 4
    },
    "CLINICAL": {
        "color": "#f59e0b",
        "label": "임상 증상 지표 (CLINICAL)",
        "desc": "불안·강박·공황·외상·해리 등 주요 임상 증상 스크리닝",
        "max_per_item": 4
    },
}

def compute_scores(scores_dict):
    """각 검사의 총점, 평균, 최대점 계산"""
    result = {}
    for key, answers in scores_dict.items():
        if not answers:
            continue
        info = SCALE_INFO.get(key, {})
        total = sum(answers)
        n = len(answers)
        max_possible = n * info.get("max_per_item", 4)
        avg = total / n if n > 0 else 0
        result[key] = {
            "total": total,
            "avg": avg,
            "n": n,
            "max": max_possible,
            "pct": total / max_possible * 100 if max_possible > 0 else 0
        }
    return result

# =============================================
# 8. HTP 해석 변환기
# =============================================
def htp_to_clinical_text(htp: dict) -> str:
    lines = []
    size_map = {
        "매우 작음": "그림의 크기가 매우 작아 자아 위축, 낮은 자존감 또는 환경에 대한 위협감을 시사함.",
        "작음":      "그림 크기가 작아 자아감의 위축 또는 내향적 경향이 관찰됨.",
        "보통":      "그림의 크기가 적절하여 자아 기능이 비교적 안정적으로 평가됨.",
        "큼":        "그림 크기가 큰 편으로 외향성 또는 과도한 자아 확장 욕구가 나타남.",
        "매우 큼":   "그림의 크기가 지나치게 커 과대한 자아상 혹은 통제 욕구가 강하게 시사됨.",
    }
    pressure_map = {
        "매우 흐림": "필압이 극히 약해 에너지 수준의 저하, 우울감 또는 의욕 감퇴가 의심됨.",
        "흐림":      "필압이 약하여 심리적 에너지의 저하 경향이 관찰됨.",
        "보통":      "필압이 적절하여 심리적 에너지 수준이 평균 범위에 있음.",
        "강함":      "필압이 강하여 긴장감, 충동성 또는 강한 자기주장 경향을 나타냄.",
        "매우 강함": "필압이 매우 강해 분노감, 긴장 또는 충동 조절의 어려움이 시사됨.",
    }
    if htp.get("house_size"):
        lines.append("【집】 " + size_map.get(htp["house_size"], ""))
    if htp.get("door"):
        lines.append("【집-문】 손잡이가 없는 문은 외부 세계와의 단절감, 타인에 대한 접근 차단 욕구 또는 회피적 대인 태도를 시사함.")
    if htp.get("window"):
        lines.append("【집-창문】 창문이 지나치게 많거나 큰 경우 외부로부터의 자극에 대한 과민성, 타인의 시선 의식 또는 경계심이 반영될 수 있음.")
    if htp.get("tree_root"):
        lines.append("【나무-뿌리】 지나치게 강조된 뿌리는 심리적 안정감에 대한 강한 욕구 또는 존재론적 불안감을 시사함.")
    if htp.get("person_arm"):
        lines.append("【사람-팔】 팔의 생략 또는 은닉은 환경에 대한 무력감, 통제력 상실감 혹은 의존 욕구를 나타냄.")
    if htp.get("pressure"):
        lines.append("【필압】 " + pressure_map.get(htp["pressure"], ""))
    return "\n".join(lines) if lines else "HTP 데이터 없음."

# =============================================
# 9. AI 결과지 생성 (강화된 프롬프트)
# =============================================
def build_prompt(user_info, score_stats, sct_data, htp_text):
    sct_lines = "\n".join([
        f"  • {s}{a}" for s, a in sct_data if a.strip()
    ]) or "  (응답 없음)"

    score_summary = ""
    for key, stat in score_stats.items():
        info = SCALE_INFO.get(key, {})
        score_summary += f"  - {info.get('label', key)}: 원점수 {stat['total']}점 / {stat['max']}점 (백분위 {stat['pct']:.1f}%)\n"
        score_summary += f"    ({info.get('desc', '')})\n"

    prompt = f"""
당신은 20년 경력의 수석 정신건강임상심리사(1급)입니다.
아래 내담자의 Full Battery 심리평가 데이터 전체를 통합 분석하여
실제 대학병원 수준의 심리평가보고서를 작성하십시오.

═══════════════════════════════════════════
 내담자 기본 정보
═══════════════════════════════════════════
• 성명: {user_info['name']}
• 성별: {user_info['gen']}
• 생년월일: {user_info['birth']}
• 의뢰인 관계: {user_info['rel']}

═══════════════════════════════════════════
 1. 객관식 5종 검사 원점수 요약
═══════════════════════════════════════════
{score_summary}

═══════════════════════════════════════════
 2. 문장완성검사(SCT) 주관식 응답
═══════════════════════════════════════════
{sct_lines}

═══════════════════════════════════════════
 3. HTP 투사그림검사 임상적 특징
═══════════════════════════════════════════
{htp_text}

═══════════════════════════════════════════
 작성 지침 (반드시 준수)
═══════════════════════════════════════════
[문체]
- 전문 평어체 사용: ~됨, ~시사됨, ~판단됨, ~나타남, ~관찰됨
- 병원 보고서 수준의 객관적이고 정교한 언어 구사
- 수치와 임상적 의미를 반드시 연결하여 서술

[분석 깊이]
- 단순 점수 나열 금지
- SCT 응답에서 내담자의 무의식적 갈등, 핵심 신념, 대인관계 패턴을 반드시 추출
- HTP 특징과 MMPI 점수를 교차 검증하여 방어기제 및 정서 조절 패턴 분석
- IQ 점수와 CLINICAL 점수의 상호작용(인지-정서 해리 여부) 평가
- MBTI/TCI 결과와 SCT를 결합하여 기질-환경 적합도 평가

[목차 구조 - 반드시 아래 형식 그대로]
# 종합 심리평가보고서 (Psychological Evaluation Report)

## 1. 인지 및 지능 기능 평가
(IQ 검사 결과 해석 / 처리속도·작업기억·유동추론 분석)

## 2. 지각 및 사고적 측면
(현실검증력, 사고 조직화, HTP 투사 내용과의 연계 해석)

## 3. 정서 및 심리적 적응 상태
(MMPI 임상 척도별 분석 + SCT 응답의 정서 패턴 + HTP 정서 지표 통합)

## 4. 기질 및 성격 특성
(MBTI 유형 해석 + TCI 기질 차원 분석 + SCT에서 드러난 성격 패턴)

## 5. 대인관계 및 가족역동
(SCT 응답 중 부모·친구·타인 관련 문항 심층 분석)

## 6. 임상적 위험 요인 평가
(CLINICAL 척도 + MMPI 주요 임상 척도 기반 위험 요인 명시)

## 7. 종합 소견 및 치료적 제언
(핵심 심리적 문제 요약 / 권장 치료 접근법 / 예후 / 추적 평가 권고)
"""
    return prompt


# =============================================
# 10. 메인 앱 진입부
# =============================================
if 'reg' not in st.session_state:
    st.session_state['reg'] = False

# ─────────────── 로그인/등록 화면 ───────────────
if not st.session_state['reg']:
    st.markdown("""
    <div style="text-align:center; padding:40px 0 20px;">
        <h1 style="color:#005088;">🧠 Full Battery 2.0</h1>
        <h3 style="color:#475569; font-weight:400;">정밀 심리 진단 시스템</h3>
        <p style="color:#94a3b8;">IQ · MBTI · TCI · MMPI · CLINICAL · SCT · HTP 통합 분석</p>
    </div>
    """, unsafe_allow_html=True)

    col_form, _ = st.columns([1.2, 1])
    with col_form:
        with st.form("login_form"):
            st.subheader("내담자 정보 입력")
            name  = st.text_input("성함 (이름)", placeholder="홍길동")
            birth = st.text_input("생년월일 (8자리)", placeholder="19900101")
            gen   = st.selectbox("성별", ["남성", "여성"])
            rel   = st.selectbox("의뢰 관계", ["본인", "부", "모", "자녀", "배우자", "기타"])
            col1, col2 = st.columns(2)
            with col1:
                load_btn = st.form_submit_button("📂 기존 기록 불러오기", use_container_width=True)
            with col2:
                new_btn  = st.form_submit_button("🚀 신규 검사 시작", use_container_width=True, type="primary")

        if (load_btn or new_btn) and name and birth:
            st.session_state['u'] = {"name": name, "birth": birth, "gen": gen, "rel": rel}
            st.session_state['scores'] = {}
            st.session_state['sct'] = [""] * len(db["sct_starts"])
            st.session_state['htp'] = {}
            if load_btn:
                with st.spinner("DB에서 기록을 조회 중입니다..."):
                    try:
                        res = requests.get(GOOGLE_SCRIPT_URL,
                                           params={"name": name, "birth": birth},
                                           timeout=10).json()
                        if res.get("status") == "success":
                            st.session_state['scores'] = res.get("scores", {})
                            st.toast("✅ 기존 기록을 불러왔습니다.", icon="📂")
                    except Exception:
                        st.warning("구글 시트 연결 오류. 빈 상태로 시작합니다.")
            st.session_state['reg'] = True
            st.rerun()
        elif (load_btn or new_btn) and not (name and birth):
            st.error("이름과 생년월일을 입력해주세요.")

# ─────────────── 메인 검사 화면 ───────────────
else:
    u = st.session_state['u']

    # 사이드바
    st.sidebar.markdown(f"""
    <div style="background:#005088;color:white;padding:16px;border-radius:10px;margin-bottom:16px;">
        <div style="font-size:18px;font-weight:bold;">👤 {u['name']}님</div>
        <div style="font-size:13px;opacity:0.85;">{u['gen']} · {u['rel']} · {u['birth']}</div>
    </div>
    """, unsafe_allow_html=True)

    menu = st.sidebar.radio(
        "검사 단계",
        ["📋 1단계: 객관식 검사", "✍️ 2단계: 문장완성(SCT)", "🎨 3단계: 투사그림(HTP)", "📑 4단계: 종합 결과지"],
        label_visibility="collapsed"
    )

    # 진행률 표시
    progress_map = {
        "📋 1단계: 객관식 검사": 0.25,
        "✍️ 2단계: 문장완성(SCT)": 0.50,
        "🎨 3단계: 투사그림(HTP)": 0.75,
        "📑 4단계: 종합 결과지": 1.00
    }
    st.sidebar.progress(progress_map[menu])

    completed = []
    if st.session_state.get('scores'): completed.append("✅ 객관식")
    if any(s.strip() for s in st.session_state.get('sct', [])): completed.append("✅ SCT")
    if st.session_state.get('htp'): completed.append("✅ HTP")
    if completed:
        st.sidebar.markdown("**완료된 검사:** " + " · ".join(completed))

    st.sidebar.divider()
    st.sidebar.caption(f"🤖 AI 엔진: `{_model_name}`")
    if st.sidebar.button("🔄 초기화 (처음으로)", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # ═══════════════════════════════════════
    # 1단계: 객관식 검사
    # ═══════════════════════════════════════
    if menu == "📋 1단계: 객관식 검사":
        st.header("📋 객관식 정밀 진단 검사")
        st.caption("각 문항을 읽고 본인에게 해당하는 정도를 선택해 주세요.")

        opts = {0: "전혀 아니다", 1: "아니다", 2: "보통", 3: "그렇다", 4: "매우 그렇다"}
        cur_s = st.session_state.get('scores', {})

        SCALE_COLORS = {
            "IQ": "🔵", "MBTI": "🟦", "TCI": "🟢", "MMPI": "🔴", "CLINICAL": "🟠"
        }

        for c, qs in db["qs"].items():
            if not qs:
                st.info(f"{c} 문항 파일({c.lower()}.txt)이 없습니다.")
                continue
            info = SCALE_INFO.get(c, {})
            with st.expander(
                f"{SCALE_COLORS.get(c, '📌')} **{info.get('label', c)}** — {len(qs)}문항",
                expanded=False
            ):
                st.caption(info.get('desc', ''))
                ans_array = []
                saved = cur_s.get(c, [])
                for i, q in enumerate(qs):
                    default_idx = saved[i] if i < len(saved) else 2
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

        st.divider()
        if st.button("🚀 검사 완료 및 저장", use_container_width=True, type="primary"):
            st.session_state['scores'] = cur_s
            # 구글 시트 저장
            try:
                requests.post(
                    GOOGLE_SCRIPT_URL,
                    data=json.dumps({"user": u, "scores": cur_s}),
                    timeout=10
                )
                st.success("✅ 저장 완료! 왼쪽 메뉴에서 **2단계 SCT**로 이동하세요.")
            except Exception:
                st.session_state['scores'] = cur_s
                st.success("✅ 임시 저장 완료 (네트워크 오류로 DB 미반영). 다음 단계로 이동하세요.")

    # ═══════════════════════════════════════
    # 2단계: SCT 문장완성
    # ═══════════════════════════════════════
    elif menu == "✍️ 2단계: 문장완성(SCT)":
        st.header("✍️ 문장완성검사 (SCT)")
        st.info("문장을 읽고 **가장 먼저 떠오르는 생각**으로 자유롭게 완성해 주세요. 정답은 없습니다.")

        sct_ans = st.session_state.get('sct', [""] * len(db["sct_starts"]))

        for i, start in enumerate(db["sct_starts"]):
            col_num, col_input = st.columns([0.05, 0.95])
            with col_num:
                st.markdown(f"**{i+1}**")
            with col_input:
                sct_ans[i] = st.text_input(
                    start,
                    value=sct_ans[i],
                    key=f"sct_{i}",
                    label_visibility="visible"
                )

        st.divider()
        if st.button("💾 SCT 저장", use_container_width=True, type="primary"):
            st.session_state['sct'] = sct_ans
            filled = sum(1 for a in sct_ans if a.strip())
            st.success(f"✅ {filled}/{len(db['sct_starts'])}문항 저장 완료! **3단계 HTP**로 이동하세요.")

    # ═══════════════════════════════════════
    # 3단계: HTP 투사그림
    # ═══════════════════════════════════════
    elif menu == "🎨 3단계: 투사그림(HTP)":
        st.header("🎨 투사그림검사 (HTP)")
        st.info("도화지에 **집·나무·사람**을 그린 후, 그림의 특징을 아래에서 선택해 주세요.")

        htp = st.session_state.get('htp', {})

        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("🏠 집 (House)")
            htp['house_size']   = st.select_slider("집의 전체 크기", ["매우 작음","작음","보통","큼","매우 큼"], value=htp.get('house_size', "보통"))
            htp['door']         = st.checkbox("문에 손잡이가 없음", value=htp.get('door', False))
            htp['window']       = st.checkbox("창문이 지나치게 많거나 큼", value=htp.get('window', False))
            htp['chimney']      = st.checkbox("굴뚝에서 연기가 지나치게 많이 남", value=htp.get('chimney', False))
            htp['house_roof']   = st.checkbox("지붕이 지나치게 강조됨", value=htp.get('house_roof', False))

        with col2:
            st.subheader("🌳 나무 (Tree)")
            htp['tree_root']    = st.checkbox("뿌리가 지나치게 강조됨", value=htp.get('tree_root', False))
            htp['tree_dead']    = st.checkbox("나무가 죽거나 쓰러져 있음", value=htp.get('tree_dead', False))
            htp['tree_hollow']  = st.checkbox("나무에 구멍(공동)이 있음", value=htp.get('tree_hollow', False))
            htp['tree_branch']  = st.checkbox("가지가 끊겨 있거나 날카로움", value=htp.get('tree_branch', False))
            htp['tree_fruit']   = st.checkbox("열매가 지나치게 많음", value=htp.get('tree_fruit', False))

        with col3:
            st.subheader("🧍 사람 (Person)")
            htp['person_arm']   = st.checkbox("팔이 생략되거나 뒤로 숨김", value=htp.get('person_arm', False))
            htp['person_face']  = st.checkbox("얼굴 표정이 없거나 생략됨", value=htp.get('person_face', False))
            htp['person_eye']   = st.checkbox("눈이 지나치게 크거나 작음", value=htp.get('person_eye', False))
            htp['person_feet']  = st.checkbox("발이 생략됨", value=htp.get('person_feet', False))
            htp['person_size']  = st.select_slider("사람의 전체 크기", ["매우 작음","작음","보통","큼","매우 큼"], value=htp.get('person_size', "보통"))

        st.divider()
        st.subheader("✏️ 전반적 그림 특징")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            htp['pressure']     = st.select_slider("필압 (선의 굵기·강도)", ["매우 흐림","흐림","보통","강함","매우 강함"], value=htp.get('pressure', "보통"))
            htp['placement']    = st.selectbox("그림 위치", ["중앙","좌측 치우침","우측 치우침","상단 치우침","하단 치우침","구석"], index=["중앙","좌측 치우침","우측 치우침","상단 치우침","하단 치우침","구석"].index(htp.get('placement', "중앙")))
        with col_p2:
            htp['erasure']      = st.checkbox("지우개 흔적이 많음", value=htp.get('erasure', False))
            htp['shading']      = st.checkbox("지나친 음영 처리가 있음", value=htp.get('shading', False))

        st.divider()
        if st.button("💾 HTP 저장", use_container_width=True, type="primary"):
            st.session_state['htp'] = htp
            st.success("✅ HTP 데이터 저장 완료! **4단계 종합 결과지**로 이동하세요.")

    # ═══════════════════════════════════════
    # 4단계: 종합 결과지
    # ═══════════════════════════════════════
    elif menu == "📑 4단계: 종합 결과지":
        st.header("📑 종합 임상 심리평가보고서")

        has_scores = bool(st.session_state.get('scores'))
        has_sct    = any(s.strip() for s in st.session_state.get('sct', []))
        has_htp    = bool(st.session_state.get('htp'))

        # 데이터 현황 표시
        c1, c2, c3 = st.columns(3)
        c1.metric("객관식 검사", "✅ 완료" if has_scores else "⚠️ 미완료")
        c2.metric("SCT 문장완성", "✅ 완료" if has_sct else "⚠️ 미완료")
        c3.metric("HTP 투사그림", "✅ 완료" if has_htp else "⚠️ 미완료")

        if not has_scores:
            st.warning("⚠️ 객관식 검사 데이터가 없습니다. 1단계를 먼저 완료해 주세요.")
            st.stop()

        # 점수 요약 섹션
        st.subheader("📊 Clinical Profile — 다차원 T-Score")
        score_stats = compute_scores(st.session_state['scores'])

        cols = st.columns(len(score_stats))
        for i, (key, stat) in enumerate(score_stats.items()):
            info = SCALE_INFO.get(key, {})
            with cols[i]:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score-val" style="color:{info.get('color','#005088')};">{stat['total']}</div>
                    <div class="score-label">{info.get('label', key).split('(')[0]}</div>
                    <div style="font-size:11px;color:#94a3b8;">{stat['pct']:.0f}%ile</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        for key, stat in score_stats.items():
            info = SCALE_INFO.get(key, {})
            components.html(
                t_score_html(
                    info.get('label', key),
                    stat['total'],
                    stat['max'],
                    color=info.get('color', '#005088'),
                    description=info.get('desc', '')
                ),
                height=80
            )

        st.divider()

        # AI 보고서 생성 버튼
        if st.button("🧠 AI 통합 심리평가보고서 생성", use_container_width=True, type="primary"):
            htp_text   = htp_to_clinical_text(st.session_state.get('htp', {}))
            sct_pairs  = list(zip(db["sct_starts"], st.session_state.get('sct', [])))
            prompt     = build_prompt(u, score_stats, sct_pairs, htp_text)

            with st.spinner("AI 임상심리사가 전체 데이터를 통합 분석 중입니다... (30~60초 소요)"):
                try:
                    resp = model.generate_content(prompt)
                    st.session_state['final_report'] = resp.text
                    st.toast("✅ 보고서 생성 완료!", icon="🧠")
                except Exception as e:
                    st.error(f"AI 연동 오류: {e}")

        # 보고서 출력
        if 'final_report' in st.session_state:
            st.divider()
            # 보고서 헤더
            st.markdown(f"""
            <div class="report-header">
                <h2 style="margin:0 0 8px;">종합 심리평가보고서</h2>
                <div style="opacity:0.9; font-size:14px;">
                    내담자: <strong>{u['name']}</strong> &nbsp;|&nbsp;
                    성별: <strong>{u['gen']}</strong> &nbsp;|&nbsp;
                    생년월일: <strong>{u['birth']}</strong> &nbsp;|&nbsp;
                    의뢰 관계: <strong>{u['rel']}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 보고서 본문
            st.markdown(st.session_state['final_report'])

            st.divider()
            # 저장 옵션
            st.subheader("🖨️ 보고서 저장")
            col_print, col_down = st.columns(2)
            with col_print:
                if st.button("🖨️ 인쇄 / PDF 저장", use_container_width=True):
                    components.html("<script>window.print();</script>", height=0)
            with col_down:
                report_text = f"""
종합 심리평가보고서
내담자: {u['name']} | 성별: {u['gen']} | 생년월일: {u['birth']} | 의뢰: {u['rel']}
{'='*60}

{st.session_state['final_report']}
"""
                st.download_button(
                    "💾 TXT 파일 다운로드",
                    data=report_text.encode("utf-8"),
                    file_name=f"심리평가보고서_{u['name']}_{u['birth']}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

import textwrap
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# Custom Font Loading for Streamlit Cloud (Linux)
# ---------------------------------------------------------
import matplotlib.font_manager as fm
import os
import platform
try:
    _font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NanumGothic.ttf')
    if os.path.exists(_font_path):
        if 'NanumGothic' not in [f.name for f in fm.fontManager.ttflist]:
            fm.fontManager.addfont(_font_path)
except Exception:
    pass
# ---------------------------------------------------------
import matplotlib.patheffects as path_effects
import os
import json
import re
import hashlib
from datetime import datetime
from io import BytesIO
from analyzer import CoupangAdAnalyzer

# -----------------------------------------------------------------------------
# 성능 최적화를 위한 렌더링 캐시 함수 정의
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_cached_keyword_html(df_display_dict, search_q=""):
    """
    Pandas iterrows 병목을 해결하기 위한 HTML 렌더링 캐시 함수.
    DataFrame 전체를 딕셔너리로 받아 Streamlit 해싱 오류 방지.
    """
    import pandas as pd
    df_display = pd.DataFrame.from_dict(df_display_dict)
    
    formatted_rows = []
    for _, r in df_display.iterrows():
        st_val = r.get('status', '유지')
        diff_v = int(r.get('imp_diff', 0))
        if st_val == "신규":
            diff_text = f"✨[신규] ▲{diff_v:,}"
        elif st_val == "중단":
            diff_text = f"🛑[중단] (전일:{int(r.get('p_imp',0)):,})"
        else:
            p_imp = int(r.get('p_imp', 0))
            pct = (diff_v / p_imp * 100) if p_imp > 0 else 0
            if diff_v > 0:
                diff_text = f"▲{diff_v:,} (+{pct:.1f}%)"
            elif diff_v < 0:
                diff_text = f"▼{abs(diff_v):,} ({pct:.1f}%)"
            else:
                diff_text = "-"
                
        sp_diff = int(r.get('spend_diff', 0))
        sp_diff_text = f"▲{sp_diff:,}" if sp_diff > 0 else (f"▼{abs(sp_diff):,}" if sp_diff < 0 else "-")
        
        ck_diff = int(r.get('click_diff', 0))
        p_click = int(r.get('p_click', 0))
        if st_val == "신규":
            ck_diff_text = f"✨[신규]"
        elif st_val == "중단":
            ck_diff_text = f"🛑[중단]"
        else:
            if ck_diff > 0:
                pct_ck = (ck_diff / p_click * 100) if p_click > 0 else 0
                ck_diff_text = f"▲{ck_diff:,} (+{pct_ck:.0f}%)"
            elif ck_diff < 0:
                pct_ck = (ck_diff / p_click * 100) if p_click > 0 else 0
                ck_diff_text = f"▼{abs(ck_diff):,} ({pct_ck:.0f}%)"
            else:
                ck_diff_text = "-"
                
        formatted_rows.append({
            "구분": r.get('region', '-'),
            "키워드": r.get('kw', ''),
            "최신노출": f"{int(r.get('l_imp',0)):,}",
            "전일대비": diff_text,
            "누적노출": f"{int(r.get('imp',0)):,}",
            "클릭수": f"{int(r.get('click',0)):,}",
            "클릭증감": ck_diff_text,
            "CTR%": f"{r.get('CTR',0):.2f}%",
            "전환율%": f"{r.get('CVR',0):.1f}%",
            "주문건수": f"{int(r.get('orders',0)):,}",
            "최신광고비": f"{int(r.get('l_spend',0)):,}",
            "지출변동": sp_diff_text,
            "누적광고비": f"{int(r.get('spend',0)):,}",
            "전환매출": f"{int(r.get('sales',0)):,}",
            "CPC": f"{int(r.get('CPC',0)):,}",
            "ROAS": f"{r.get('ROAS',0):.1f}%",
            "광고순위": f"{r.get('rank',0):.1f}위",
            "상품명": r.get('pname', '-')
        })
    
    formatted_df = pd.DataFrame(formatted_rows)
    
    html_table = """
  <div style="max-height: 1200px; overflow-y: auto; border: 1.5px solid #BF360C; border-radius: 6px; font-family: 'Malgun Gothic', 'NanumGothic', sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        <table id="orange-keyword-table" style="width: 100%; border-collapse: collapse; font-size: 8.5px; font-weight: bold; color: #FFFFFF; text-align: left; table-layout: fixed;">
            <thead>
                <tr style="background-color: #F1F5F9; position: sticky; top: 0; z-index: 10; border-bottom: 2px solid #BF360C; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
    """
    
    col_widths = {
        "구분": 80, "키워드": 160, "최신노출": 85, "전일대비": 130, "누적노출": 85,
        "클릭수": 65, "클릭증감": 110, "CTR%": 65, "전환율%": 65, "주문건수": 65,
        "최신광고비": 90, "지출변동": 100, "누적광고비": 90, "전환매출": 90,
        "CPC": 70, "ROAS": 80, "광고순위": 70, "상품명": 350
    }
    total_w = sum(col_widths.values())
    
    for col in formatted_df.columns:
        w_px = col_widths.get(col, 80)
        w_pct = (w_px / total_w) * 100
        html_table += f'<th style="width: {w_pct:.3f}%; min-width: 25px; padding: 4px 6px; color: #000000 !important; border: 0.5px solid #BF360C; font-weight: bold; text-align: left; white-space: nowrap; background-color: #F1F5F9; position: relative;">'
        html_table += f'<span style="color: #000000 !important;">{col}</span>'
        html_table += f'<div class="col-resizer" style="width: 6px; height: 100%; position: absolute; right: 0; top: 0; cursor: col-resize; user-select: none; z-index: 5;"></div>'
        html_table += f'</th>'
    html_table += "</tr></thead><tbody>"
    
    for _, row in formatted_df.iterrows():
        kw_val = str(row["키워드"]).replace("'", "&apos;").replace('"', '&quot;')
        html_table += f'<tr class="keyword-row" data-keyword="{kw_val}" style="background-color:#E65100;border-bottom:0.5px solid #BF360C;cursor:pointer;">'
        for val in row:
            html_table += f'<td style="padding:3px 6px;color:#FFFFFF;border:0.5px solid #BF360C;white-space:nowrap;">{val}</td>'
        html_table += "</tr>"
    html_table += "</tbody></table></div>"
    # 우클릭 팝업 메뉴 HTML 구조 복구
    html_table += '<div id="ctx-menu" style="display:none;position:fixed;z-index:99999;width:210px;background:#1a1f35;border:1px solid rgba(255,255,255,0.12);border-radius:10px;box-shadow:0 12px 40px rgba(0,0,0,0.7);font-family: \'Malgun Gothic\', \'NanumGothic\',sans-serif;padding:6px 0;"><div id="ctx-kw-title" style="padding:9px 14px 8px;font-size:12px;color:#a78bfa;border-bottom:1px solid rgba(255,255,255,0.09);font-weight:bold;background:#111627;border-radius:10px 10px 0 0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">🔑 키워드</div><div class="ctx-item" onclick="doAction(\'타겟\')" style="padding:10px 16px;font-size:13px;color:#e2e8f0;cursor:pointer;display:flex;align-items:center;gap:8px;"><span style="width:22px;height:22px;background:#f97316;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;">🎯</span>타겟 키워드로 이동</div><div class="ctx-item" onclick="doAction(\'수동\')" style="padding:10px 16px;font-size:13px;color:#e2e8f0;cursor:pointer;display:flex;align-items:center;gap:8px;"><span style="width:22px;height:22px;background:#f97316;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;">⚙️</span>수동 관리로 이동</div><div class="ctx-item" onclick="doAction(\'제외\')" style="padding:10px 16px;font-size:13px;color:#e2e8f0;cursor:pointer;display:flex;align-items:center;gap:8px;"><span style="width:22px;height:22px;background:#ef4444;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;">🚫</span>제외 키워드로 이동</div><div style="height:1px;background:rgba(255,255,255,0.08);margin:4px 0;"></div><div class="ctx-item" onclick="doAction(\'복사\')" style="padding:10px 16px;font-size:13px;color:#e2e8f0;cursor:pointer;display:flex;align-items:center;gap:8px;"><span style="font-size:16px;">📋</span>키워드 복사</div></div><style>.ctx-item:hover{background:rgba(99,102,241,0.3)!important;}</style>'
    
    return html_table, len(formatted_rows)

# -----------------------------------------------------------------------------
# 1. 폰트 및 페이지 설정 (Premium Dark Theme)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="쿠팡 광고 최적화 마스터 Web",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 우클릭 메뉴 통신용 완벽 숨김 입력창 핸들러 ──
st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='kw_mover_secret_trigger']) { display: none !important; }</style>", unsafe_allow_html=True)
trigger_val = st.text_input("kw_mover_secret_trigger", key="kw_mover_trigger", label_visibility="collapsed")

if trigger_val:
    parts = trigger_val.split("|||")
    if len(parts) >= 2:
        q_action = parts[0]
        q_target = parts[1]
        q_t = parts[2] if len(parts) > 2 else ""
        
        if "processed_trigger_t" not in st.session_state:
            st.session_state["processed_trigger_t"] = ""
            
        if q_t and q_t != st.session_state["processed_trigger_t"]:
            st.session_state["processed_trigger_t"] = q_t
            if q_target and q_action in ("타겟", "수동", "제외"):
                import json, os
                classes_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keyword_classes.json")
                _kw_classes_early = {}
                if os.path.exists(classes_file):
                    try:
                        with open(classes_file, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                            if content:
                                _kw_classes_early = json.loads(content)
                    except Exception as e:
                        # 파일이 손상되었거나 동시 접근 잠금 시 빈 딕셔너리로 초기화
                        pass
                
                # 방어 로직: 딕셔너리가 아닌 경우 대비
                if not isinstance(_kw_classes_early, dict):
                    _kw_classes_early = {}
                    
                _kw_classes_early[q_target] = q_action
                
                # 원자적 쓰기(Atomic Write) 모방 및 에러 방어
                try:
                    with open(classes_file, "w", encoding="utf-8") as f:
                        json.dump(_kw_classes_early, f, ensure_ascii=False, indent=4)
                except Exception:
                    pass
                
                # toast 메시지 대기 등록 및 탭 포커스 예약
                st.session_state["pending_toast"] = f"✅ '{q_target}' → [{q_action} 관리] 이동 완료"
                
                tab_labels = {
                    "타겟": "🎯 타겟 관리",
                    "수동": "⚙️ 수동 관리",
                    "제외": "🚫 제외 관리"
                }
                st.session_state["pending_tab_focus"] = tab_labels.get(q_action, "")
                
                # 초기화 후 재시작 (상태 초기화 트리거)
                st.session_state["kw_trigger_input"] = "" 
                st.rerun()

# matplotlib 한글 폰트 설정 (Windows 기준 맑은 고딕 우선)
plt.rcParams['font.family'] = 'NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 네온 글래스모피즘 스타일 적용을 위한 Custom CSS
st.markdown("""
<style>
    /* 배경 설정 */
    .stApp {
        background-color: #0B0B1A;
        color: #E2E8F0;
    }
    
    /* 글로벌 다크 테마 일반 텍스트 가독성 유지 (테마 textColor 가 블랙이므로 CSS로 흰색 복구) */
    .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #E2E8F0 !important;
    }
    
    /* 타이틀 그라디언트 복구 */
    .title-gradient {
        font-family: 'Malgun Gothic', 'NanumGothic'', 'NanumGothic', sans        font-size: 2.8rem;
        margin-bottom: 20px;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
    }
    
    /* =========================================================================
       ⚙️ 전체 테마 리디자인: 미니멀 테크 프리미엄 다크 (Stripe/Vercel Style)
       ========================================================================= */
    
    /* 1. st.tabs 탭 리스트 바를 고급스러운 다크 캡슐형으로 전환 (50대 노안 배려) */
    .stApp div[role="tablist"] {
        background: rgba(20, 24, 38, 0.8) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 14px !important;
        padding: 6px 8px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
        gap: 8px !important;
        margin-bottom: 20px !important;
    }
    
    /* 2. 개별 탭 버튼 기본 스타일 (입체적인 카드 형태로 독립) */
    .stApp button[role="tab"] {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        margin: 2px 0 !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* 3. st.tabs 비활성 탭 글자 스타일 (선명한 그레이로 가독성 강화) */
    .stApp button[role="tab"][aria-selected="false"] p,
    .stApp button[role="tab"][aria-selected="false"] span,
    .stApp button[role="tab"][aria-selected="false"] * {
        color: #94A3B8 !important;
        font-weight: 700 !important;
        font-size: 1.12rem !important; /* 대표님을 위한 큼직한 크기 */
        letter-spacing: 0.5px !important;
        text-shadow: none !important;
    }
    
    /* 비활성 탭 호버 시 피드백 */
    .stApp button[role="tab"][aria-selected="false"]:hover {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .stApp button[role="tab"][aria-selected="false"]:hover * {
        color: #FFFFFF !important;
    }
    
    
    /* ------------------------------------------------------------- */
    /* 📌 상단 탭 고정 (Sticky Header) CSS                           */
    /* ------------------------------------------------------------- */
    /* Streamlit 기본 헤더 숨김 */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* 최상단 마스터 타이틀 고정 (:has 속성 사용하여 정확한 타겟팅) */
    div.block-container > div:first-child > div[data-testid="stVerticalBlock"] > div:has(h1) {
        position: sticky !important;
        top: 0px !important;
        z-index: 1000 !important;
        background-color: #0B0B1A !important;
        padding-top: 10px !important;
        padding-bottom: 5px !important;
        margin-top: -40px !important; 
    }

    /* 실시간 분석 중인 파일명 (Caption) 고정 */
    div.block-container > div:first-child > div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stCaptionContainer"]) {
        position: sticky !important;
        top: 60px !important; 
        z-index: 1000 !important;
        background-color: #0B0B1A !important;
        padding-bottom: 10px !important;
        border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    }

    /* 메인 탭 (모든 탭 리스트의 기본 고정 설정) */
    div[data-testid="stTabs"] > div[role="tablist"] {
        position: sticky !important;
        top: 90px !important; /* 타이틀+캡션 아래 */
        z-index: 999 !important;
        background-color: #0B0B1A !important;
        padding-top: 15px !important;
        padding-bottom: 15px !important;
        border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    }

    /* 서브 탭 (메인 탭 안에 중첩된 탭) 고정 */
    div[data-testid="stTabs"] div[data-testid="stTabs"] > div[role="tablist"] {
        top: 165px !important; /* 메인 탭 아래 */
        z-index: 998 !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5) !important;
    }
    
    /* 4. st.tabs 활성 탭 (단정하고 고급스러운 인디고 블루 적용) */
    .stApp button[role="tab"][aria-selected="true"] {
        background: #6366F1 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35) !important;
        transform: translateY(-1px) !important;
    }
    
    .stApp button[role="tab"][aria-selected="true"] p,
    .stApp button[role="tab"][aria-selected="true"] span,
    .stApp button[role="tab"][aria-selected="true"] * {
        color: #FFFFFF !important;
        font-weight: 850 !important;
        font-size: 1.25rem !important; /* 대표님을 위한 대폭 확대 */
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* 5. 테이블 헤더 글자색 검정으로 지정하여 가독성 개선 */
    .stApp th, 
    .stApp th *, 
    .stApp .stDataFrame th, 
    .stApp div[data-testid="stDataFrame"] th, 
    .stApp div[data-testid="stDataFrame"] [role="columnheader"] p, 
    .stApp div[data-testid="stDataFrame"] [role="columnheader"] span {
        color: #FFFFFF !important;
        background-color: #1F2937 !important;
        font-weight: bold !important;
    }
    .stApp div[data-testid="stDataFrame"] {
        --textColor: #FFFFFF !important;
        --secondaryBackgroundColor: #111827 !important;
    }
    
    /* 6. 테이블 내부 텍스트 색상 및 상속 스타일 제어 */
    .stApp table td,
    .stApp table td *,
    .stApp table td p,
    .stApp table td span,
    .stApp table tr td,
    .stApp table tr td * {
        color: #E2E8F0 !important;
        font-weight: bold !important;
    }
    
    /* 7. 검색 입력창 글자색 지정 */
    .stApp div[data-testid="stTextInput"] input,
    .stApp input[type="text"],
    .stApp input {
        color: #FFFFFF !important;
        background-color: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }
    .stApp input::placeholder {
        color: #94A3B8 !important;
        opacity: 0.8 !important;
    }
    
    /* 8. 본문 st.button (검색, 초기화, 필터 해제 버튼 등)을 미니멀 플랫 스타일로 리디자인 */
    .stApp button:not([role="tab"]),
    .stApp button:not([role="tab"]) p,
    .stApp button:not([role="tab"]) span,
    .stApp button:not([role="tab"]) * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.02rem !important;
    }
    .stApp div[data-testid="stButton"] button {
        background-color: #1F2937 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
    }
    .stApp div[data-testid="stButton"] button:hover {
        background-color: #6366F1 !important; /* 인디고 포인트 */
        border-color: rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2) !important;
    }
    
    /* 9. 프리미엄 카드 스타일 (지표 카드 리디자인) */
    .premium-card {
        background: rgba(22, 28, 45, 0.75) !important;
        border: 1.5px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 14px !important;
        padding: 16px !important;
        margin-bottom: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
        transition: all 0.25s ease !important;
    }
    .premium-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4) !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.15) !important;
    }
    
    /* 카드 헤더 및 지표 텍스트 */
    .card-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #94A3B8;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 850;
        margin-bottom: 4px;
        letter-spacing: -0.5px;
    }
    
    /* 처방전 및 행동 예측 카드 */
    .tune-card {
        background: rgba(27, 20, 50, 0.75) !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        border-radius: 14px !important;
        padding: 22px !important;
        color: #E9D5FF !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2) !important;
    }
    .predict-card {
        background: rgba(17, 28, 55, 0.75) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-radius: 14px !important;
        padding: 22px !important;
        color: #93C5FD !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* 10. 최상단 stHeader 투명화 및 레이아웃 밀착 */
    header[data-testid="stHeader"], [data-testid="stHeader"] {
        background-color: transparent !important;
        background: transparent !important;
        height: 0px !important;
        min-height: 0px !important;
        border: none !important;
        box-shadow: none !important;
        overflow: visible !important;
        pointer-events: none !important;
    }
    header[data-testid="stHeader"] [data-testid="stHeaderActionElements"] {
        display: none !important;
    }
    [data-testid="stAppViewContainer"] {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
        display: flex !important;
        flex-direction: row !important;
    }
    [data-testid="stMain"] {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
        width: 100% !important;
    }
    [data-testid="stAppViewBlockContainer"], .block-container {
        padding-top: 0rem !important;
        margin-top: 0px !important;
        padding-bottom: 1.2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    h1 {
        margin-top: 0px !important;
        padding-top: 0px !important;
    }
    
    /* 11. 사이드바 다크테마 적용 */
    [data-testid="stSidebar"] {
        background-color: #060913 !important; /* 무광 매트 딥 그레이 */
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* 사이드바 기본 텍스트 선명화 */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4 {
        color: #E2E8F0 !important;
    }
    [data-testid="stSidebar"] strong {
        color: #FFFFFF !important;
    }
    
    /* 사이드바 로그아웃 버튼 */
    [data-testid="stSidebar"] button:not([role="tab"]) {
        background-color: #1F2030 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
    }
    .stApp [data-testid="stSidebar"] button:not([role="tab"]) *,
    .stApp [data-testid="stSidebar"] button:not([role="tab"]) p,
    .stApp [data-testid="stSidebar"] button:not([role="tab"]) span,
    .stApp [data-testid="stSidebar"] button:not([role="tab"]) div {
        color: #EF4444 !important; /* 차분한 경고 레드 색상으로 잘 보이게 지정 */
        font-weight: bold !important;
    }
    .stApp [data-testid="stSidebar"] button:not([role="tab"]):hover {
        background-color: #EF4444 !important;
        border-color: #EF4444 !important;
    }
    .stApp [data-testid="stSidebar"] button:not([role="tab"]):hover *,
    .stApp [data-testid="stSidebar"] button:not([role="tab"]):hover p,
    .stApp [data-testid="stSidebar"] button:not([role="tab"]):hover span {
        color: #FFFFFF !important;
    }
    
    /* 12. 파일 업로더 외부 글래스모피즘 박스 패키징 */
    .stApp [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background: rgba(22, 28, 45, 0.6) !important;
        border: 1.5px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 14px !important;
        padding: 14px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* 내부 드롭존 영역 리디자인 */
    .stApp [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: rgba(13, 17, 28, 0.7) !important;
        border: 1.5px dashed rgba(99, 102, 241, 0.25) !important;
        border-radius: 10px !important;
        padding: 24px 14px !important;
        transition: all 0.3s ease !important;
    }
    
    /* 드롭존 호버 시 피드백 */
    .stApp [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #6366F1 !important;
        background: rgba(13, 17, 28, 0.9) !important;
    }
    
    /* 파일 업로더 내부 버튼 (Upload 버튼) - 가로폭 100% 꽉 채우고 대표님을 위해 큼직하게 튜닝 */
    .stApp [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
        width: 100% !important; /* 가로폭 전체 차지하도록 설정 */
        margin-top: 12px !important;
        background: linear-gradient(135deg, #6366F1, #4F46E5) !important; /* 정돈된 인디고 그라디언트 */
        color: #FFFFFF !important;
        font-weight: 850 !important;
        font-size: 1.15rem !important; /* 대표님을 위한 크고 선명한 폰트 */
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 20px !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
        transition: all 0.25s ease !important;
        cursor: pointer !important;
    }
    
    .stApp [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button:hover {
        background: linear-gradient(135deg, #4F46E5, #6366F1) !important;
        box-shadow: 0 6px 18px rgba(99, 102, 241, 0.5) !important;
        transform: translateY(-1px) !important;
    }
    
    /* 업로더 내부 텍스트 가독성 */
    .stApp [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p,
    .stApp [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span {
        color: #E2E8F0 !important;
        font-weight: bold !important;
        font-size: 1.05rem !important;
    }
    .stApp [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p,
    .stApp [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small {
        color: #94A3B8 !important;
        font-size: 0.9rem !important; /* 큼직한 가이드 텍스트 */
        font-weight: 600 !important;
    }
    
    /* 계정 관리 expander 가독성 강화 */
    [data-testid="stSidebar"] details {
        background-color: #111422 !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
        padding: 6px !important;
    }
    [data-testid="stSidebar"] details summary {
        color: #818CF8 !important;
        font-weight: bold !important;
    }
    
    /* 13. 사이드바가 접혔을 때 좌측 상단에 나타나는 '사이드바 복원/열기' 버튼 리디자인 */
    header[data-testid="stHeader"] [data-testid="collapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] * {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
    }
    header[data-testid="stHeader"] [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] {
        position: fixed !important;
        top: 15px !important;
        left: 15px !important;
        background-color: #6366F1 !important;
        border: 1.5px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 50% !important;
        width: 42px !important;
        height: 42px !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
        z-index: 99999999 !important;
        cursor: pointer !important;
        pointer-events: auto !important;
        transition: all 0.25s ease !important;
        align-items: center !important;
        justify-content: center !important;
    }
    [data-testid="collapsedControl"] svg {
        fill: #FFFFFF !important;
        width: 22px !important;
        height: 22px !important;
    }
    [data-testid="collapsedControl"]:hover {
        background-color: #4F46E5 !important;
        transform: scale(1.08) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6) !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 로그인 및 계정 관리 로직
# -----------------------------------------------------------------------------
BASE_DIR = r"c:\Users\SEMION-A\쿠팡광고관리"
if not os.path.exists(BASE_DIR):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    # 기본 관리자 계정 반환 (기본 비밀번호: coupangmaster2026)
    return {"admin": "6feafae6f3d4f5618b2d9e2ce728601e5e37789c10eeb4a703e552c1efadab62"}

def save_users(users):
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"계정 저장 중 오류 발생: {e}")

def hash_pw(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

users = load_users()

# 로그아웃 처리
def logout():
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.rerun()

# -----------------------------------------------------------------------------
# 2-1. 로그인 화면 렌더링
# -----------------------------------------------------------------------------
if not st.session_state["logged_in"]:
    with st.sidebar:
        st.markdown("<div style='text-align: center; margin-top: 30px;'><h2>🚀</h2><h3 style='color: #60A5FA;'>쿠팡 광고 마스터 Web</h3><p style='color: #94A3B8; font-size: 0.9rem;'>시스템 사용을 위해 로그인을 진행해 주세요.</p></div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; margin-top: 80px;'><h1><span class='rocket-icon'>🚀</span> <span class='title-gradient'>쿠팡 광고 최적화 마스터 Web</span></h1></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h3 style='text-align: center; color: #60A5FA;'>🔒 계정 로그인</h3>", unsafe_allow_html=True)
        username = st.text_input("아이디(ID)", placeholder="아이디를 입력하세요")
        password = st.text_input("비밀번호(Password)", type="password", placeholder="비밀번호를 입력하세요")
        login_btn = st.button("로그인 실행", use_container_width=True)
        
        if login_btn:
            username = username.strip()
            password = password.strip()
            current_users = load_users()
            hashed = hash_pw(password)
            if username in current_users and current_users[username] == hashed:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"🎉 {username}님, 반갑습니다!")
                st.rerun()
            else:
                st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 데이터 및 메모 로드 공통 헬퍼
# -----------------------------------------------------------------------------
MEMOS_FILE = os.path.join(BASE_DIR, "ad_memos.json")
CLASSES_FILE = os.path.join(BASE_DIR, "keyword_classes.json")

def load_json(file_path, default):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"파일 저장 중 오류 발생 ({file_path}): {e}")

# -----------------------------------------------------------------------------
# 3-1. 성과 추이 탭 렌더링용 보조 헬퍼 및 이식 함수
# -----------------------------------------------------------------------------
def _parse_memo_date_to_key(date_str):
    ds = str(date_str).strip()
    try:
        if '-' in ds:
            parts = ds.split('-')
            year = int(parts[0])
            if year < 100:
                year += 2000
            return f"{year:04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        if len(ds) == 6 and ds.isdigit():
            year = 2000 + int(ds[0:2])
            month = int(ds[2:4])
            day = int(ds[4:6])
            return f"{year:04d}-{month:02d}-{day:02d}"
        if len(ds) == 8 and ds.isdigit():
            year = int(ds[0:4])
            month = int(ds[4:6])
            day = int(ds[6:8])
            return f"{year:04d}-{month:02d}-{day:02d}"
    except:
        pass
    return ds

def _memo_date_to_mmdd(date_str):
    ds = str(date_str).strip()
    try:
        if '-' in ds and len(ds) >= 10:
            parts = ds.split('-')
            return f"{int(parts[1]):02d}.{int(parts[2]):02d}"
        if len(ds) == 6 and ds.isdigit():
            return f"{int(ds[2:4]):02d}.{int(ds[4:6]):02d}"
        if len(ds) == 8 and ds.isdigit():
            return f"{int(ds[4:6]):02d}.{int(ds[6:8]):02d}"
    except:
        pass
    return None

def _fmt_val(v, kind):
    if kind == 'won':
        if abs(v) >= 10000: return f"{v/10000:.1f}만"
        elif abs(v) >= 1000: return f"{v/1000:.0f}k"
        if abs(v) >= 10000: return "{:.1f}만".format(v/10000)
        elif abs(v) >= 1000: return "{:.0f}k".format(v/1000)
        else: return "{:,}".format(int(v))
    elif kind == 'pct': return "{:.1f}%".format(v)
    elif kind == 'int': return "{:,}".format(int(v))
    return str(v)

def _annotate_smart(ax, xs, ys, color, kind, pe, fontsize=8, step=2):
    for i, v in enumerate(ys):
        if i % step != 0: continue
        if v == 0: continue
        offset_y = 10 if (i // step) % 2 == 0 else -14
        txt = _fmt_val(v, kind)
        ax.annotate(txt, (xs.iloc[i] if hasattr(xs, 'iloc') else xs[i], ys.iloc[i] if hasattr(ys, 'iloc') else ys[i]),
                    xytext=(0, offset_y), textcoords="offset points", ha='center',
                    color=color, weight='bold', fontsize=fontsize, path_effects=pe)

def show_pyplot_with_tooltip(fig):
    import io
    import json
    import re
    import streamlit as st
    import matplotlib.pyplot as plt
    
    # Apply dynamic bottom padding if there are memos to prevent clipping
    max_memo_len = getattr(fig, 'max_memo_len', 0)
    if max_memo_len > 0:
        # 1 char at fontsize 7-8 is about 8.5 points width when rotated
        text_length_inches = max_memo_len * (8.5 / 72.0)
        
        w, h = fig.get_size_inches()
        
        # The text is drawn starting from inside the axes (around 90% height) downwards.
        # This means there is already 'h * 0.8' inches of space available inside the figure!
        # We ONLY need to pad if the text length exceeds this available space.
                # For multi-row figures, h * 0.8 is completely wrong because the bottom axes 
        # only has a few inches of space before the figure ends.
        # Since most axes in this app are roughly 4-5 inches tall, the available space
        # inside the bottom-most axis is safely around 3.0 inches.
        available_space = 3.0
        padding_inches = text_length_inches - available_space
        
        if padding_inches > 0:
            padding_inches += 0.2  # tiny safety buffer
            fig.set_size_inches(w, h + padding_inches)
            
            # Adjust bottom margin to accommodate the padding without shrinking the axes
            fig.subplots_adjust(bottom=padding_inches / (h + padding_inches))
        
        # ALWAYS add an invisible rectangle at the very bottom of the figure (y=0)
        # so that bbox_inches='tight' does NOT delete our carefully calculated padding
        # or the default figure margins!
        import matplotlib.patches as patches
        rect = patches.Rectangle((0, 0), 1, 0.01, transform=fig.transFigure, alpha=0.0)
        fig.patches.append(rect)
    
    # 데이터프레임 JSON 획득
    df_json_str = getattr(fig, 'df_json', '[]')
    
    # memos 리스트 로드
    memos_list = load_json(MEMOS_FILE, [])
    memos_json_str = json.dumps(memos_list, ensure_ascii=False)
    
    f = io.BytesIO()
    fig.savefig(f, format='svg')  # Removed bbox_inches='tight' because it crops Korean text!
    svg_str = f.getvalue().decode('utf-8')
    plt.close(fig)
    
    # 툴팁 HTML/CSS/JS 템플릿
    tooltip_html = f"""
<style>
    .custom-chart-tooltip {{
        position: absolute;
        background: rgba(11, 11, 26, 0.96);
        border: 2px solid #C2185B;
        box-shadow: 0 0 15px rgba(194, 24, 91, 0.5);
        border-radius: 8px;
        color: #E2E8F0;
        padding: 10px 14px;
        font-family: 'Malgun Gothic', 'NanumGothic'', 'NanumGothic', 'Apple SD Gothic Neo', sans-serif;
        font-size: 11.5px;
        pointer-events: none;
        display: none;
        z-index: 99999;
        line-height: 1.45;
        min-width: 180px;
    }}
    [id^="hover_trigger_"], [id^="memo_line_"], [id^="memo_star_"], [id^="memo_text_"] {{
        cursor: pointer;
    }}
    [id^="memo_line_"]:hover, [id^="hover_trigger_"]:hover {{
        stroke-width: 3.0px !important;
        stroke: #C2185B !important;
        opacity: 0.8 !important;
    }}
</style>
<div id="chart-tooltip-box" class="custom-chart-tooltip"></div>
<script>
    (function() {{
        const tooltip = document.getElementById('chart-tooltip-box') || (function() {{
            const el = document.createElement('div');
            el.id = 'chart-tooltip-box';
            el.className = 'custom-chart-tooltip';
            document.body.appendChild(el);
            return el;
        }})();
        
        // 차트용 원본 데이터 및 메모 데이터 복원
        const rawData = {df_json_str};
        const memosData = {memos_json_str};
        
        // 메모의 날짜 형식을 MM.DD로 변환하는 도우미
        function memoDateToMMDD(dateStr) {{
            if (!dateStr) return "";
            const clean = dateStr.trim();
            if (clean.includes('-')) {{
                const parts = clean.split('-');
                if (parts.length >= 3) return `${{parts[1]}}.${{parts[2]}}`;
            }}
            return "";
        }}
        
        // 1) 마우스 호버 트리거 및 메모선 이벤트 바인딩
        document.querySelectorAll('[id^="hover_trigger_"], [id^="memo_line_"], [id^="memo_star_"], [id^="memo_text_"]').forEach(el => {{
            const parts = el.id.split('_');
            let mmdd = "";
            
            if (el.id.startsWith("hover_trigger_")) {{
                mmdd = parts[2];
            }} else {{
                // memo_line_YYYY-MM-DD_text 형식
                const dateYmd = parts[2];
                mmdd = memoDateToMMDD(dateYmd);
            }}
            
            if (!mmdd) return;
            
            el.addEventListener('mousemove', (e) => {{
                // 1) 데이터 매칭
                const record = rawData.find(r => {{
                    if (!r.date_s) return false;
                    return r.date_s.trim() === mmdd.trim();
                }});
                
                // 2) 메모 매칭
                const dayMemos = memosData.filter(m => memoDateToMMDD(m.date) === mmdd.trim());
                
                let contentHtml = `<div style="text-align: left;">`;
                contentHtml += `<strong style="font-size: 12.5px; color: #E2E8F0; border-bottom: 1px solid #C2185B; padding-bottom: 4px; display: block; margin-bottom: 6px;">📅 ${{mmdd}} 성과 요약</strong>`;
                
                let hasMetric = false;
                if (record) {{
                    if (record.spend !== undefined) {{
                        contentHtml += `🔹 광고비: <span style="color: #FBBF24; font-weight: bold;">${{parseInt(record.spend).toLocaleString()}}원</span><br/>`;
                        hasMetric = true;
                    }}
                    if (record.sales !== undefined) {{
                        contentHtml += `📈 광고매출: <span style="color: #34D399; font-weight: bold;">${{parseInt(record.sales).toLocaleString()}}원</span><br/>`;
                        hasMetric = true;
                    }}
                    if (record.ROAS !== undefined) {{
                        contentHtml += `🎯 ROAS: <span style="color: #FB923C; font-weight: bold;">${{parseFloat(record.ROAS).toFixed(2)}}%</span><br/>`;
                        hasMetric = true;
                    }}
                    if (record.orders !== undefined) {{
                        contentHtml += `🛍️ 주문건수: <span style="color: #60A5FA; font-weight: bold;">${{parseInt(record.orders).toLocaleString()}}건</span><br/>`;
                        hasMetric = true;
                    }}
                    if (record.click !== undefined) {{
                        contentHtml += `🖱️ 클릭수: <span style="color: #60A5FA; font-weight: bold;">${{parseInt(record.click).toLocaleString()}}회</span><br/>`;
                        hasMetric = true;
                    }}
                    if (record.CTR !== undefined) {{
                        contentHtml += `📊 클릭률(CTR): <span style="color: #FB923C; font-weight: bold;">${{parseFloat(record.CTR).toFixed(2)}}%</span><br/>`;
                        hasMetric = true;
                    }}
                    if (record.CVR !== undefined) {{
                        contentHtml += `🔄 전환율(CVR): <span style="color: #FB923C; font-weight: bold;">${{parseFloat(record.CVR).toFixed(2)}}%</span><br/>`;
                        hasMetric = true;
                    }}
                }}
                
                if (!hasMetric) {{
                    contentHtml += `<span style="color: #94A3B8; font-style: italic;">조회 데이터 없음</span><br/>`;
                }}
                
                // 3) 메모 리스트 출력
                if (dayMemos.length > 0) {{
                    contentHtml += `<div style="border-top: 1px dashed #555; margin-top: 6px; padding-top: 6px;">`;
                    contentHtml += `<span style="color: #FFD700; font-weight: bold;">📝 등록된 메모 (${{dayMemos.length}}개)</span><br/>`;
                    dayMemos.forEach((m, idx) => {{
                        contentHtml += `<span style="color: #FFD700; font-size: 11px;">${{idx + 1}}. ${{m.memo}}</span><br/>`;
                    }});
                    contentHtml += `</div>`;
                }}
                
                contentHtml += `</div>`;
                
                // 툴팁 위치 제어 및 노출
                tooltip.style.display = 'block';
                tooltip.innerHTML = contentHtml;
                tooltip.style.left = (e.pageX + 15) + 'px';
                tooltip.style.top = (e.pageY + 15) + 'px';
            }});
            
            el.addEventListener('mouseleave', () => {{
                tooltip.style.display = 'none';
            }});
        }});
    }})();
</script>
"""
    # SVG 반응형 스타일 적용 (가로폭 100% 꽉 채우기)
    svg_str = re.sub(r'\bwidth="[^"]+"', '', svg_str, count=1)
    svg_str = re.sub(r'\bheight="[^"]+"', '', svg_str, count=1)
    
    import streamlit.components.v1 as components
    import re
    # Extract width and height from viewBox to correctly limit max-width
    svg_viewbox_match = re.search(r'viewBox="([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"', svg_str)
    if svg_viewbox_match:
        width_pt = float(svg_viewbox_match.group(3))
        height_pt = float(svg_viewbox_match.group(4))
        width_px = int(width_pt * 1.333)
        height_val = int(height_pt * 1.333) + 30
        
        # We MUST bound the max-width to its native width_px, otherwise on huge monitors 
        # it will scale up infinitely but the iframe height_val is fixed, leading to bottom cropping!
        style_injection = f'<svg style="width: 100%; max-width: {width_px}px; height: auto; display: block; margin: 0 auto;"'
    else:
        # Fallback
        height_val = int(fig.get_figheight() * fig.dpi) + 30
        style_injection = '<svg style="width: 100%; height: auto; display: block; margin: 0 auto;"'
        
    svg_str = re.sub(r'<svg\b', style_injection, svg_str, count=1)
    components.html(svg_str + tooltip_html, height=height_val, scrolling=False)


def render_ai_diagnosis_html(d):
    if not d:
        return ""
    
    html = []
    # 1. 👑 [최상단] AI 최종 종합 판정 대왕 썸머리 카드
    html.append(textwrap.dedent(f"""
  <div style="background: #1E1E38; border: 2px solid #60A5FA; border-radius: 18px; padding: 25px; margin-bottom: 20px;">
      <h2 style="font-family: 'Malgun Gothic', 'NanumGothic', sans-serif; font-size: 22px; font-weight: bold; color: #FBBF24; margin-top: 0; margin-bottom: 15px;">
            👑 AI 최종 종합 판정 (Summary)
        </h2>
      <p style="font-family: 'Malgun Gothic', 'NanumGothic', sans-serif; font-size: 15px; font-weight: bold; color: white; line-height: 1.6; white-space: pre-line; margin: 0;">
            {d['briefing']}
        </p>
    </div>
    """))
    
    # 2. [그 아래] 10개 차트 개별 진단 리포트 카드 자동 생성
    for adv in d.get('advice', []):
        solutions_html = ""
        for s in adv.get('solution', []):
            solutions_html += f'<div style="font-family: \'Malgun Gothic\', sans-serif; font-size: 13px; color: #94A3B8; margin-bottom: 6px; display: flex; align-items: flex-start; gap: 6px;"><span>✔️</span><span>{s}</span></div>'
            
        trend_html = ""
        trend_text = adv.get('trend_insight', '')
        if trend_text:
            trend_html = f"""
          <div style="background: #0F1A2E; border: 1px solid #F59E0B; border-radius: 10px; padding: 12px; margin-top: 10px;">
              <div style="font-family: 'Malgun Gothic', 'NanumGothic', sans-serif; font-size: 13px; font-weight: bold; color: #FDE68A; line-height: 1.5; white-space: pre-line;">
                    {trend_text}
                </div>
            </div>
            """
            
        html.append(textwrap.dedent(f"""
      <div style="background: #1A1A2E; border: 1.5px solid #2E2E4A; border-radius: 15px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);">
          <h3 style="font-family: 'Malgun Gothic', 'NanumGothic', sans-serif; font-size: 18px; font-weight: bold; color: #60A5FA; margin-top: 0; margin-bottom: 12px;">
                {adv['subject']}
            </h3>
          <p style="font-family: 'Malgun Gothic', 'NanumGothic', sans-serif; font-size: 14px; font-weight: bold; color: #E2E8F0; margin-bottom: 8px;">
                💡 분석: {adv['meaning']}
            </p>
          <p style="font-family: 'Malgun Gothic', 'NanumGothic', sans-serif; font-size: 13px; color: #A7F3D0; margin-bottom: 12px; line-height: 1.5; white-space: pre-line;">
                📖 이렇게 보면 좋은 거 (초등생도 1초 이해!):<br>
                {adv['easy_story']}
            </p>
          <div style="background: #0D0D21; border-radius: 10px; padding: 12px; margin-bottom: 5px;">
                {solutions_html}
            </div>
            {trend_html}
        </div>
        """))
        
    return "\n".join(line.strip() for line in "\n".join(html).split("\n"))


def render_dash_kpi_gauge_streamlit(overall):
    """⚡ 핵심 KPI 건강도: 4대 지표를 직관적 게이지로 표시"""
    plt.rcParams['font.family'] = 'NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic'
    pe = [path_effects.withStroke(linewidth=2, foreground='black')]
    
    fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=95)
    fig.patch.set_facecolor('#0B0B1A')
    
    ax.set_facecolor('#0B0B1A')
    ax.set_title("광고 핵심 KPI 건강도", color='white', pad=40, loc='center',
                 fontdict={'size': 16, 'weight': 'bold', 'family': 'NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic'})
    ax.text(0.5, 1.01, '초록=양호 / 노랑=주의 / 빨강=위험 (기준: 업계 평균)',
            transform=ax.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=11, style='italic')
    
    kpis = [
        ('ROAS', overall['ROAS'], 330, 1000, '%', False),
        ('CTR', overall['CTR'], 0.5, 2.0, '%', False),
        ('CVR', overall['CVR'], 5.0, 20.0, '%', False),
        ('CPC', overall['CPC'], 300, 800, '원', True),
    ]
    
    ax.set_xlim(0, 1.15)
    ax.set_ylim(-0.5, len(kpis) - 0.5)
    ax.set_yticks(range(len(kpis)))
    ax.set_yticklabels([k[0] for k in kpis][::-1], color='white', fontsize=13, weight='bold')
    ax.tick_params(axis='x', bottom=False, labelbottom=False)
    ax.tick_params(axis='y', left=False)
    for sp in ax.spines.values(): 
        sp.set_visible(False)
    
    for idx, (name, val, good, max_v, unit, lower_better) in enumerate(kpis):
        y = len(kpis) - 1 - idx
        fill = min(val / max_v, 1.0) if max_v > 0 else 0
        
        if lower_better:
            if val <= good: color = '#10B981'
            elif val <= good * 2: color = '#F59E0B'
            else: color = '#EF4444'
        else:
            if val >= good: color = '#10B981'
            elif val >= good * 0.5: color = '#F59E0B'
            else: color = '#EF4444'
        
        # 배경 바
        ax.barh(y, 1.0, height=0.45, color='#1F2937', edgecolor='none')
        # 채움 바
        bars = ax.barh(y, fill, height=0.45, color=color, edgecolor='none', alpha=0.85)
        
        # 값 표시
        if unit == '원':
            val_text = f'{int(val):,}{unit}'
        else:
            val_text = f'{val:.1f}{unit}'
        
        ax.text(fill + 0.03 if fill < 0.85 else fill - 0.03, y, val_text, 
                va='center', ha='left' if fill < 0.85 else 'right',
                color='white', fontsize=11, weight='bold', path_effects=pe)
        
        # 기준선
        good_pos = min(good / max_v, 1.0) if max_v > 0 else 0
        ax.axvline(x=good_pos, ymin=(y - 0.2 + 0.5) / len(kpis), ymax=(y + 0.2 + 0.5) / len(kpis),
                  color='#FFD700', linewidth=1.5, linestyle='--', alpha=0.7)
    
    fig.tight_layout(rect=[0, 0.02, 1, 0.88])
    show_pyplot_with_tooltip(fig)
    plt.close(fig)


def render_dashboard_pie_streamlit(br_df):
    plt.rcParams['font.family'] = 'NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
    pe = [path_effects.withStroke(linewidth=3, foreground='black')]
    
    fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=95)
    fig.patch.set_facecolor('#0B0B1A')
    ax.set_facecolor('#0B0B1A')
    ax.set_title("노출 영역별 상세 성과", color='white', pad=40, loc='center',
                 fontdict={'size': 16, 'weight': 'bold', 'family': 'NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic'})
    ax.text(0.5, 1.01, '광고비(막대) 대비 클릭수와 주문수(선) 효율을 확인하세요',
            transform=ax.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=11, style='italic')
    
    if br_df is not None and not br_df.empty:
        target_regions = ['검색 영역', '비검색 영역', '오디언스 플러스(외부 채널) - Product Ad']
        s_dict = {reg: {'spend': 0.0, 'click': 0.0, 'orders': 0.0} for reg in target_regions}
        
        raw_s = br_df.groupby('region').agg({'spend': 'sum', 'click': 'sum', 'orders': 'sum'})
        
        for r_name, row in raw_s.iterrows():
            r_name_str = str(r_name)
            matched = False
            
            if '비검색' in r_name_str:
                s_dict['비검색 영역']['spend'] += row['spend']
                s_dict['비검색 영역']['click'] += row['click']
                s_dict['비검색 영역']['orders'] += row['orders']
                matched = True
            elif '검색' in r_name_str:
                s_dict['검색 영역']['spend'] += row['spend']
                s_dict['검색 영역']['click'] += row['click']
                s_dict['검색 영역']['orders'] += row['orders']
                matched = True
            elif '오디언스' in r_name_str or '외부 채널' in r_name_str or '오피니언' in r_name_str:
                s_dict['오디언스 플러스(외부 채널) - Product Ad']['spend'] += row['spend']
                s_dict['오디언스 플러스(외부 채널) - Product Ad']['click'] += row['click']
                s_dict['오디언스 플러스(외부 채널) - Product Ad']['orders'] += row['orders']
                matched = True
            
            if not matched:
                s_dict[r_name_str] = {
                    'spend': row['spend'],
                    'click': row['click'],
                    'orders': row['orders']
                }
        
        s_df = pd.DataFrame(s_dict).T
        
        labels = []
        for name in s_df.index:
            n_str = str(name)
            if '오디언스' in n_str or '외부 채널' in n_str or '오피니언' in n_str:
                labels.append('오피니언 영역')
            elif len(n_str) > 6:
                labels.append(n_str[:6] + '..')
            else:
                labels.append(n_str)
        
        colors = ['#EC4899', '#8B5CF6', '#3B82F6', '#F59E0B', '#10B981']
        bars = ax.bar(labels, s_df['spend'].values, color=colors[:len(s_df)], width=0.4, edgecolor='none', alpha=0.7)
        
        ax.set_ylabel('광고비 (원)', color='#EC4899', size=9, weight='bold', fontfamily='NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic')
        ax.tick_params(axis='y', labelcolor='#EC4899', labelsize=8)
        ax.set_ylim(0, max(s_df['spend'].max() * 1.25, 10000))
        
        ax2 = ax.twinx()
        
        line_click = ax2.plot(labels, s_df['click'].values, color='#3B82F6', marker='o', linewidth=2, markersize=5,
                              label='— 클릭수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        
        line_orders = ax2.plot(labels, s_df['orders'].values, color='#10B981', marker='s', linewidth=2, markersize=5,
                               label='— 주문수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        
        ax2.set_ylabel('클릭수(회) / 주문수(건)', color='white', size=9, weight='bold', fontfamily='NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic')
        ax2.tick_params(axis='y', labelcolor='white', labelsize=8)
        ax2.set_ylim(0, max(s_df['click'].max() * 1.3, 10))
        
        for i in range(len(s_df)):
            c_val = s_df['click'].iloc[i]
            ax2.annotate(f"{int(c_val)}회", (i, c_val), xytext=(-5, 8), textcoords="offset points",
                         color='#3B82F6', weight='bold', fontsize=8, path_effects=pe, ha='center')
            
            o_val = s_df['orders'].iloc[i]
            ax2.annotate(f"{int(o_val)}건", (i, o_val), xytext=(5, -12), textcoords="offset points",
                         color='#10B981', weight='bold', fontsize=8, path_effects=pe, ha='center')
        
        import matplotlib.patches as mpatches
        patch_spend = mpatches.Patch(color='#EC4899', alpha=0.7, label='■ 광고비')
        
        h1 = [patch_spend]
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, ['■ 광고비'] + l2, loc='upper right', fontsize=8,
                  facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
        
        ax.tick_params(axis='x', labelcolor='white', labelsize=10, rotation=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#1F2937')
        ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.3)
        
    else:
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center', color='#6B7280', 
               fontsize=14, fontfamily='NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic')
    
    fig.tight_layout(rect=[0, 0, 1, 0.82])
    show_pyplot_with_tooltip(fig)
    plt.close(fig)


def render_kpi_summary_cards_streamlit(overall, region_summary):
    if not overall:
        return
        
    def normalize_region(name):
        s = str(name).replace(' ', '')
        if '검색' in s and '비검색' not in s and '비' not in s[:1]:
            return '검색'
        elif '비검색' in s or '상세' in s or '추천' in s or s == '-':
            return '비검색'
        elif '오디언스' in s or '오프사이트' in s or 'off' in s.lower() or '외부' in s:
            return '오디언스'
        return s
        
    region_data = {'검색': {}, '비검색': {}, '오디언스': {}}
    if region_summary is not None and not region_summary.empty:
        rs = region_summary.copy()
        rs['norm_region'] = rs['region'].apply(normalize_region)
        for rn in ['검색', '비검색', '오디언스']:
            rr = rs[rs['norm_region'] == rn]
            if not rr.empty:
                region_data[rn] = {
                    'spend': rr['spend'].sum(), 'sales': rr['sales'].sum(),
                    'orders': rr['orders'].sum(), 'imp': rr['imp'].sum(),
                    'click': rr['click'].sum(),
                }
                rd = region_data[rn]
                rd['ROAS'] = (rd['sales'] / rd['spend'] * 100) if rd['spend'] > 0 else 0
                rd['CTR'] = (rd['click'] / rd['imp'] * 100) if rd['imp'] > 0 else 0
                rd['CVR'] = (rd['orders'] / rd['click'] * 100) if rd['click'] > 0 else 0
            else:
                region_data[rn] = {'spend': 0, 'sales': 0, 'orders': 0, 'imp': 0, 'click': 0, 'ROAS': 0, 'CTR': 0, 'CVR': 0}

    metrics = [
        ("전체 광고비", "spend", "원"), ("실현 광고비", "spend", "원"),
        ("전환 매출", "sales", "원"), ("전체 매출", "sales", "원"),
        ("전체 판매수", "orders", "회"), ("노출수", "imp", "회"),
        ("클릭수", "click", "회"), ("클릭률", "CTR", "%"),
        ("전환 판매수", "orders", "회"), ("전환 주문수", "orders", "회"),
        ("수익률(ROAS)", "ROAS", "%"), ("전환율(CVR)", "CVR", "%")
    ]
    
    def _sub_label(k, u):
        parts = []
        for rn in ['검색', '비검색', '오디언스']:
            rd = region_data.get(rn, {})
            rv = rd.get(k, 0.0)
            if u == "원":
                parts.append(f"©{rn[:2]} {int(rv):,}")
            elif u == "%":
                parts.append(f"©{rn[:2]} {rv:.2f}%")
            else:
                parts.append(f"©{rn[:2]} {int(rv):,}")
        return ' / '.join(parts)

    for r in range(2):
        cols = st.columns(6)
        for c in range(6):
            idx = r * 6 + c
            t, k, u = metrics[idx]
            val = overall.get(k, 0.0)
            if "광고비" in t:
                color = "#FBBF24"
            elif "매출" in t:
                color = "#34D399"
            elif t in ["전체 판매수", "노출수", "클릭수", "전환 판매수", "전환 주문수"]:
                color = "#60A5FA"
            else:
                color = "#FB923C"
                
            if u == "원" or u == "회": 
                text = f"{int(val):,} {u}"
            else: 
                text = f"{val:.2f} {u}"
                
            sub_text = _sub_label(k, u)
            with cols[c]:
                st.markdown(f"""
              <div class="premium-card" style="padding: 12px; margin-bottom: 10px; border-color: #3B82F6;">
                  <div class="card-header" style="font-size: 0.85rem; text-align: center; margin-bottom: 4px;">{t}</div>
                  <div class="metric-value" style="color: {color}; font-size: 1.35rem; text-align: center; margin-bottom: 2px;">{text}</div>
                  <div style="font-size: 0.65rem; color: #94A3B8; text-align: center; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{sub_text}</div>
                </div>
                """, unsafe_allow_html=True)


def render_magnifier_diagnosis_streamlit(df, by_region_df=None):
    def normalize_region(name):
        s = str(name).replace(' ', '')
        if '검색' in s and '비검색' not in s and '비' not in s[:1]:
            return '검색 영역'
        elif '비검색' in s or '상세' in s or '추천' in s or s == '-':
            return '비검색 영역'
        elif '오디언스' in s or '오프사이트' in s or 'off' in s.lower() or '외부' in s:
            return '오디언스'
        return s
        
    region_colors = {
        '검색 영역': ('#3B82F6', '🔵'),
        '비검색 영역': ('#F59E0B', '🟡'),
        '오디언스': ('#10B981', '🟢')
    }
    region_labels = ['검색 영역', '비검색 영역', '오디언스']
    
    analysis_targets = []
    analysis_targets.append(('📊 전체 합산', df, '#EC4899'))
    
    if by_region_df is not None and not by_region_df.empty:
        rdf = by_region_df.copy()
        rdf['norm_region'] = rdf['region'].apply(normalize_region)
        
        for region_name in region_labels:
            rdata = rdf[rdf['norm_region'] == region_name].copy()
            if rdata.empty:
                continue
            rdata = rdata.groupby(['date_s']).agg({
                'imp': 'sum', 'click': 'sum', 'spend': 'sum',
                'sales': 'sum', 'orders': 'sum'
            }).reset_index()
            rdata['CTR'] = np.where(rdata['imp'] > 0, (rdata['click'] / rdata['imp']) * 100, 0)
            rdata['CVR'] = np.where(rdata['click'] > 0, (rdata['orders'] / rdata['click']) * 100, 0)
            rdata['ROAS'] = np.where(rdata['spend'] > 0, (rdata['sales'] / rdata['spend']) * 100, 0)
            
            rc, emoji = region_colors.get(region_name, ('#FFFFFF', '⚪'))
            analysis_targets.append((f'{emoji} {region_name}', rdata, rc))

    st.markdown("""
<style>
    .diag-container {
        background-color: #10102B;
        border: 2px solid #EC4899;
        border-radius: 15px;
        padding: 20px;
        margin-top: 15px;
        margin-bottom: 25px;
        box-shadow: 0 0 15px rgba(236, 72, 153, 0.2);
    }
    .diag-title-neon {
        font-size: 1.25rem;
        font-weight: bold;
        color: #F472B6;
        margin-bottom: 18px;
        font-family: 'Malgun Gothic', 'NanumGothic', sans-serif;
    }
    .diag-subcard {
        background-color: #1A1A2E;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
    }
    .diag-target-name {
        font-size: 1rem;
        font-weight: bold;
        margin-bottom: 8px;
        font-family: 'Malgun Gothic', 'NanumGothic', sans-serif;
    }
    .diag-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin-bottom: 10px;
    }
    .diag-badge {
        background-color: #1A1D36;
        border-radius: 6px;
        padding: 8px;
        text-align: center;
        font-size: 0.85rem;
        font-weight: bold;
        font-family: 'Malgun Gothic', 'NanumGothic', sans-serif;
    }
    .diag-verdict {
        font-size: 0.88rem;
        font-weight: bold;
        margin-top: 8px;
        font-family: 'Malgun Gothic', 'NanumGothic', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

    diag_html = '<div class="diag-container">'
    diag_html += '<div class="diag-title-neon">🔑 AI 광고효율 돋보기 1초 진단 처방전 (영역별 분석)</div>'
    
    has_target = False
    for target_name, target_df, border_color in analysis_targets:
        n_days = len(target_df)
        if n_days < 2:
            continue
            
        has_target = True
        split_idx = max(1, n_days - 3) if n_days >= 4 else 1
        recent_df = target_df.iloc[split_idx:]
        prev_df = target_df.iloc[:split_idx]
        
        recent_roas = recent_df['ROAS'].mean()
        prev_roas = prev_df['ROAS'].mean()
        recent_imp = recent_df['imp'].mean()
        prev_imp = prev_df['imp'].mean()
        recent_ctr = recent_df['CTR'].mean()
        prev_ctr = prev_df['CTR'].mean()
        recent_cvr = recent_df['CVR'].mean()
        prev_cvr = prev_df['CVR'].mean()
        
        chg_roas = ((recent_roas - prev_roas) / prev_roas * 100) if prev_roas > 0 else (100.0 if recent_roas > 0 else 0)
        chg_imp = ((recent_imp - prev_imp) / prev_imp * 100) if prev_imp > 0 else (100.0 if recent_imp > 0 else 0)
        chg_ctr = ((recent_ctr - prev_ctr) / prev_ctr * 100) if prev_ctr > 0 else (100.0 if recent_ctr > 0 else 0)
        chg_cvr = ((recent_cvr - prev_cvr) / prev_cvr * 100) if prev_cvr > 0 else (100.0 if recent_cvr > 0 else 0)
        
        lamp_imp = "위험" if chg_imp < -20 else ("주의" if chg_imp < -5 else "양호")
        lamp_ctr = "위험" if chg_ctr < -20 else ("주의" if chg_ctr < -5 else "양호")
        lamp_cvr = "위험" if chg_cvr < -20 else ("주의" if chg_cvr < -5 else "양호")
        
        if chg_roas < 0:
            min_val = min(chg_imp, chg_ctr, chg_cvr)
            if min_val == chg_ctr:
                verdict = "⚠️ 클릭률 급감이 주요 원인! 썸네일/상품명 교체 검토 필요"
            elif min_val == chg_cvr:
                verdict = "⚠️ 전환율 하락이 주요 원인! 상세페이지/가격/리뷰 점검 필요"
            else:
                verdict = "⚠️ 노출 부족이 주요 원인! 입찰가 인상 검토 필요"
            v_color = "#F87171"
        else:
            max_val = max(chg_imp, chg_ctr, chg_cvr)
            if max_val == chg_ctr:
                verdict = "🟢 클릭률 상승세! 썸네일 전략이 효과적"
            elif max_val == chg_cvr:
                verdict = "🟢 전환율 상승세! 상세페이지 설득력 우수"
            else:
                verdict = "🟢 노출 증가세! 입찰 전략 안정적"
            v_color = "#34D399"
            
        diag_html += f"""
<div class="diag-subcard" style="border: 1px solid {border_color};">
  <div class="diag-target-name" style="color: {border_color};">{target_name}</div>
  <div class="diag-grid">
      <div class="diag-badge" style="color: #00E5FF;">🔹 노출수 [{lamp_imp}] ({chg_imp:+.1f}%)</div>
      <div class="diag-badge" style="color: #FB923C;">🔸 클릭률 [{lamp_ctr}] ({chg_ctr:+.1f}%)</div>
      <div class="diag-badge" style="color: #10B981;">🔹 전환율 [{lamp_cvr}] ({chg_cvr:+.1f}%)</div>
      <div class="diag-badge" style="color: #FF00FF;">🔸 ROAS [{'양호' if chg_roas>=0 else '위험'}] ({chg_roas:+.1f}%)</div>
    </div>
  <div class="diag-verdict" style="color: {v_color};">{verdict}</div>
</div>
"""
        
    diag_html += '</div>'
    if has_target:
        st.markdown(diag_html, unsafe_allow_html=True)


def _draw_memo_vlines(axes, date_labels, pe, memos, fontsize=8):
    # 1) 모든 날짜에 대해 마우스 호버 감지용 투명 가이드라인 생성 (gid 지정)
    for ax in axes:
        for mmdd in date_labels:
            line = ax.axvline(x=mmdd, color='cyan', linewidth=10, alpha=0.001, zorder=1)
            line.set_gid(f"hover_trigger_{mmdd}")
            
    if not memos:
        return
        
    if axes:
        axes[0].figure.has_memos = True
        
        # Only calculate max length for memos that are actually drawn on this figure!
        valid_memos = [m for m in memos if _memo_date_to_mmdd(m['date']) in date_labels]
        if valid_memos:
            current_max = max([len(m.get('memo', '')) for m in valid_memos])
        else:
            current_max = 0
            
        # Update figure's max_memo_len (keep max if called multiple times)
        existing_max = getattr(axes[0].figure, 'max_memo_len', 0)
        axes[0].figure.max_memo_len = max(existing_max, current_max)
        
    memo_colors = ['#FFD700', '#FF6B6B', '#69DB7C', '#74C0FC', '#DA77F2']
    color_idx = 0
    
    sorted_memos = sorted(memos, key=lambda m: _parse_memo_date_to_key(m['date']))
    seen_mmdd_counts = {}
    
    for m in sorted_memos:
        memo_date = m['date']
        memo_text = m['memo']
        
        mmdd = _memo_date_to_mmdd(memo_date)
        if mmdd is None or mmdd not in date_labels:
            continue
            
        color = memo_colors[color_idx % len(memo_colors)]
        color_idx += 1
        
        mmdd_count = seen_mmdd_counts.get(mmdd, 0)
        seen_mmdd_counts[mmdd] = mmdd_count + 1
        
        if mmdd_count == 0:
            ha_val = 'right'
            summary = memo_text
        elif mmdd_count == 1:
            ha_val = 'left'
            summary = memo_text
        else:
            padding_spaces = "   " * (mmdd_count // 2)
            if mmdd_count % 2 == 0:
                ha_val = 'right'
                summary = memo_text + padding_spaces
            else:
                ha_val = 'left'
                summary = padding_spaces + memo_text
                
        for ax in axes:
            line = ax.axvline(x=mmdd, color=color, linewidth=1.2, linestyle=':', alpha=0.75, zorder=5)
            
            # Y축 상단(0.96 위치)에 노란색/해당 색상의 별마커(★) 추가
            ylim = ax.get_ylim()
            y_star = ylim[0] + (ylim[1] - ylim[0]) * 0.96
            star = ax.plot(mmdd, y_star, marker='*', color=color, markersize=8, zorder=6)[0]
            
            safe_text = memo_text.replace(' ', '_').replace('"', '').replace("'", "")
            line.set_gid(f"memo_line_{memo_date}_{safe_text}")
            star.set_gid(f"memo_star_{memo_date}_{safe_text}")
            
            y_pos = ylim[0] + (ylim[1] - ylim[0]) * 0.90
            txt = ax.text(mmdd, y_pos, summary, rotation=90, va='top', ha=ha_val,
                   color=color, fontsize=max(6, fontsize-1), weight='bold', alpha=0.85,
                   path_effects=pe, fontfamily='NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic')
            txt.set_gid(f"memo_text_{memo_date}_{safe_text}")


def render_kpi_summary_cards_streamlit(overall, region_summary):
    if not overall:
        return
        
    def normalize_region(name):
        s = str(name).replace(' ', '')
        if '검색' in s and '비검색' not in s and '비' not in s[:1]:
            return '검색'
        elif '비검색' in s or '상세' in s or '추천' in s or s == '-':
            return '비검색'
        elif '오디언스' in s or '오프사이트' in s or 'off' in s.lower() or '외부' in s:
            return '오디언스'
        return s
        
    region_data = {'검색': {}, '비검색': {}, '오디언스': {}}
    if region_summary is not None and not region_summary.empty:
        rs = region_summary.copy()
        rs['norm_region'] = rs['region'].apply(normalize_region)
        for region_name in ['검색', '비검색', '오디언스']:
            rr = rs[rs['norm_region'] == region_name]
            if not rr.empty:
                region_data[region_name] = {
                    'spend': rr['spend'].sum(), 'sales': rr['sales'].sum(),
                    'orders': rr['orders'].sum(), 'imp': rr['imp'].sum(),
                    'click': rr['click'].sum(),
                }
                rd = region_data[region_name]
                rd['ROAS'] = (rd['sales'] / rd['spend'] * 100) if rd['spend'] > 0 else 0
                rd['CTR'] = (rd['click'] / rd['imp'] * 100) if rd['imp'] > 0 else 0
                rd['CVR'] = (rd['orders'] / rd['click'] * 100) if rd['click'] > 0 else 0

    metrics = [
        ("전체 광고비", overall['spend'], "원", "spend"),
        ("실현 광고비", overall['spend'], "원", "spend"),
        ("전환 매출", overall['sales'], "원", "sales"),
        ("전체 매출", overall['sales'], "원", "sales"),
        ("전체 판매수", overall.get('total_qty', 0), "회", "orders"),
        ("노출수", overall['imp'], "회", "imp"),
        ("클릭수", overall['click'], "회", "click"),
        ("클릭률", overall['CTR'], "%", "CTR"),
        ("전환 판매수", overall.get('conv_qty', 0), "회", "orders"),
        ("전환 주문수", overall['orders'], "회", "orders"),
        ("수익률(ROAS)", overall['ROAS'], "%", "ROAS"),
        ("전환율(CVR)", overall['CVR'], "%", "CVR")
    ]
    
    region_emojis = {'검색': '🔵', '비검색': '🟡', '오디언스': '🟢'}
    
    st.markdown("### 📊 광고 성과 요약 지표")
    
    for r in range(2):
        cols = st.columns(6)
        for c in range(6):
            idx = r * 6 + c
            t, val, u, k = metrics[idx]
            
            if "광고비" in t:
                color = "#FBBF24"
            elif "매출" in t:
                color = "#34D399"
            elif t in ["전체 판매수", "노출수", "클릭수", "전환 판매수", "전환 주문수"]:
                color = "#60A5FA"
            else:
                color = "#FB923C"
                
            if u == "원" or u == "회": 
                text = f"{int(val):,} {u}"
            else: 
                text = f"{val:.2f} {u}"
                
            parts = []
            for rn in ['검색', '비검색', '오디언스']:
                rd = region_data.get(rn, {})
                rv = rd.get(k, 0.0)
                emoji = region_emojis.get(rn, '⚪')
                if u == "원" or u == "회":
                    parts.append(f"{emoji}{rn[:2]} {int(rv):,}")
                else:
                    parts.append(f"{emoji}{rn[:2]} {rv:.2f}%")
            
            sub_label = ' / '.join(parts)
            
            with cols[c]:
                st.markdown(f"""
              <div class="premium-card" style="padding: 10px; margin-bottom: 10px; border-width: 1.5px; border-color: #3B82F6;">
                  <div style="font-size: 0.75rem; font-weight: bold; color: #E2E8F0; text-align: center;">{t}</div>
                  <div style="font-size: 1.15rem; font-weight: bold; color: {color}; text-align: center; margin: 4px 0;">{text}</div>
                  <div style="font-size: 0.6rem; color: #94A3B8; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{sub_label}</div>
                </div>
                """, unsafe_allow_html=True)

def render_magnifier_chart_streamlit(df, by_region_df, memos):
    pe = [path_effects.withStroke(linewidth=2, foreground='black')]
    master_dates = df['date_s'].tolist()
    
    def normalize_region(name):
        s = str(name).replace(' ', '')
        if '검색' in s and '비검색' not in s and '비' not in s[:1]:
            return '검색 영역'
        elif '비검색' in s or '상세' in s or '추천' in s or s == '-':
            return '비검색 영역'
        elif '오디언스' in s or '오프사이트' in s or 'off' in s.lower() or '외부' in s:
            return '오디언스'
        return s
    
    region_colors = {
        '검색 영역': '#3B82F6',
        '비검색 영역': '#F59E0B',
        '오디언스': '#10B981'
    }
    region_labels = ['검색 영역', '비검색 영역', '오디언스']
    
    if by_region_df is not None and not by_region_df.empty:
        rdf = by_region_df.copy()
        rdf['norm_region'] = rdf['region'].apply(normalize_region)
        available_regions = [r for r in region_labels if r in rdf['norm_region'].unique()]
        if not available_regions:
            available_regions = region_labels[:1]
        
        n_regions = len(available_regions)
        fig = plt.figure(figsize=(14, 4 * n_regions + 0.8))
        fig.df_json = df.to_json(orient='records')
        fig.patch.set_facecolor('#0B0B1A')
        
        fig.suptitle("0. 영역별 광고효율 돋보기 상대 지수 분석 (첫 날 = 100% 기준)", 
                    color='white', fontsize=14, fontweight='bold', y=0.98)
        
        for idx, region_name in enumerate(available_regions):
            rdata = rdf[rdf['norm_region'] == region_name].copy()
            if rdata.empty:
                continue
                
            rdata = rdata.groupby('date_s').agg({
                'imp': 'sum', 'click': 'sum', 'spend': 'sum', 
                'sales': 'sum', 'orders': 'sum'
            }).reset_index()
            rdata['CTR'] = np.where(rdata['imp'] > 0, (rdata['click'] / rdata['imp']) * 100, 0)
            rdata['CVR'] = np.where(rdata['click'] > 0, (rdata['orders'] / rdata['click']) * 100, 0)
            rdata['ROAS'] = np.where(rdata['spend'] > 0, (rdata['sales'] / rdata['spend']) * 100, 0)
            
            if len(rdata) < 1:
                continue
            
            ax = fig.add_subplot(n_regions, 1, idx + 1)
            ax.set_facecolor('#0B0B1A')
            ax.tick_params(axis='x', labelcolor='#94A3B8', labelsize=8, rotation=15)
            ax.tick_params(axis='y', labelcolor='#94A3B8', labelsize=8)
            ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
            for sp in ax.spines.values(): sp.set_color('#1F2937')
            
            def get_base(series):
                val = series.iloc[0]
                if val > 0: return val
                mean_val = series.mean()
                if mean_val > 0: return mean_val
                return 1.0
            
            base_imp = get_base(rdata['imp'])
            base_ctr = get_base(rdata['CTR'])
            base_cvr = get_base(rdata['CVR'])
            base_roas = get_base(rdata['ROAS'])
            
            rdata['imp_idx'] = rdata['imp'] / base_imp * 100
            rdata['ctr_idx'] = rdata['CTR'] / base_ctr * 100
            rdata['cvr_idx'] = rdata['CVR'] / base_cvr * 100
            rdata['roas_idx'] = rdata['ROAS'] / base_roas * 100
            
            dates = rdata['date_s'].tolist()
            rc = region_colors.get(region_name, '#FFFFFF')
            
            l_imp, = ax.plot(dates, rdata['imp_idx'], color='#00E5FF', marker='o', markersize=4, linewidth=1.8, 
                    label='💎 노출수 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])

            l_ctr, = ax.plot(dates, rdata['ctr_idx'], color='#FB923C', marker='s', markersize=4, linewidth=1.8, 
                    label='🍊 클릭률(CTR) 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])

            l_cvr, = ax.plot(dates, rdata['cvr_idx'], color='#10B981', marker='^', markersize=4, linewidth=1.8, 
                    label='🍋 전환율(CVR) 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])

            l_roas, = ax.plot(dates, rdata['roas_idx'], color='#FF00FF', marker='D', markersize=5, linewidth=2.5, 
                    label='🌸 광고효율(ROAS) 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
            
            ax.axhline(y=100, color='#FFFFFF', linestyle='--', linewidth=1.0, alpha=0.5, label='— 첫 날 기준선 (100%)')
            ax.set_title(f"【{region_name}】 노출·클릭률·전환율·ROAS 상대 지수 추이", color=rc, pad=10, fontdict={'size': 11, 'weight': 'bold'})
            ax.set_ylabel('상대 지수 (%)', color='white', size=8, weight='bold')
            ax.legend(loc='upper left', fontsize=7.5, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
            
            _draw_memo_vlines([ax], dates, pe, memos, fontsize=7)
        
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        show_pyplot_with_tooltip(fig)
        plt.close(fig)
    else:
        fig = plt.figure(figsize=(14, 4))
        fig.df_json = df.to_json(orient='records')
        fig.patch.set_facecolor('#0B0B1A')
        ax = fig.add_subplot(1, 1, 1)
        ax.set_facecolor('#0B0B1A')
        ax.tick_params(axis='x', labelcolor='#94A3B8', labelsize=8, rotation=15)
        ax.tick_params(axis='y', labelcolor='#94A3B8', labelsize=8)
        ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
        for sp in ax.spines.values(): sp.set_color('#1F2937')
        
        def get_base(col):
            val = df[col].iloc[0]
            if val > 0: return val
            mean_val = df[col].mean()
            if mean_val > 0: return mean_val
            return 1.0
            
        base_imp = get_base('imp')
        base_ctr = get_base('CTR')
        base_cvr = get_base('CVR')
        base_roas = get_base('ROAS')
        
        df_copy = df.copy()
        df_copy['imp_idx'] = df_copy['imp'] / base_imp * 100
        df_copy['ctr_idx'] = df_copy['CTR'] / base_ctr * 100
        df_copy['cvr_idx'] = df_copy['CVR'] / base_cvr * 100
        df_copy['roas_idx'] = df_copy['ROAS'] / base_roas * 100
        
        dates = df_copy['date_s'].tolist()
        
        ax.plot(dates, df_copy['imp_idx'], color='#00E5FF', marker='o', markersize=4, linewidth=1.8, 
                label='💎 노출수 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax.plot(dates, df_copy['ctr_idx'], color='#FB923C', marker='s', markersize=4, linewidth=1.8, 
                label='🍊 클릭률(CTR) 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax.plot(dates, df_copy['cvr_idx'], color='#10B981', marker='^', markersize=4, linewidth=1.8, 
                label='🍋 전환율(CVR) 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax.plot(dates, df_copy['roas_idx'], color='#FF00FF', marker='D', markersize=5, linewidth=2.5, 
                label='🌸 광고효율(ROAS) 지수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax.axhline(y=100, color='#FFFFFF', linestyle='--', linewidth=1.0, alpha=0.5, label='— 첫 날 기준선 (100%)')
        
        ax.set_ylabel('상대 지수 (%)', color='white', size=8, weight='bold')
        ax.set_title("0. 광고효율 돋보기 상대 지수 분석 (첫 날 데이터 = 100% 기준)", color='white', pad=10, fontdict={'size': 11, 'weight': 'bold'})
        ax.legend(loc='upper left', fontsize=7.5, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
        
        _draw_memo_vlines([ax], dates, pe, memos, fontsize=7)
        fig.tight_layout()
        show_pyplot_with_tooltip(fig)
        plt.close(fig)

def render_large_trend_chart_streamlit(df, kw_data, memos):
    pe = [path_effects.withStroke(linewidth=2, foreground='black')]
    n = len(df)
    fs_title = 12; fs_guide = 7.5; fs_ann = 7.5; fs_label = 8.5; fs_tick = 7.5; fs_leg = 8
    ms = 3.5; lw = 1.6
    
    fig = plt.figure(figsize=(15, 30))
    fig.df_json = df.to_json(orient='records')
    fig.patch.set_facecolor('#0B0B1A')
    
    def add_legend(ax, ax2):
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1+h2, l1+l2, loc='upper left', fontsize=fs_leg, 
                  facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
    
    def setup_ax(ax):
        ax.set_facecolor('#0B0B1A')
        ax.tick_params(axis='x', labelcolor='#94A3B8', labelsize=fs_tick, rotation=20)
        ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
        for sp in ax.spines.values(): sp.set_color('#1F2937')
    
    # ─── 1. 광고비 vs 광고매출 ───
    ax1 = fig.add_subplot(6, 2, 1); setup_ax(ax1)
    ax1.set_title("1. 광고비 vs 광고매출 추이", color='white', pad=40, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
    guide_str1 = "용돈 지출[광고비 막대] | 열매 수확[광고매출 선] ☞ [적자] 매출 선이 낮음 점검 | [안전] 매출 선이 높음"
    ax1.text(0.5, 1.02, guide_str1, transform=ax1.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#111122', edgecolor='#FF00FF', alpha=0.9))
    ax1.bar(df['date_s'], df['spend'], color='#EF4444', alpha=0.35, label='■ 광고비')
    ax1.set_ylabel('광고비 (원)', color='#EF4444', weight='bold', fontsize=fs_label)
    ax1.tick_params(axis='y', labelcolor='#EF4444', labelsize=fs_tick)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x/10000)}만" if x>=10000 else f"{int(x)}"))
    
    ax1_2 = ax1.twinx()
    ax1_2.plot(df['date_s'], df['sales'], color='#00E5FF', marker='o', markersize=ms, linewidth=lw, label='— 광고매출액', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
    ax1_2.set_ylabel('광고매출액 (원)', color='#00E5FF', weight='bold', fontsize=fs_label)
    ax1_2.tick_params(axis='y', labelcolor='#00E5FF', labelsize=fs_tick)
    ax1_2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x/10000)}만" if x>=10000 else f"{int(x)}"))
    _annotate_smart(ax1_2, df['date_s'], df['sales'], '#00E5FF', 'won', pe, fontsize=fs_ann-0.5, step=2)
    ax1.set_ylim(bottom=0, top=max(df['spend'].max() if len(df['spend']) > 0 else 0, 1) * 1.15)
    ax1_2.set_ylim(bottom=0, top=max(df['sales'].max() if len(df['sales']) > 0 else 0, 1) * 1.15)
    add_legend(ax1, ax1_2)

    # ─── 2. 클릭수 vs 광고매출 ───
    ax2 = fig.add_subplot(6, 2, 2); setup_ax(ax2)
    ax2.set_title("2. 클릭수 vs 광고매출 추이", color='white', pad=40, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
    guide_str2 = "손님 입장[클릭수 막대] | 지갑 오픈[광고매출 선] ☞ [구경만] 클릭 높고 매출 바닥 | [알짜] 적은 클릭 높은 매출"
    ax2.text(0.5, 1.02, guide_str2, transform=ax2.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#111122', edgecolor='#FBBF24', alpha=0.9))
    ax2.bar(df['date_s'], df['click'], color='#F59E0B', alpha=0.35, label='■ 클릭수')
    ax2.set_ylabel('클릭수 (회)', color='#F59E0B', weight='bold', fontsize=fs_label)
    ax2.tick_params(axis='y', labelcolor='#F59E0B', labelsize=fs_tick)
    
    ax2_2 = ax2.twinx()
    ax2_2.plot(df['date_s'], df['sales'], color='#00E5FF', marker='o', markersize=ms, linewidth=lw, label='— 광고매출액', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
    ax2_2.set_ylabel('광고매출액 (원)', color='#00E5FF', weight='bold', fontsize=fs_label)
    ax2_2.tick_params(axis='y', labelcolor='#00E5FF', labelsize=fs_tick)
    ax2_2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x/10000)}만" if x>=10000 else f"{int(x)}"))
    _annotate_smart(ax2_2, df['date_s'], df['sales'], '#00E5FF', 'won', pe, fontsize=fs_ann-0.5, step=2)
    ax2.set_ylim(bottom=0, top=max(df['click'].max() if len(df['click']) > 0 else 0, 1) * 1.15)
    ax2_2.set_ylim(bottom=0, top=max(df['sales'].max() if len(df['sales']) > 0 else 0, 1) * 1.15)
    add_legend(ax2, ax2_2)

    # ─── 3. 광고비 vs ROAS ───
    ax3 = fig.add_subplot(6, 2, 3); setup_ax(ax3)
    ax3.set_title("3. 광고비 vs ROAS 추이", color='white', pad=40, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
    guide_str3 = "마중물 투입[광고비 막대] | 마법의 효율[ROAS 선] ☞ [비효율] 광고비 늘고 ROAS 하락 | [안정] ROAS 330%선 지탱"
    ax3.text(0.5, 1.02, guide_str3, transform=ax3.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#111122', edgecolor='#10B981', alpha=0.9))
    ax3.bar(df['date_s'], df['spend'], color='#EF4444', alpha=0.35, label='■ 광고비')
    ax3.set_ylabel('광고비 (원)', color='#EF4444', weight='bold', fontsize=fs_label)
    ax3.tick_params(axis='y', labelcolor='#EF4444', labelsize=fs_tick)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x/10000)}만" if x>=10000 else f"{int(x)}"))
    
    ax3_2 = ax3.twinx()
    ax3_2.plot(df['date_s'], df['ROAS'], color='#10B981', marker='o', markersize=ms, linewidth=lw, label='— ROAS%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
    ax3_2.axhline(y=330, color='#F59E0B', linestyle='--', linewidth=1.0, label='— 흑자 안전 기준선 (330%)')
    ax3_2.set_ylabel('ROAS (%)', color='#10B981', weight='bold', fontsize=fs_label)
    ax3_2.tick_params(axis='y', labelcolor='#10B981', labelsize=fs_tick)
    _annotate_smart(ax3_2, df['date_s'], df['ROAS'], '#10B981', 'pct', pe, fontsize=fs_ann-0.5, step=2)
    ax3.set_ylim(bottom=0, top=max(df['spend'].max() if len(df['spend']) > 0 else 0, 1) * 1.15)
    ax3_2.set_ylim(bottom=0, top=max(df['ROAS'].max() if len(df['ROAS']) > 0 else 0, 1) * 1.15)
    add_legend(ax3, ax3_2)

    # ─── 4. 노출수 vs 클릭수 ───
    ax4 = fig.add_subplot(6, 2, 4); setup_ax(ax4)
    ax4.set_title("4. 노출수 vs 클릭수 추이", color='white', pad=40, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
    guide_str4 = "스쳐 지나감[노출수 막대] | 발길 멈춤[클릭수 선] ☞ [썸네일 부족] 노출 많은데 클릭 바닥 | [인기] 노출 대비 클릭 높음"
    ax4.text(0.5, 1.02, guide_str4, transform=ax4.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#111122', edgecolor='#60A5FA', alpha=0.9))
    ax4.bar(df['date_s'], df['imp'], color='#60A5FA', alpha=0.25, label='■ 노출수')
    ax4.set_ylabel('노출수 (회)', color='#60A5FA', weight='bold', fontsize=fs_label)
    ax4.tick_params(axis='y', labelcolor='#60A5FA', labelsize=fs_tick)
    ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x/10000)}만" if x>=10000 else f"{int(x)}"))
    
    ax4_2 = ax4.twinx()
    ax4_2.plot(df['date_s'], df['click'], color='#3B82F6', marker='o', markersize=ms, linewidth=lw, label='— 클릭수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
    ax4_2.set_ylabel('클릭수 (회)', color='#3B82F6', weight='bold', fontsize=fs_label)
    ax4_2.tick_params(axis='y', labelcolor='#3B82F6', labelsize=fs_tick)
    _annotate_smart(ax4_2, df['date_s'], df['click'], '#3B82F6', 'int', pe, fontsize=fs_ann-0.5, step=2)
    ax4.set_ylim(bottom=0, top=max(df['imp'].max() if len(df['imp']) > 0 else 0, 1) * 1.15)
    ax4_2.set_ylim(bottom=0, top=max(df['click'].max() if len(df['click']) > 0 else 0, 1) * 1.15)
    add_legend(ax4, ax4_2)

    # ─── 5. 클릭수 vs CTR ───
    ax5 = fig.add_subplot(6, 2, 5); setup_ax(ax5)
    ax5.set_title("5. 클릭수 vs CTR 추이", color='white', pad=40, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
    guide_str5 = "매장 입장[클릭수 막대] | 호기심 지수[CTR 선] ☞ [흥미 없음] CTR 0.5% 미만 | [자석 썸네일] CTR 1.5% 돌파"
    ax5.text(0.5, 1.02, guide_str5, transform=ax5.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#111122', edgecolor='#FB923C', alpha=0.9))
    ax5.bar(df['date_s'], df['click'], color='#F59E0B', alpha=0.35, label='■ 클릭수')
    ax5.set_ylabel('클릭수 (회)', color='#F59E0B', weight='bold', fontsize=fs_label)
    ax5.tick_params(axis='y', labelcolor='#F59E0B', labelsize=fs_tick)
    
    ax5_2 = ax5.twinx()
    ax5_2.plot(df['date_s'], df['CTR'], color='#FB923C', marker='o', markersize=ms, linewidth=lw, label='— CTR%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
    ax5_2.axhline(y=1.0, color='#6B7280', linestyle='--', linewidth=1.0, label='— 평균 기준선 (1.0%)')
    ax5_2.set_ylabel('CTR (%)', color='#FB923C', weight='bold', fontsize=fs_label)
    ax5_2.tick_params(axis='y', labelcolor='#FB923C', labelsize=fs_tick)
    _annotate_smart(ax5_2, df['date_s'], df['CTR'], '#FB923C', 'pct', pe, fontsize=fs_ann-0.5, step=2)
    ax5.set_ylim(bottom=0, top=max(df['click'].max() if len(df['click']) > 0 else 0, 1) * 1.15)
    ax5_2.set_ylim(bottom=0, top=max(df['CTR'].max() if len(df['CTR']) > 0 else 0, 1) * 1.15)
    add_legend(ax5, ax5_2)

    # ─── 6. 클릭수 vs CVR ───
    ax6 = fig.add_subplot(6, 2, 6); setup_ax(ax6)
    ax6.set_title("6. 클릭수 vs CVR 추이", color='white', pad=40, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
    guide_str6 = "매장 입장[클릭수 막대] | 구매 설득력[CVR 선] ☞ [설득 부족] CVR 3% 미만 | [완벽 설득] CVR 5~10% 이상 유지"
    ax6.text(0.5, 1.02, guide_str6, transform=ax6.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#111122', edgecolor='#EC4899', alpha=0.9))
    ax6.bar(df['date_s'], df['click'], color='#F59E0B', alpha=0.35, label='■ 클릭수')
    ax6.set_ylabel('클릭수 (회)', color='#F59E0B', weight='bold', fontsize=fs_label)
    ax6.tick_params(axis='y', labelcolor='#F59E0B', labelsize=fs_tick)
    
    ax6_2 = ax6.twinx()
    ax6_2.plot(df['date_s'], df['CVR'], color='#EC4899', marker='o', markersize=ms, linewidth=lw, label='— CVR%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
    ax6_2.axhline(y=5.0, color='#6B7280', linestyle='--', linewidth=1.0, label='— 평균 기준선 (5.0%)')
    ax6_2.set_ylabel('CVR (%)', color='#EC4899', weight='bold', fontsize=fs_label)
    ax6_2.tick_params(axis='y', labelcolor='#EC4899', labelsize=fs_tick)
    _annotate_smart(ax6_2, df['date_s'], df['CVR'], '#EC4899', 'pct', pe, fontsize=fs_ann-0.5, step=2)
    ax6.set_ylim(bottom=0, top=max(df['click'].max() if len(df['click']) > 0 else 0, 1) * 1.15)
    ax6_2.set_ylim(bottom=0, top=max(df['CVR'].max() if len(df['CVR']) > 0 else 0, 1) * 1.15)
    add_legend(ax6, ax6_2)

    # ─── 7. 클릭수 vs CPC ───
    ax7 = fig.add_subplot(6, 2, 7); setup_ax(ax7)
    ax7.set_title("7. 클릭수 vs 평균 클릭비용(CPC) 추이", color='white', pad=40, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
    guide_str7 = "매장 구경[클릭수 막대] | 손님 단가[CPC 선] ☞ [출혈 경쟁] CPC 선 고공행진 | [꿀 매물] 저렴한 CPC 단가 유입"
    ax7.text(0.5, 1.02, guide_str7, transform=ax7.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#111122', edgecolor='#8B5CF6', alpha=0.9))
    ax7.bar(df['date_s'], df['click'], color='#F59E0B', alpha=0.35, label='■ 클릭수')
    ax7.set_ylabel('클릭수 (회)', color='#F59E0B', weight='bold', fontsize=fs_label)
    ax7.tick_params(axis='y', labelcolor='#F59E0B', labelsize=fs_tick)
    
    ax7_2 = ax7.twinx()
    ax7_2.plot(df['date_s'], df['CPC'], color='#8B5CF6', marker='o', markersize=ms, linewidth=lw, label='— CPC (₩)', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
    ax7_2.set_ylabel('CPC (원)', color='#8B5CF6', weight='bold', fontsize=fs_label)
    ax7_2.tick_params(axis='y', labelcolor='#8B5CF6', labelsize=fs_tick)
    _annotate_smart(ax7_2, df['date_s'], df['CPC'], '#8B5CF6', 'int', pe, fontsize=fs_ann-0.5, step=2)
    ax7.set_ylim(bottom=0, top=max(df['click'].max() if len(df['click']) > 0 else 0, 1) * 1.15)
    ax7_2.set_ylim(bottom=0, top=max(df['CPC'].max() if len(df['CPC']) > 0 else 0, 1) * 1.15)
    add_legend(ax7, ax7_2)

    # ─── 8. 날짜별 광고비·광고매출 추이 ───
    ax8 = fig.add_subplot(6, 2, 8); setup_ax(ax8)
    ax8.set_title("8. 날짜별 광고비·광고매출 추이", color='white', pad=40, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
    guide_str8 = "매일 쓰는 돈[광고비 선] | 매일 버는 돈[광고매출 선] ☞ [적자] 쓴 돈이 높음 | [흑자] 두 선의 간격이 멀어짐"
    ax8.text(0.5, 1.02, guide_str8, transform=ax8.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#111122', edgecolor='#34D399', alpha=0.9))
    ax8.plot(df['date_s'], df['spend'], color='#EF4444', marker='s', markersize=ms, linewidth=lw, linestyle='--', label='— 광고비')
    ax8.plot(df['date_s'], df['sales'], color='#00E5FF', marker='o', markersize=ms, linewidth=lw+0.5, label='— 광고매출액', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
    ax8.set_ylabel('금액 (원)', color='white', weight='bold', fontsize=fs_label)
    ax8.tick_params(axis='y', labelcolor='#94A3B8', labelsize=fs_tick)
    ax8.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x/10000)}만" if x>=10000 else f"{int(x)}"))
    _annotate_smart(ax8, df['date_s'], df['sales'], '#00E5FF', 'won', pe, fontsize=fs_ann-0.5, step=2)
    ax8.legend(loc='upper left', fontsize=fs_leg, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)

    # ─── 9. 날짜별 ROAS ───
    ax9 = fig.add_subplot(6, 2, 9); setup_ax(ax9)
    ax9.set_title("9. 날짜별 ROAS 추이", color='white', pad=40, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
    guide_str9 = "가성비 맥박수[ROAS 선] | 기준선 ☞ [경고등] 주황 경계선(300%) 아래 | [건강] 초록 안전선(330%) 위 유지"
    ax9.text(0.5, 1.02, guide_str9, transform=ax9.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#111122', edgecolor='#F59E0B', alpha=0.9))
    ax9.plot(df['date_s'], df['ROAS'], color='#FF00FF', marker='o', markersize=ms+1, linewidth=lw+0.5, label='— ROAS%', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
    ax9.axhline(y=300, color='#F59E0B', linestyle='--', linewidth=1.0, alpha=0.8, label='— 경계선(300%)')
    ax9.axhline(y=330, color='#10B981', linestyle='-', linewidth=1.0, alpha=0.8, label='— 안전선(330%)')
    ax9.set_ylabel('ROAS (%)', color='#FF00FF', weight='bold', fontsize=fs_label)
    ax9.tick_params(axis='y', labelcolor='#FF00FF', labelsize=fs_tick)
    _annotate_smart(ax9, df['date_s'], df['ROAS'], '#FF00FF', 'pct', pe, fontsize=fs_ann-0.5, step=2)
    ax9.legend(loc='upper left', fontsize=fs_leg, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)

    # ─── 10. 키워드별 광고비 대비 전환수 ───
    ax10 = fig.add_subplot(6, 2, 10); ax10.set_facecolor('#0B0B1A')
    ax10.tick_params(axis='y', labelcolor='#94A3B8', labelsize=fs_tick)
    ax10.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
    ax10.set_title("10. 키워드별 광고비 대비 전환수", color='white', pad=40, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
    guide_str10 = "우등생 색출[광고비 막대] | 성적표[전환수 선] ☞ [식충이] 광고비 많고 주문 바닥 | [우등] 적은 비용 높은 주문"
    ax10.text(0.5, 1.02, guide_str10, transform=ax10.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, weight='bold',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#111122', edgecolor='#FB923C', alpha=0.9))
    
    if kw_data is not None and not kw_data.empty:
        top_kws = kw_data.sort_values('spend', ascending=False).head(10).copy()
        def wrap_kw(text, width=8):
            if not text: return ""
            t = str(text).strip()
            return '\n'.join([t[i:i+width] for i in range(0, len(t), width)])
        top_kws['kw_wrapped'] = top_kws['kw'].apply(lambda x: wrap_kw(x, 8))
        x_indices = list(range(len(top_kws)))
        x_labels = top_kws['kw_wrapped'].tolist()
        
        ax10.bar(x_indices, top_kws['spend'], color='#EF4444', alpha=0.35, label='■ 광고비')
        ax10.set_ylabel('광고비 (원)', color='#EF4444', weight='bold', fontsize=fs_label)
        ax10.tick_params(axis='y', labelcolor='#EF4444', labelsize=fs_tick)
        ax10.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x/1000)}천" if x>=1000 else f"{int(x)}"))
        
        ax10.set_xticks(x_indices)
        ax10.set_xticklabels(x_labels, color='white', fontsize=fs_tick - 1.5, rotation=0, ha='center')
        ax10.tick_params(axis='x', labelcolor='white', labelsize=fs_tick - 1.5)
        
        ax10_2 = ax10.twinx()
        ax10_2.plot(x_indices, top_kws['orders'], color='#10B981', marker='s', markersize=ms, linewidth=lw, label='— 주문수', path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
        ax10_2.set_ylabel('주문수 (건)', color='#10B981', weight='bold', fontsize=fs_label)
        ax10_2.tick_params(axis='y', labelcolor='#10B981', labelsize=fs_tick)
        
        for i, v in enumerate(top_kws['orders']):
            if v == 0: continue
            ax10_2.annotate(f"{int(v)}건", (x_indices[i], v), xytext=(0, 8), textcoords="offset points", ha='center', color='#10B981', weight='bold', fontsize=fs_ann-0.5, path_effects=pe)
        ax10.set_ylim(bottom=0, top=max(top_kws['spend'].max() if len(top_kws['spend']) > 0 else 0, 1) * 1.15)
        ax10_2.set_ylim(bottom=0, top=max(top_kws['orders'].max() if len(top_kws['orders']) > 0 else 0, 1) * 1.15)
        add_legend(ax10, ax10_2)
    else:
        ax10.text(0.5, 0.5, "표시할 키워드 데이터가 없습니다.", transform=ax10.transAxes, ha='center', va='center', color='#94A3B8', fontsize=11)

    # ─── 11. 광고비 비중 및 광고 기여도 ───
    ax11 = fig.add_subplot(6, 2, 11); setup_ax(ax11)
    ax11.set_title("11. 광고비 비중 및 광고 기여도 추이", color='white', pad=40, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
    guide_str11 = "광고비 비중 선 = 매출 대비 광고비 비율 | 마진 안전선 = 내 마진율 마지노선 ☞ [위험] 마진율 선 위로 치솟음"
    ax11.text(0.5, 1.02, guide_str11, transform=ax11.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#111122', edgecolor='#FBBF24', alpha=0.9))
    spend_ratio_series = (df['spend'] / df['sales'] * 100).fillna(0)
    ax11.plot(df['date_s'], spend_ratio_series, color='#FBBF24', marker='o', markersize=ms, linewidth=lw, label='— 광고비 비중 (%)')
    ax11.axhline(y=30, color='#10B981', linestyle='--', linewidth=1.0, alpha=0.8, label='— 내 마진율 (30%)')
    ax11.axhline(y=10, color='#EF4444', linestyle=':', linewidth=1.0, alpha=0.8, label='— 경고선 (10%)')
    ax11.set_ylabel('비중 (%)', color='white', weight='bold', fontsize=fs_label)
    ax11.tick_params(axis='y', labelcolor='white', labelsize=fs_tick)
    _annotate_smart(ax11, df['date_s'], spend_ratio_series, '#FBBF24', 'pct', pe, fontsize=fs_ann-0.5, step=2)
    ax11.legend(loc='upper left', fontsize=fs_leg, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)

    # ─── 12. 광고 차감 후 최종 순수익 vs 광고비 ───
    ax12 = fig.add_subplot(6, 2, 12); setup_ax(ax12)
    ax12.set_title("12. 광고 차감 후 최종 순수익 vs 광고비 추이", color='white', pad=40, loc='center', fontdict={'size': fs_title, 'weight': 'bold'})
    guide_str12 = "알짜 순이익[하늘색 선] | 광고비 예산[빨간 선] ☞ [가짜 흑자] 광고비 선은 오르는데 최종 순이익 선은 하락"
    ax12.text(0.5, 1.02, guide_str12, transform=ax12.transAxes, ha='center', va='bottom', color='#A0AEC0', fontsize=fs_guide, weight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#111122', edgecolor='#34D399', alpha=0.9))
    
    margin_rate = 0.3
    gross_profit = df['sales'] * margin_rate
    net_profit = gross_profit - df['spend']
    
    ax12.bar(df['date_s'], gross_profit, color='#94A3B8', alpha=0.15, label='■ 광고 전 마진액 (₩)')
    ax12.plot(df['date_s'], df['spend'], color='#EF4444', marker='x', linewidth=lw-0.5, markersize=ms, linestyle='--', label='— 지출 광고비 (₩)')
    ax12.plot(df['date_s'], net_profit, color='#00E5FF', marker='o', linewidth=lw+1, markersize=ms+1, label='— 진짜 최종 순이익 (₩)',
              path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
    ax12.axhline(y=0, color='white', linestyle='-', linewidth=0.8, alpha=0.5)
    ax12.set_ylabel('금액 (원)', color='white', fontsize=fs_label)
    ax12.tick_params(axis='y', labelcolor='white', labelsize=fs_tick)
    ax12.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x/10000)}만" if x>=10000 else f"{int(x)}"))
    
    for i, v in enumerate(net_profit):
        if i % 2 != 0: continue
        if v == 0: continue
        offset_y = 10 if (i // 2) % 2 == 0 else -14
        ann_color = '#00E5FF' if v >= 0 else '#FF4444'
        txt = _fmt_val(v, 'won')
        ax12.annotate(txt, (df['date_s'].iloc[i], v), 
                       xytext=(0, offset_y), textcoords="offset points", ha='center', color=ann_color, 
                       weight='bold', fontsize=fs_ann-0.8, path_effects=pe)
    ax12.legend(loc='upper left', fontsize=fs_leg, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)

    # 모든 차트에 메모 수직선 표시
    date_labels = df['date_s'].tolist()
    all_axes = [ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8, ax9, ax11, ax12]
    try:
        _draw_memo_vlines(all_axes, date_labels, pe, memos, fontsize=7)
    except Exception:
        pass
        
    fig.subplots_adjust(left=0.06, right=0.94, top=0.97, bottom=0.03, hspace=0.35, wspace=0.3)
    show_pyplot_with_tooltip(fig)
    plt.close(fig)

# -----------------------------------------------------------------------------
# 4. 사이드바 구성 (파일 업로드, 계정 관리 등)
# -----------------------------------------------------------------------------
st.sidebar.markdown(f"### 👤 로그인 사용자: **{st.session_state['username']}**")
if st.sidebar.button("🔓 로그아웃", use_container_width=True):
    logout()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📂 데이터 가져오기")
uploaded_file = st.sidebar.file_uploader("쿠팡 광고성과 엑셀 파일 (.xlsx)", type=["xlsx"], label_visibility="collapsed")

# 분석 상태 세션 저장
if "analyzer" not in st.session_state:
    st.session_state["analyzer"] = None
if "current_file_name" not in st.session_state:
    st.session_state["current_file_name"] = ""

# 1) 사용자가 직접 파일을 업로드한 경우 (업로드 우선)
if uploaded_file is not None:
    if st.session_state["current_file_name"] != uploaded_file.name:
        with st.spinner("🚀 업로드된 광고 데이터를 정밀 분석하는 중입니다..."):
            analyzer = CoupangAdAnalyzer()
            file_bytes = uploaded_file.read()
            success = analyzer.load_data(BytesIO(file_bytes))
            if success:
                analyzer.process()
                st.session_state["analyzer"] = analyzer
                st.session_state["current_file_name"] = uploaded_file.name
                st.sidebar.success(f"✅ 분석 완료! ({analyzer.last_analysis_info})")
                st.toast("✅ 분석 완료! 데이터가 성공적으로 갱신되었습니다.")
            else:
                st.sidebar.error("❌ 파일 로드 실패. 템플릿을 확인하세요.")

# 2) 파일 업로드가 없고 세션에 아직 분석 데이터가 없는 경우 (로컬 폴더 자동 로드)
elif st.session_state["analyzer"] is None:
    import glob
    # 쿠팡광고관리 폴더 내 pa_daily_keyword 엑셀 파일 우선 탐색
    xlsx_pattern = os.path.join(BASE_DIR, "A01424983_pa_daily_keyword_*.xlsx")
    local_files = glob.glob(xlsx_pattern)
    
    if not local_files:
        xlsx_pattern_fallback = os.path.join(BASE_DIR, "*.xlsx")
        local_files = glob.glob(xlsx_pattern_fallback)
        local_files = [f for f in local_files if "sample_report" not in os.path.basename(f)]
        
    if local_files:
        # 가장 최근 수정된 파일 선택
        latest_file = max(local_files, key=os.path.getmtime)
        latest_file_name = os.path.basename(latest_file)
        
        with st.spinner("📂 로컬 최신 광고 데이터를 자동으로 읽어와 분석하는 중입니다..."):
            try:
                analyzer = CoupangAdAnalyzer()
                with open(latest_file, "rb") as f:
                    file_bytes = f.read()
                success = analyzer.load_data(BytesIO(file_bytes))
                if success:
                    analyzer.process()
                    st.session_state["analyzer"] = analyzer
                    st.session_state["current_file_name"] = latest_file_name
                    # st.sidebar.info(f"📂 로컬 최신 파일 자동 감지 및 로드 완료:\n`{latest_file_name}`")
            except Exception as e:
                st.sidebar.warning(f"로컬 파일 자동 로드 실패: {e}")

# Admin 전용 계정 관리
if st.session_state["username"] == "admin":
    users = load_users()  # 실시간 유저 목록 갱신
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ 계정 관리 (Admin 전용)")
    
    with st.sidebar.expander("👤 계정 추가"):
        new_id = st.text_input("새 아이디", key="new_id")
        new_pw = st.text_input("새 비밀번호", type="password", key="new_pw")
        if st.button("계정 생성", use_container_width=True):
            if new_id.strip() and new_pw.strip():
                if new_id in users:
                    st.error("이미 존재하는 아이디입니다.")
                else:
                    users[new_id] = hash_pw(new_pw)
                    save_users(users)
                    st.success("계정이 성공적으로 생성되었습니다.")
                    st.rerun()
            else:
                st.error("빈 칸을 입력할 수 없습니다.")
                
    with st.sidebar.expander("🗑️ 계정 삭제"):
        user_list = [u for u in users.keys() if u != "admin"]
        target_user = st.selectbox("삭제할 사용자 선택", user_list)
        if st.button("계정 삭제 실행", use_container_width=True):
            if target_user:
                del users[target_user]
                save_users(users)
                st.success("계정이 삭제되었습니다.")
                st.rerun()

# -----------------------------------------------------------------------------
# 4. 영역별 및 실판매 대조 차트 렌더링 헬퍼 함수
# -----------------------------------------------------------------------------
def render_region_trend_charts_streamlit(df, by_region, memos):
    import matplotlib.patheffects as path_effects
    
    plt.rcParams['font.family'] = 'NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic'
    pe = [path_effects.withStroke(linewidth=2.5, foreground='black')]
    
    fig = plt.figure(figsize=(12, 10), dpi=100)
    fig.df_json = df.to_json(orient='records')
    fig.patch.set_facecolor('#0B0B1A')
    
    def _map_region_group(region_name):
        r_name = str(region_name).strip()
        if '비검색' in r_name:
            return '비검색'
        elif '검색' in r_name:
            return '검색'
        elif any(k in r_name for k in ['오디언스', '외부', '리타게팅', '오피니언']):
            return '오디언스'
        return '기타'
        
    by_region = by_region.copy()
    by_region['grouped_region'] = by_region['region'].apply(_map_region_group)
    
    pivot_df = by_region.groupby(['date_s', 'grouped_region']).agg({
        'sales': 'sum',
        'spend': 'sum'
    }).reset_index()
    
    sales_pivot = pivot_df.pivot(index='date_s', columns='grouped_region', values='sales').fillna(0)
    spend_pivot = pivot_df.pivot(index='date_s', columns='grouped_region', values='spend').fillna(0)
    
    for col in ['검색', '비검색', '오디언스']:
        if col not in sales_pivot.columns: sales_pivot[col] = 0.0
        if col not in spend_pivot.columns: spend_pivot[col] = 0.0
        
    dates = df['date_s'].tolist()
    sales_pivot = sales_pivot.reindex(dates).fillna(0)
    spend_pivot = spend_pivot.reindex(dates).fillna(0)
    
    colors = {
        '검색': '#2196F3',
        '비검색': '#8BC34A',
        '오디언스': '#78909C'
    }
    
    bar_w = 0.8
    
    def setup_ax(ax):
        ax.set_facecolor('#0B0B1A')
        ax.tick_params(axis='x', labelcolor='#94A3B8', labelsize=9, rotation=0)
        ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
        for sp in ax.spines.values(): sp.set_color('#1F2937')
        
    # 차트 1: 매출 및 ROAS 추이
    ax1 = fig.add_subplot(2, 1, 1)
    setup_ax(ax1)
    ax1.set_title("노출 영역별 매출 및 효율(ROAS) 추이", color='white', pad=25, fontdict={'size': 14, 'weight': 'bold'})
    
    s_non_search = sales_pivot['비검색'].values
    s_search = sales_pivot['검색'].values
    s_audience = sales_pivot['오디언스'].values
    
    ax1.bar(dates, s_audience, color=colors['오디언스'], width=bar_w, alpha=0.9, label='오디언스매출')
    ax1.bar(dates, s_non_search, bottom=s_audience, color=colors['비검색'], width=bar_w, alpha=0.9, label='비검색매출')
    ax1.bar(dates, s_search, bottom=s_audience+s_non_search, color=colors['검색'], width=bar_w, alpha=0.9, label='검색매출')
    
    ax1.set_ylabel('매출/광고비 (원)', color='white', size=10, weight='bold')
    ax1.tick_params(axis='y', labelcolor='#94A3B8', labelsize=8)
    
    daily_spend = spend_pivot.sum(axis=1).values
    ax1.plot(dates, daily_spend, color='#FFA726', linewidth=2.5, marker='o', markersize=3, label='광고비',
             path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
    
    ax1_twin = ax1.twinx()
    daily_sales = sales_pivot.sum(axis=1).values
    daily_roas = np.where(daily_spend > 0, (daily_sales / daily_spend) * 100, 0)
    
    ax1_twin.plot(dates, daily_roas, color='#42A5F5', marker='o', markersize=4, linewidth=2, label='ROAS',
                  path_effects=[path_effects.SimpleLineShadow(), path_effects.Normal()])
    
    ax1_twin.set_ylabel('ROAS (%)', color='#42A5F5', size=10, weight='bold')
    ax1_twin.tick_params(axis='y', labelcolor='#42A5F5', labelsize=8)
    ax1_twin.spines['right'].set_color('#42A5F5')
    
    max_ax1 = max(np.max(daily_sales) if len(daily_sales) > 0 else 0, np.max(daily_spend) if len(daily_spend) > 0 else 0)
    ax1.set_ylim(bottom=0, top=max_ax1 * 1.15 if max_ax1 > 0 else 1.0)
    
    max_roas = np.max(daily_roas) if len(daily_roas) > 0 else 0
    ax1_twin.set_ylim(bottom=0, top=max_roas * 1.15 if max_roas > 0 else 1.0)
    
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(h1+h2, l1+l2, loc='upper left', fontsize=8.5,
               facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
               
    # 차트 2: 광고비 점유 추이
    ax2 = fig.add_subplot(2, 1, 2)
    setup_ax(ax2)
    ax2.set_title("노출 영역별 광고비 점유 추이", color='white', pad=25, fontdict={'size': 14, 'weight': 'bold'})
    
    sp_non_search = spend_pivot['비검색'].values
    sp_search = spend_pivot['검색'].values
    sp_audience = spend_pivot['오디언스'].values
    
    ax2.bar(dates, sp_audience, color=colors['오디언스'], width=bar_w, alpha=0.9, label='오디언스광고비')
    ax2.bar(dates, sp_non_search, bottom=sp_audience, color=colors['비검색'], width=bar_w, alpha=0.9, label='비검색광고비')
    ax2.bar(dates, sp_search, bottom=sp_audience+sp_non_search, color=colors['검색'], width=bar_w, alpha=0.9, label='검색광고비')
    
    ax2.set_ylabel('광고비 (원)', color='white', size=10, weight='bold')
    ax2.tick_params(axis='y', labelcolor='#94A3B8', labelsize=8)
    ax2.legend(loc='upper left', fontsize=8.5, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
    
    _draw_memo_vlines([ax1, ax2], dates, pe, memos, fontsize=8)
    
    fig.tight_layout(pad=3.0)
    show_pyplot_with_tooltip(fig)
    plt.close(fig)

def render_real_price_chart_streamlit(df, p_val, memos):
    import matplotlib.patheffects as path_effects
    
    df = df.sort_values('p_date')
    dates = df['date_s'].tolist()
    
    coupang_vals = []
    real_vals = []
    spend_vals = []
    
    for _, r in df.iterrows():
        spend = r.get('spend', 0)
        sales = r.get('sales', 0)
        orders = r.get('orders', 0)
        
        s_real = p_val * orders
        
        coupang_vals.append(sales)
        real_vals.append(s_real)
        spend_vals.append(spend)
        
    plt.rcParams['font.family'] = 'NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic'
    fig = plt.figure(figsize=(13, 4.2), dpi=95)
    fig.df_json = df.to_json(orient='records')
    fig.patch.set_facecolor('#0B0B1A')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#0B0B1A')
    
    ax.set_title("집행광고비 vs 광고전환매출 추이 비교", color='white', pad=25, loc='left',
                 fontdict={'size': 14, 'weight': 'bold', 'family': 'NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic'})
                 
    ax.plot(dates, spend_vals, color='#F59E0B', marker='x', markersize=6, linewidth=2, linestyle='--', label='집행광고비')
    ax.plot(dates, coupang_vals, color='#3B82F6', marker='o', markersize=6, linewidth=2.5, label='광고전환매출 (쿠팡시스템)')
    ax.plot(dates, real_vals, color='#10B981', marker='s', markersize=6, linewidth=2.5, label='광고전환매출 (내 판매가)')
        
    ax.set_ylabel("금액 (원)", color='white', fontsize=10, weight='bold')
    ax.tick_params(axis='y', labelcolor='white', labelsize=9)
    ax.tick_params(axis='x', labelcolor='#94A3B8', labelsize=9)
    ax.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
    
    def format_y_thousand(val, pos):
        if val == 0: return '0'
        if abs(val) >= 1000000: return f"{val/1000000:.1f}백만"
        return f"{int(val/1000)}천"
    ax.yaxis.set_major_formatter(plt.FuncFormatter(format_y_thousand))
        
    for sp in ax.spines.values():
        sp.set_color('#1F2937')
        
    ax.legend(loc='upper right', fontsize=9, facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8, prop={'family': 'NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic'})
    
    try:
        pe = [path_effects.withStroke(linewidth=2, foreground='black')]
        _draw_memo_vlines([ax], dates, pe, memos, fontsize=8)
    except Exception:
        pass
        
    fig.tight_layout()
    show_pyplot_with_tooltip(fig)
    plt.close(fig)


st.markdown("<h1><span class='rocket-icon'>🚀</span> <span class='title-gradient'>쿠팡 광고 최적화 마스터 Web</span></h1>", unsafe_allow_html=True)

if st.session_state["analyzer"] is None:
    st.info("💡 좌측 사이드바에서 **쿠팡 광고 성과 엑셀 파일**을 먼저 올려 분석을 실행해 주세요!")
    st.stop()

analyzer = st.session_state["analyzer"]

# Force update the class of the analyzer instance to use the latest reloaded methods
import sys
if "analyzer" in sys.modules:
    import importlib
    importlib.reload(sys.modules["analyzer"])
    analyzer.__class__ = sys.modules["analyzer"].CoupangAdAnalyzer

st.caption(f"📅 실시간 분석 중인 파일: **{st.session_state['current_file_name']}** | {analyzer.last_analysis_info}")





# ── Rerun 후 대기 중인 toast 알림 출력 ──
if st.session_state.get("pending_toast"):
    st.toast(st.session_state["pending_toast"])
    del st.session_state["pending_toast"]

# 탭 자동 포커싱 스크립트 주입 (Rerun 후 실행)
if st.session_state.get("pending_tab_focus"):
    target_tab_label = st.session_state["pending_tab_focus"]
    del st.session_state["pending_tab_focus"]
    
    js_code = f"""
    <script>
    (function() {{
        var parentDoc = window.parent.document;
        var clickSubTab = function() {{
            var attempts = 0;
            var interval = setInterval(function() {{
                var newTabs = parentDoc.querySelectorAll('[role=\\'tab\\'], button[data-baseweb=\\'tab\\'], button[id*=\\'tab\\']');
                var cleanTarget = '{target_tab_label}'.replace(/[^가-힣a-zA-Z0-9 ]/g, '').trim();
                var found = false;
                for (var j = 0; j < newTabs.length; j++) {{
                    var tabTxt = newTabs[j].textContent.replace(/[^가-힣a-zA-Z0-9 ]/g, '').trim();
                    if (tabTxt.includes(cleanTarget)) {{
                        newTabs[j].click();
                        found = true;
                        break;
                    }}
                }}
                attempts++;
                if (found || attempts > 20) {{
                    clearInterval(interval);
                }}
            }}, 100);
        }};

        var tabs = parentDoc.querySelectorAll('[role=\\'tab\\'], button[data-baseweb=\\'tab\\'], button[id*=\\'tab\\']');
        var kwTab = null;
        for (var i = 0; i < tabs.length; i++) {{
            var txt = tabs[i].textContent || '';
            if (txt.includes('키워드/입찰')) {{
                kwTab = tabs[i];
                break;
            }}
        }}
        
        if (kwTab) {{
            var isAlreadyActive = kwTab.getAttribute('aria-selected') === 'true';
            if (isAlreadyActive) {{
                clickSubTab();
            }} else {{
                kwTab.click();
                setTimeout(clickSubTab, 150);
            }}
        }} else {{
            clickSubTab();
        }}
    }})();
    </script>
    """
    import streamlit.components.v1 as components
    components.html(js_code, height=0)



tab_perf, tab_keyword, tab_tools, tab_memo = st.tabs([
    "📊 종합 성과", "⚙️ 키워드/입찰", "🛡️ AI분석/도구", "📝 일별 메모"
])

# -----------------------------------------------------------------------------
# 5-1. Tab 1: 📊 종합 성과
# -----------------------------------------------------------------------------
with tab_perf:
    sub_perf_tab1, sub_perf_tab2, sub_perf_tab3, sub_perf_tab4 = st.tabs([
        "📊 광고요약", "📈 성과 추이", "🌐 영역별 분석", "📊 실판매 분석"
    ])
    
    overall = analyzer.get_overall_summary()
    
    # 5-1-1. 광고요약
    with sub_perf_tab1:
        st.markdown("""
        <style>
            /* 광고요약 탭 내의 Streamlit columns 여백 축소 */
            div[data-testid="column"] {
                margin-bottom: -10px !important;
            }
        </style>
        """, unsafe_allow_html=True)
        st.subheader("📊 광고 주요 성과 지표")
        
        # --- 영역별 세부 분류 계산 (카드 서브라벨용) ---
        region_summary = analyzer.get_region_summary()
        def _normalize_region(name):
            s = str(name).replace(' ', '')
            if '비검색' in s or '비' == s[:1]: return '비검색'
            elif '검색' in s: return '검색'
            elif any(x in s for x in ['오디언스', '외부', '오피니언', '리타게팅']): return '오디언스'
            return s
        region_data = {'검색': {}, '비검색': {}, '오디언스': {}}
        if region_summary is not None and not region_summary.empty:
            rs = region_summary.copy()
            rs['norm'] = rs['region'].apply(_normalize_region)
            for rn in ['검색', '비검색', '오디언스']:
                rr = rs[rs['norm'] == rn]
                if not rr.empty:
                    rd = {
                        'spend': rr['spend'].sum(), 'sales': rr['sales'].sum(),
                        'orders': rr['orders'].sum(), 'imp': rr['imp'].sum(),
                        'click': rr['click'].sum(),
                    }
                    rd['ROAS'] = (rd['sales'] / rd['spend'] * 100) if rd['spend'] > 0 else 0
                    rd['CTR'] = (rd['click'] / rd['imp'] * 100) if rd['imp'] > 0 else 0
                    rd['CVR'] = (rd['orders'] / rd['click'] * 100) if rd['click'] > 0 else 0
                    region_data[rn] = rd

        def _sub_label(key, unit):
            parts = []
            for rn in ['검색', '비검색', '오디언스']:
                v = region_data.get(rn, {}).get(key, 0)
                if unit == '원': parts.append(f"©{rn[:2]} {int(v):,}")
                elif unit == '%': parts.append(f"©{rn[:2]} {v:.2f}%")
                else: parts.append(f"©{rn[:2]} {int(v):,}")
            return ' / '.join(parts)

        # 4x3 그리드로 지표 카드 출력
        metrics = [
            ("전체 광고비", overall['spend'], "원", "#FBBF24", 'spend'),
            ("실현 광고비", overall['spend'], "원", "#FBBF24", 'spend'),
            ("전환 매출", overall['sales'], "원", "#34D399", 'sales'),
            ("전체 매출", overall['sales'], "원", "#34D399", 'sales'),
            ("전체 판매수", overall['total_qty'], "회", "#60A5FA", 'orders'),
            ("노출수", overall['imp'], "회", "#60A5FA", 'imp'),
            ("클릭수", overall['click'], "회", "#60A5FA", 'click'),
            ("클릭률", overall['CTR'], "%", "#FB923C", 'CTR'),
            ("전환 판매수", overall['conv_qty'], "회", "#60A5FA", 'orders'),
            ("전환 주문수", overall['orders'], "회", "#60A5FA", 'orders'),
            ("수익률(ROAS)", overall['ROAS'], "%", "#FB923C", 'ROAS'),
            ("전환율(CVR)", overall['CVR'], "%", "#FB923C", 'CVR')
        ]
        
        for r in range(2):
            cols = st.columns(6)
            for c in range(6):
                idx = r * 6 + c
                title, val, unit, color, sub_key = metrics[idx]
                with cols[c]:
                    if unit == "원":
                        val_str = f"{int(val):,} {unit}"
                    elif unit == "%":
                        val_str = f"{val:.2f} {unit}"
                    else:
                        val_str = f"{int(val):,} {unit}"
                    sub_text = _sub_label(sub_key, unit)
                    st.markdown(f"""
                  <div class="premium-card" style="padding: 10px; margin-bottom: 10px; border-width: 1.5px; border-color: #3B82F6;">
                      <div style="font-size: 0.75rem; font-weight: bold; color: #E2E8F0; text-align: center;">{title}</div>
                      <div class="metric-value" style="color: {color}; font-size: 1.35rem; text-align: center; margin-bottom: 2px;">{val_str}</div>
                      <div style="font-size: 0.65rem; color: #94A3B8; text-align: center; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{sub_text}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # =====================================================
        # 📈 성과 그래프 (집행 광고비 vs 광고 전환 매출)
        # =====================================================
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 12px; border: 0; border-top: 1px solid rgba(255, 255, 255, 0.1);'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top: -5px; margin-bottom: 15px; font-family: 'Malgun Gothic', sans-serif; font-weight: bold; color: white; font-size: 1.25rem;'>📈 성과 그래프</h3>", unsafe_allow_html=True)
        pd_data = analyzer.get_daily_performance()
        if not pd_data['total'].empty:
            df_perf = pd_data['total']
            dates = df_perf['date_s'].tolist()
            spend_vals = df_perf['spend'].tolist()
            sales_vals = df_perf['sales'].tolist()
            
            fig_trend, ax1 = plt.subplots(figsize=(14, 4))
            fig_trend.df_json = df_perf.to_json(orient='records')
            fig_trend.patch.set_facecolor('#0B0B1A')
            ax1.set_facecolor('#0B0B1A')
            
            # 좌축: 집행 광고비
            ax1.plot(dates, spend_vals, color='#3B82F6', marker='s', markersize=5, linewidth=2.5, label='집행 광고비')
            ax1.set_ylabel('집행 광고비 (원)', color='white', fontsize=10, weight='bold')
            ax1.tick_params(axis='y', labelcolor='#3B82F6', labelsize=9)
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x/1000)}천" if x >= 1000 else f"{int(x)}"))
            
            # 우축: 광고 전환 매출
            ax2 = ax1.twinx()
            ax2.plot(dates, sales_vals, color='#10B981', marker='s', markersize=5, linewidth=2.5, label='광고 전환 매출')
            ax2.set_ylabel('광고 전환 매출 (원)', color='white', fontsize=10, weight='bold')
            ax2.tick_params(axis='y', labelcolor='#10B981', labelsize=9)
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x/1000)}천" if x >= 1000 else f"{int(x)}"))
            
            max_sp = max(spend_vals) if spend_vals and max(spend_vals) > 0 else 1000
            max_sl = max(sales_vals) if sales_vals and max(sales_vals) > 0 else 1000
            ax1.set_ylim(bottom=0, top=max_sp * 1.15)
            ax2.set_ylim(bottom=0, top=max_sl * 1.15)
            
            ax1.tick_params(axis='x', labelcolor='#94A3B8', labelsize=9)
            ax1.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.4)
            for sp in ax1.spines.values(): sp.set_color('#1F2937')
            for sp in ax2.spines.values(): sp.set_color('#1F2937')
            
            h1, l1 = ax1.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax1.legend(h1+h2, l1+l2, loc='upper right', fontsize=9,
                       facecolor='#1A1A2E', edgecolor='#333', labelcolor='white', framealpha=0.8)
            
            try:
                import matplotlib.patheffects as path_effects
                pe = [path_effects.withStroke(linewidth=2, foreground='black')]
                memos = load_json(MEMOS_FILE, [])
                _draw_memo_vlines([ax1], dates, pe, memos, fontsize=8)
            except Exception:
                pass
                
            fig_trend.tight_layout()
            show_pyplot_with_tooltip(fig_trend)
            plt.close(fig_trend)
        else:
            st.info("성과 그래프를 표시할 추이 데이터가 없습니다.")

        # =====================================================
        # 2x2 차트 그리드 (수익성 / TOP5 / KPI건강도 / 영역별)
        # =====================================================
        st.markdown("---")
        col_chart1, col_chart2 = st.columns(2)
        
        # --- 💰 수익성 한눈에 보기 ---
        with col_chart1:
            st.markdown("#### 💰 수익성 한눈에 보기")
            st.caption("매출이 광고비보다 높으면 이익! ROAS 330% 이상이 안전권")
            
            spend_v = overall['spend']
            sales_v = overall['sales']
            profit = sales_v - spend_v
            roas = overall['ROAS']
            
            fig_p, ax_p = plt.subplots(figsize=(6, 4.5))
            fig_p.patch.set_facecolor('#0B0B1A')
            ax_p.set_facecolor('#0B0B1A')
            
            cats = ['총 광고비', '총 매출']
            vals = [spend_v, sales_v]
            colors_bar = ['#EF4444', '#00E5FF']
            bars = ax_p.bar(cats, vals, color=colors_bar, width=0.5, alpha=0.8)
            
            p_color = '#10B981' if profit >= 0 else '#EF4444'
            p_bars = ax_p.bar(['순수익'], [profit], color=p_color, width=0.5, alpha=0.8)
            
            for bar in bars:
                h = bar.get_height()
                va_d = 'bottom' if h >= 0 else 'top'
                ax_p.text(bar.get_x() + bar.get_width()/2., h + (5 if h >= 0 else -15),
                         f"{int(h):,}원", ha='center', va=va_d, color='white', weight='bold', fontsize=9)
            for bar in p_bars:
                h = bar.get_height()
                tc = '#34D399' if h >= 0 else '#F87171'
                ax_p.text(bar.get_x() + bar.get_width()/2., h + (5 if h >= 0 else -15),
                         f"{int(h):,}원", ha='center', va='bottom' if h >= 0 else 'top', color=tc, weight='bold', fontsize=9)
            
            roas_c = '#10B981' if roas >= 330 else '#F59E0B' if roas >= 100 else '#EF4444'
            ax_p.text(0.97, 0.95, f'ROAS {roas:.0f}%', transform=ax_p.transAxes, ha='right', va='top',
                     fontsize=14, weight='bold', color=roas_c,
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='#1A1A2E', edgecolor=roas_c, alpha=0.9))
            
            ax_p.tick_params(axis='y', labelcolor='#94A3B8', labelsize=7)
            ax_p.tick_params(axis='x', labelcolor='white', labelsize=10)
            ax_p.grid(True, axis='y', color='#1F2937', linestyle='--', alpha=0.3)
            ax_p.axhline(y=0, color='#333', linewidth=0.8)
            fig_p.tight_layout()
            show_pyplot_with_tooltip(fig_p)
            plt.close(fig_p)
        
        # --- 🏆 TOP5 효자 키워드 ---
        with col_chart2:
            st.markdown("#### 🏆 TOP5 효자 키워드")
            st.caption("매출을 가장 많이 만드는 키워드에 예산을 집중하세요")
            
            plt.rcParams['font.family'] = 'NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic'
            plt.rcParams['axes.unicode_minus'] = False
            
            kw_data = analyzer.summary_df
            fig_kw, ax_kw = plt.subplots(figsize=(6, 4.5))
            fig_kw.patch.set_facecolor('#0B0B1A')
            ax_kw.set_facecolor('#0B0B1A')
            
            if kw_data is not None and not kw_data.empty:
                top5 = kw_data.nlargest(5, 'sales')[['kw', 'sales', 'spend', 'ROAS']].iloc[::-1]
                labels = [kw[:8] + '..' if len(str(kw)) > 8 else str(kw) for kw in top5['kw']]
                
                colors_map = []
                for _, r in top5.iterrows():
                    if r['ROAS'] >= 330: colors_map.append('#10B981')
                    elif r['ROAS'] >= 100: colors_map.append('#F59E0B')
                    else: colors_map.append('#EF4444')
                
                bars = ax_kw.barh(labels, top5['sales'].values, color=colors_map, height=0.5, alpha=0.8)
                
                for bar in bars:
                    w = bar.get_width()
                    ax_kw.text(w + (w*0.01 + 10), bar.get_y() + bar.get_height()/2.,
                              f"{int(w):,}원", ha='left', va='center', color='white', weight='bold', fontsize=8)
            else:
                ax_kw.text(0.5, 0.5, '데이터 없음', transform=ax_kw.transAxes, ha='center', va='center',
                          color='#666', fontsize=14)
            
            ax_kw.tick_params(axis='y', labelcolor='white', labelsize=9)
            ax_kw.tick_params(axis='x', labelcolor='#94A3B8', labelsize=7)
            ax_kw.grid(True, axis='x', color='#1F2937', linestyle='--', alpha=0.3)
            
            fig_kw.tight_layout()
            show_pyplot_with_tooltip(fig_kw)
            plt.close(fig_kw)
            
        # --- 두 번째 행: KPI 건강도 & 영역별 상세 성과 ---
        col_chart3, col_chart4 = st.columns(2)
        
        with col_chart3:
            st.markdown("#### ⚡ 핵심 KPI 건강도")
            st.caption("초록=양호 / 노랑=주의 / 빨강=위험 (기준: 업계 평균)")
            render_dash_kpi_gauge_streamlit(overall)
            
        with col_chart4:
            st.markdown("#### 🍩 노출 영역별 상세 성과")
            st.caption("광고비(막대) 대비 클릭수와 주문수(선) 효율을 확인하세요")
            by_region = pd_data.get('by_region', pd.DataFrame())
            render_dashboard_pie_streamlit(by_region)

        # --- 📋 영역별 광고 성과 요약 (Summary) 테이블 ---
        st.markdown("---")
        st.markdown("#### 📋 영역별 광고 성과 요약 (Summary)")
        region_summary = analyzer.get_region_summary()
        if region_summary is not None and not region_summary.empty:
            summary_data = []
            for _, r in region_summary.iterrows():
                summary_data.append({
                    "노출영역": r['region'],
                    "매출액": f"{int(r['sales']):,}원",
                    "광고비": f"{int(r['spend']):,}원",
                    "광고효율(ROAS)%": f"{r['ROAS']:.1f}%",
                    "주문건수": f"{int(r['orders']):,}건",
                    "클릭수": f"{int(r['click']):,}회",
                    "노출수": f"{int(r['imp']):,}회",
                    "CTR%": f"{r['CTR']:.2f}%",
                    "전환율%": f"{r['CVR']:.1f}%",
                    "CPC": f"{int(r['CPC']):,}원"
                })
            st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
        else:
            st.info("영역별 요약 데이터가 없습니다.")

    # 5-1-2. 성과 추이 차트
    with sub_perf_tab2:
        pd_data = analyzer.get_daily_performance()
        if not pd_data['total'].empty:
            memos = load_json(MEMOS_FILE, [])
            
            # 1. KPI 요약 카드 (6x2)
            region_summary = analyzer.get_region_summary()
            render_kpi_summary_cards_streamlit(overall, region_summary)
            
            # 2. 돋보기 1초 진단 처방전
            by_region = pd_data.get('by_region', pd.DataFrame())
            render_magnifier_diagnosis_streamlit(pd_data['total'], by_region_df=by_region)
            
            # 3. 돋보기 상대 지수 차트
            render_magnifier_chart_streamlit(pd_data['total'], by_region, memos)
            
            # 4. 기존 12대 차트
            render_large_trend_chart_streamlit(pd_data['total'], analyzer.summary_df, memos)
        else:
            st.info("성과 차트를 표시할 추이 데이터가 없습니다.")

    # 5-1-3. 영역별 분석
    with sub_perf_tab3:
        st.subheader("📋 노출 영역별 상세 성과 (매출/광고비 점유율 포함)")
        
        if analyzer.raw_df is not None:
            df = analyzer.raw_df.copy()
            m = analyzer._get_column_mapping(df)
            if m['region']:
                for k in ['imp', 'click', 'spend', 'sales', 'orders']:
                    if m[k]:
                        df[m[k]] = pd.to_numeric(
                            df[m[k]].astype(str).str.replace(',', '').str.replace('₩', '').str.replace('원', ''),
                            errors='coerce'
                        ).fillna(0)
                        
                def _map_region_group(region_name):
                    r_name = str(region_name).strip()
                    if '비검색' in r_name: return '비검색'
                    elif '검색' in r_name: return '검색'
                    elif any(k in r_name for k in ['오디언스', '외부', '리타게팅', '오피니언']): return '오디언스'
                    return '기타'
                    
                df['grouped_region'] = df[m['region']].apply(_map_region_group)
                s = df.groupby('grouped_region').agg({
                    m['sales']: 'sum',
                    m['spend']: 'sum',
                    m['orders']: 'sum',
                    m['click']: 'sum',
                    m['imp']: 'sum'
                }).reset_index()
                s.columns = ['region', 'sales', 'spend', 'orders', 'click', 'imp']
                
                order_map = {'검색': 0, '비검색': 1, '오디언스': 2, '기타': 3}
                s['order'] = s['region'].map(order_map).fillna(4)
                s = s.sort_values('order').drop(columns=['order'])
                
                total_sales = s['sales'].sum()
                total_spend = s['spend'].sum()
                total_orders = s['orders'].sum()
                total_click = s['click'].sum()
                total_imp = s['imp'].sum()
                
                rows = []
                for _, row in s.iterrows():
                    r_name = row['region']
                    imp = row['imp']
                    click = row['click']
                    orders = row['orders']
                    sales = row['sales']
                    spend = row['spend']
                    
                    ctr = (click / imp * 100) if imp > 0 else 0
                    cvr = (orders / click * 100) if click > 0 else 0
                    cpm = (spend / imp * 1000) if imp > 0 else 0
                    cpc = (spend / click) if click > 0 else 0
                    roas = (sales / spend * 100) if spend > 0 else 0
                    cpa = (spend / orders) if orders > 0 else 0
                    aov = (sales / orders) if orders > 0 else 0
                    
                    spend_pct = (spend / total_spend * 100) if total_spend > 0 else 0
                    sales_pct = (sales / total_sales * 100) if total_sales > 0 else 0
                    
                    rows.append({
                        "노출 영역": r_name,
                        "노출수": f"{int(imp):,}",
                        "클릭": f"{int(click):,}",
                        "주문": f"{int(orders):,}",
                        "클릭률": f"{ctr:.2f}%",
                        "전환율": f"{cvr:.2f}%",
                        "CPM": f"{int(cpm):,}원",
                        "CPC": f"{int(cpc):,}원",
                        "광고비": f"{int(spend):,}원 ({spend_pct:.0f}%)",
                        "광고매출": f"{int(sales):,}원 ({sales_pct:.0f}%)",
                        "ROAS": f"{roas:.2f}%",
                        "전환당비용": f"{int(cpa):,}원",
                        "객단가": f"{int(aov):,}원"
                    })
                
                t_ctr = (total_click / total_imp * 100) if total_imp > 0 else 0
                t_cvr = (total_orders / total_click * 100) if total_click > 0 else 0
                t_cpm = (total_spend / total_imp * 1000) if total_imp > 0 else 0
                t_cpc = (total_spend / total_click) if total_click > 0 else 0
                t_roas = (total_sales / total_spend * 100) if total_spend > 0 else 0
                t_cpa = (total_spend / total_orders) if total_orders > 0 else 0
                t_aov = (total_sales / total_orders) if total_orders > 0 else 0
                
                rows.append({
                    "노출 영역": "합계",
                    "노출수": f"{int(total_imp):,}",
                    "클릭": f"{int(total_click):,}",
                    "주문": f"{int(total_orders):,}",
                    "클릭률": f"{t_ctr:.2f}%",
                    "전환율": f"{t_cvr:.2f}%",
                    "CPM": f"{int(t_cpm):,}원",
                    "CPC": f"{int(t_cpc):,}원",
                    "광고비": f"{int(total_spend):,}원 (100%)",
                    "광고매출": f"{int(total_sales):,}원 (100%)",
                    "ROAS": f"{t_roas:.2f}%",
                    "전환당비용": f"{int(t_cpa):,}원",
                    "객단가": f"{int(t_aov):,}원"
               })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🌐 노출 영역별 성과 분석")
        pd_data = analyzer.get_daily_performance()
        if not pd_data['total'].empty:
            memos = load_json(MEMOS_FILE, [])
            by_region = pd_data.get('by_region', pd.DataFrame())
            if not by_region.empty:
                render_region_trend_charts_streamlit(pd_data['total'], by_region, memos)
            else:
                st.info("영역별 추이 데이터가 없습니다.")

    # 5-1-4. 실판매 분석
    with sub_perf_tab4:
        st.subheader("📊 실제판매가 반영 광고 성과 보정")
        
        col_in1, col_in2, col_in3, col_in4, col_in5, col_in6 = st.columns([1.5, 1.2, 0.3, 1.2, 2.0, 1.2])
        with col_in1:
            st.markdown("<div style='margin-top: 6px; font-size: 0.95rem; font-weight: bold; color: #E2E8F0; text-align: right;'>🏷️ 실제판매가 입력:</div>", unsafe_allow_html=True)
        with col_in2:
            real_price_input = st.text_input("실제판매가", value="37,500", label_visibility="collapsed", key="real_price_input_unique")
        with col_in3:
            st.markdown("<div style='margin-top: 6px; font-size: 0.95rem; color: #E2E8F0;'>원</div>", unsafe_allow_html=True)
        with col_in4:
            st.markdown("<div style='margin-top: 6px; font-size: 0.95rem; font-weight: bold; color: #E2E8F0; text-align: right;'>⚙️ 보정 기준:</div>", unsafe_allow_html=True)
        with col_in5:
            real_calc_base = st.selectbox("보정기준", ["내 판매가 기준", "쿠팡시스템 기준"], label_visibility="collapsed", key="real_calc_base_unique")
        with col_in6:
            apply_real_price = st.button("⚡ 계산 반영", use_container_width=True, key="apply_real_price_btn")
            
        try:
            p_val = float(re.sub(r'[^\d]', '', real_price_input))
        except:
            p_val = 37500.0
            
        overall = analyzer.get_overall_summary()
        if overall:
            sales_coupang = overall.get('sales', 0)
            sales_real = p_val * overall.get('orders', 0)
            spend = overall.get('spend', 0)
            roas_coupang = overall.get('ROAS', 0)
            roas_real = (sales_real / spend * 100) if spend > 0 else 0
            
            total_qty = overall.get('total_qty', 0)
            total_sales_real = p_val * total_qty
            
            st.markdown("### 📋 주요 지표 보정 대조 카드 (12대 지표)")
            real_metrics_def = [
                ("광고수익률", "ROAS", "%", False),
                ("오늘 누적 광고비", "today_spend", "원", True),
                ("집행 광고비", "spend", "원", True),
                ("광고 전환매출", "sales", "원", False),
                ("전환율", "CVR", "%", True),
                ("클릭률", "CTR", "%", True),
                ("노출수", "imp", "회", True),
                ("클릭수", "click", "회", True),
                ("광고 전환 판매수", "conv_qty", "회", True),
                ("광고 전환 주문수", "orders", "건", True),
                ("전체 매출", "total_sales", "원", False),
                ("전체 판매수", "total_qty", "개", True)
            ]
            
            for r_idx in range(2):
                cols_card = st.columns(6)
                for c_idx in range(6):
                    idx = r_idx * 6 + c_idx
                    t, k, u, is_fixed = real_metrics_def[idx]
                    
                    if k == "ROAS":
                        v_coupang = roas_coupang
                        v_real = roas_real
                    elif k == "today_spend":
                        v_coupang = spend
                        v_real = v_coupang
                    elif k == "spend":
                        v_coupang = spend
                        v_real = v_coupang
                    elif k == "sales":
                        v_coupang = sales_coupang
                        v_real = sales_real
                    elif k == "CVR":
                        v_coupang = overall.get('CVR', 0)
                        v_real = v_coupang
                    elif k == "CTR":
                        v_coupang = overall.get('CTR', 0)
                        v_real = v_coupang
                    elif k == "imp":
                        v_coupang = overall.get('imp', 0)
                        v_real = v_coupang
                    elif k == "click":
                        v_coupang = overall.get('click', 0)
                        v_real = v_coupang
                    elif k == "conv_qty":
                        v_coupang = overall.get('conv_qty', 0)
                        v_real = v_coupang
                    elif k == "orders":
                        v_coupang = overall.get('orders', 0)
                        v_real = v_coupang
                    elif k == "total_sales":
                        v_coupang = sales_coupang
                        v_real = total_sales_real
                    elif k == "total_qty":
                        v_coupang = total_qty
                        v_real = v_coupang
                        
                    if u == "원":
                        txt_coupang = f"{int(v_coupang):,} 원"
                        txt_real = f"{int(v_real):,} 원"
                    elif u in ["회", "건", "개"]:
                        txt_coupang = f"{int(v_coupang):,} {u}"
                        txt_real = f"{int(v_real):,} {u}"
                    else:
                        txt_coupang = f"{v_coupang:.2f} {u}"
                        txt_real = f"{v_real:.2f} {u}"
                        
                    if is_fixed:
                        real_val_disp = "동일값"
                        diff_disp = "보정 영향 없음"
                        diff_color = "#94A3B8"
                    else:
                        real_val_disp = txt_real
                        diff = v_real - v_coupang
                        if k in ["ROAS", "CVR", "CTR"]:
                           sign = "+" if diff >= 0 else ""
                           diff_disp = f"차이: {sign}{diff:.2f}%p"
                           diff_color = "#10B981" if diff >= 0 else "#EF4444"
                        else:
                           sign = "+" if diff >= 0 else ""
                           pct = (diff / v_coupang * 100) if v_coupang > 0 else 0
                           diff_disp = f"차이: {sign}{int(diff):,}원 ({sign}{pct:.1f}%)"
                           diff_color = "#10B981" if diff >= 0 else "#EF4444"
                           
                    with cols_card[c_idx]:
                        st.markdown(f"""
                      <div class="premium-card" style="padding: 12px 10px; margin-bottom: 5px; height: 145px; border-color: #3B82F6; text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                          <div style="font-size: 0.95rem; font-weight: bold; color: #E2E8F0; margin-bottom: 8px;">{t}</div>
                          <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 4px;">쿠팡시스템 기준: {txt_coupang}</div>
                          <div style="font-size: 0.95rem; font-weight: bold; color: #FFA726; margin-bottom: 4px;">내 판매가 기준: {real_val_disp}</div>
                          <div style="font-size: 0.8rem; color: {diff_color}; font-weight: bold;">{diff_disp}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
            st.markdown("---")
            
            st.markdown("### 📊 집행광고비 vs 광고전환매출 추이 비교 (3선 차트)")
            pd_data = analyzer.get_daily_performance()
            memos = load_json(MEMOS_FILE, [])
            if pd_data and not pd_data['total'].empty:
                render_real_price_chart_streamlit(pd_data['total'], p_val, memos)
            else:
                st.info("성과 차트를 표시할 추이 데이터가 없습니다.")
                
            st.markdown("---")
            st.subheader("📋 쿠팡시스템 기준 vs 내 판매가 기준 상세 대조표 (가로형)")
            
            row_coupang = ["쿠팡시스템 기준"]
            row_real = ["내 판매가 기준"]
            row_diff = ["차액 (이익 변동)"]
            
            row_coupang.append(f"{int(sales_coupang):,}원")
            row_real.append(f"{int(sales_real):,}원")
            diff_sales = sales_real - sales_coupang
            pct_sales = (diff_sales / sales_coupang * 100) if sales_coupang > 0 else 0
            row_diff.append(f"+{int(diff_sales):,}원 (+{pct_sales:.1f}%)" if diff_sales >= 0 else f"{int(diff_sales):,}원 ({pct_sales:.1f}%)")
            
            row_coupang.append(f"{roas_coupang:.2f}%")
            row_real.append(f"{roas_real:.2f}%")
            diff_roas = roas_real - roas_coupang
            row_diff.append(f"+{diff_roas:.2f}%p" if diff_roas >= 0 else f"{diff_roas:.2f}%p")
            
            row_coupang.append(f"{overall.get('CVR', 0):.2f}%")
            row_real.append("동일값")
            row_diff.append("0%p")
            
            row_coupang.append(f"{overall.get('CTR', 0):.2f}%")
            row_real.append("동일값")
            row_diff.append("0%p")
            
            row_coupang.append(f"{int(overall.get('imp', 0)):,}회")
            row_real.append("동일값")
            row_diff.append("-")
            
            row_coupang.append(f"{int(overall.get('click', 0)):,}회")
            row_real.append("동일값")
            row_diff.append("-")
            
            row_coupang.append(f"{int(overall.get('conv_qty', 0)):,}회")
            row_real.append("동일값")
            row_diff.append("-")
            
            row_coupang.append(f"{int(overall.get('orders', 0)):,}건")
            row_real.append("동일값")
            row_diff.append("-")
            
            row_coupang.append(f"{int(sales_coupang):,}원")
            row_real.append(f"{int(total_sales_real):,}원")
            diff_total_sales = total_sales_real - sales_coupang
            pct_total_sales = (diff_total_sales / sales_coupang * 100) if sales_coupang > 0 else 0
            row_diff.append(f"+{int(diff_total_sales):,}원 (+{pct_total_sales:.1f}%)" if diff_total_sales >= 0 else f"{int(diff_total_sales):,}원 ({pct_total_sales:.1f}%)")
            
            row_coupang.append(f"{int(total_qty):,}개")
            row_real.append("동일값")
            row_diff.append("-")
            
            horizontal_cols = [
                "구분", "광고 전환매출", "광고수익률", "전환율", "클릭률", 
                "노출수", "클릭수", "광고 전환 판매수", "광고 전환 주문수", "전체 매출", "전체 판매수"
            ]
            
            df_horizontal = pd.DataFrame([row_coupang, row_real, row_diff], columns=horizontal_cols)
            st.dataframe(df_horizontal, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# 5-2. Tab 2: ⚙️ 키워드/입찰
# -----------------------------------------------------------------------------
with tab_keyword:
    # 스타일은 상단 글로벌 CSS 블록으로 통합 이관 완료
    
    keyword_classes = load_json(CLASSES_FILE, {})

    sub_kw_tab1, sub_kw_tab2, sub_kw_tab3, sub_kw_tab4 = st.tabs([
        "🔍 키워드 분석", "🎯 타겟 관리", "⚙️ 수동 관리", "🚫 제외 관리"
    ])
    
    summary_df = analyzer.summary_df
    
    if "kw_search_input" not in st.session_state:
        st.session_state["kw_search_input"] = ""
        
    with sub_kw_tab1:
        if summary_df is not None and not summary_df.empty:
            df_display = summary_df.copy()

            # 키워드 검색 및 필터 해제 한 줄 통합 배치 (세로 여백 최소화)
            col_search1, col_search2, col_search3, col_search4, col_search5, col_search6 = st.columns([1.5, 3.0, 1.0, 1.0, 1.5, 2.6])
            with col_search1:
                st.markdown("<div style='margin-top: 6px; font-size: 0.95rem; font-weight: bold; color: #E2E8F0; text-align: right;'>🔍 키워드 검색:</div>", unsafe_allow_html=True)
            with col_search2:
                kw_search_input = st.text_input("kw_search", value=st.session_state.get("kw_search_input", ""), label_visibility="collapsed", placeholder="검색어 입력 (예: 두릅)", key="kw_search_unique_key_unique")
            with col_search3:
                btn_search = st.button("검색", use_container_width=True, key="kw_search_btn")
                if btn_search:
                    st.session_state["kw_search_input"] = kw_search_input
                    st.rerun()
            with col_search4:
                btn_init = st.button("초기화", use_container_width=True, key="kw_init_btn")
                if btn_init:
                    st.session_state["kw_search_input"] = ""
                    st.rerun()
            with col_search5:
                # 초기화 버튼 옆으로 배치 이동된 필터 해제 버튼
                reset_all = st.button("필터 해제", use_container_width=True, key="reset_all_kw_filters_btn")
                if reset_all:
                    st.session_state["kw_search_input"] = ""
                    st.rerun()
                    
            # 필터링 적용
            if st.session_state["kw_search_input"].strip():
                search_q = st.session_state["kw_search_input"].strip()
                df_display = df_display[
                    df_display['kw'].str.contains(search_q, case=False, na=False) |
                    df_display['pname'].str.contains(search_q, case=False, na=False)
                ]
            # --- Pagination 제거 (전체 렌더링) ---
            total_items = len(df_display)
            st.markdown(f"<div style='margin-top: 8px; margin-bottom: 8px; color: #E2E8F0; font-weight: bold;'>📊 총 {total_items:,}건</div>", unsafe_allow_html=True)
            df_display_page = df_display
            # --- Pagination 제거 끝 ---
            
            # 데스크톱 Populate Treeview 포맷팅 완벽 이식 (캐싱 + 페이징 적용으로 체감속도 극대화)
            df_display_dict = df_display_page.to_dict('records')
            search_q = st.session_state.get("kw_search_input", "")
            
            # st.markdown을 이용한 메인 DOM 렌더링으로 iframe 보안 샌드박스 우회
            html_table, row_count = get_cached_keyword_html(df_display_dict, search_q)
            st.markdown(html_table, unsafe_allow_html=True)
            
            # 메인 DOM에 스크립트를 직접 주입 (iframe 우회 방식을 완벽하게 복구)
            js_code = """
            <script>
            (function(){
                var parentDoc = window.parent.document;

                window.parent.doAction = function(action){
                    var menu = parentDoc.getElementById("ctx-menu");
                    if(!menu) return;
                    var kw = menu.dataset.kw || "";
                    if(kw && action){
                        try {
                            var inputs = parentDoc.querySelectorAll('input[aria-label="kw_mover_secret_trigger"]');
                            if(inputs.length > 0) {
                                var input = inputs[inputs.length - 1];
                                var nativeSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, "value").set;
                                nativeSetter.call(input, action + "|||" + kw + "|||" + Date.now());
                                input.dispatchEvent(new Event("input", { bubbles: true }));
                                input.dispatchEvent(new Event("change", { bubbles: true }));
                                input.focus({preventScroll: true});
                                setTimeout(function(){ input.blur(); }, 100);
                            }
                        }catch(e){console.error(e);}
                    }
                    menu.style.display="none";
                };

                var sortState={};
                function sortTable(ci){
                    var tb = parentDoc.querySelector("#orange-keyword-table tbody");
                    if(!tb)return;
                    var rows = Array.from(tb.querySelectorAll("tr.keyword-row"));
                    var desc = !sortState[ci];
                    sortState[ci] = desc;
                    rows.sort(function(a,b){
                        var at=(a.cells[ci]?a.cells[ci].innerText:"").trim();
                        var bt=(b.cells[ci]?b.cells[ci].innerText:"").trim();
                        var an=parseFloat(at.replace(/[^0-9.\-]/g,""));
                        var bn=parseFloat(bt.replace(/[^0-9.\-]/g,""));
                        if(!isNaN(an)&&!isNaN(bn))return desc?bn-an:an-bn;
                        return desc?bt.localeCompare(at,"ko"):at.localeCompare(bt,"ko");
                    });
                    rows.forEach(function(r){tb.appendChild(r);});
                    parentDoc.querySelectorAll("#orange-keyword-table th").forEach(function(th,i){
                        var sp=th.querySelector(".sort-arrow");
                        if(sp)sp.innerText="";
                        if(i===ci){
                            if(!sp){
                                sp=parentDoc.createElement("span");
                                sp.className="sort-arrow";
                                sp.style.marginLeft="4px";
                                th.appendChild(sp);
                            }
                            sp.innerText=desc?" ▼":" ▲";
                        }
                    });
                }

                function bindHeaders(){
                    parentDoc.querySelectorAll("#orange-keyword-table th").forEach(function(th,i){
                        if(th.dataset.sortBound)return;
                        th.dataset.sortBound="1";
                        th.style.cursor="pointer";
                        th.addEventListener("click",function(){sortTable(i);});
                    });
                }

                var selRow = null;
                function showMenu(e, kw, row){
                    e.preventDefault();
                    e.stopPropagation();
                    if(selRow && selRow !== row) selRow.style.backgroundColor="#E65100";
                    selRow = row;
                    row.style.backgroundColor="#1d4ed8";
                    var menu = parentDoc.getElementById("ctx-menu");
                    if(!menu) return;
                    var title = parentDoc.getElementById("ctx-kw-title");
                    if(title) title.innerText="🔑 "+kw;
                    menu.dataset.kw = kw;
                    menu.style.display="block";
                    var x = e.clientX, y = e.clientY;
                    if(x+215 > window.parent.innerWidth) x = window.parent.innerWidth-220;
                    if(y+240 > window.parent.innerHeight) y = window.parent.innerHeight-245;
                    menu.style.left = x+"px";
                    menu.style.top = y+"px";
                    setTimeout(function(){
                        parentDoc.addEventListener("click", hideMenu, {once:true});
                    }, 50);
                }

                function hideMenu(){
                    var m = parentDoc.getElementById("ctx-menu");
                    if(m) m.style.display="none";
                }
                
                function bindRows(){
                    parentDoc.querySelectorAll("tr.keyword-row").forEach(function(row){
                        if(row.dataset.bound)return;
                        row.dataset.bound="1";
                        row.addEventListener("click",function(){
                            if(selRow && selRow !== row) selRow.style.backgroundColor="#E65100";
                            selRow = row;
                            row.style.backgroundColor="#1d4ed8";
                        });
                        row.addEventListener("contextmenu",function(e){
                            showMenu(e, row.dataset.keyword||"", row);
                        });
                    });
                }
                
                var attempts = 0;
                function tryBind(){
                    var tb = parentDoc.querySelector("#orange-keyword-table tbody");
                    if(tb){
                        bindRows();
                        bindHeaders();
                    } else if(attempts < 10){
                        attempts++;
                        setTimeout(tryBind, 200);
                    }
                }
                setTimeout(tryBind, 500);
            })();
            </script>
            """
            import streamlit.components.v1 as components
            components.html(js_code, height=0, width=0)

            
            # 하단 여백 추가
            st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
        else:
            st.warning("분석 결과 테이블을 로드할 수 없습니다.")
            
    def render_management_tab_web(cls_name):
        cls_kws = [k for k, v in keyword_classes.items() if v == cls_name]
        if cls_kws:
            st.write(f"현재 **{cls_name}**으로 설정된 키워드 개수: {len(cls_kws)}개")
            
            rows_mgmt = []
            for kw in cls_kws:
                rows_mgmt.append({
                    "키워드": kw,
                    "최초 등록일": datetime.now().strftime("%Y-%m-%d"),
                    "메모": ""
                })
            df_mgmt = pd.DataFrame(rows_mgmt)
            st.dataframe(df_mgmt, use_container_width=True, hide_index=True)
            
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                target_del = st.multiselect("목록에서 제외할 키워드 선택", cls_kws, key=f"del_sel_mult_{cls_name}_web_unique")
                if st.button("🗑️ 등급 지정 해제 (목록에서 삭제)", key=f"del_btn_act_{cls_name}_web_unique", use_container_width=True):
                    if target_del:
                        for td in target_del:
                            if td in keyword_classes:
                                del keyword_classes[td]
                        save_json(CLASSES_FILE, keyword_classes)
                        st.success("선택한 키워드의 등급 설정이 해제되었습니다.")
                        st.rerun()
                    else:
                        st.warning("제외할 키워드를 선택해 주세요.")
            with col_act2:
                st.markdown("📋 **클립보드 복사 영역**")
                st.text_area("키워드 복사 (아래 텍스트를 복사하세요)", value="\n".join(cls_kws), height=100, key=f"copy_area_{cls_name}_web_unique")
        else:
            st.info(f"등록된 {cls_name} 키워드가 없습니다.")
 
    with sub_kw_tab2:
        st.markdown("#### 🎯 타겟 키워드 관리")
        render_management_tab_web("타겟")
        
    with sub_kw_tab3:
        st.markdown("#### ⚙️ 수동 관리 키워드 관리")
        render_management_tab_web("수동")
        
    with sub_kw_tab4:
        st.markdown("#### 🚫 제외 키워드 관리")
        render_management_tab_web("제외")

# -----------------------------------------------------------------------------
# 5-3. Tab 3: 🛡️ AI분석/도구
# -----------------------------------------------------------------------------
with tab_tools:
    sub_tool_tab1, sub_tool_tab2, sub_tool_tab3, sub_tool_tab4, sub_tool_tab5 = st.tabs([
        "🛡️ AI 나침반", "📦 상품 성과", "🧮 순익 계산기", "📐 0.64법칙 공급가 계산기", "🔮 AI 시뮬레이터"
    ])
    
    # 5-3-1. AI 나침반
    with sub_tool_tab1:
        st.subheader("🛡️ AI 최종 종합 판정 나침반")
        memos = load_json(MEMOS_FILE, [])
        diagnosis = analyzer.get_ai_diagnosis(memos)
        if diagnosis:
            diag_html = render_ai_diagnosis_html(diagnosis)
            st.markdown(diag_html, unsafe_allow_html=True)
        else:
            st.warning("진단서를 작성할 데이터가 부족합니다.")

    # 5-3-2. 상품 성과
    with sub_tool_tab2:
        st.subheader("📦 상품별 분석 차트 조회")
        
        m_map = analyzer._get_column_mapping(analyzer.raw_df)
        pname_col = m_map.get('pname')
        
        if pname_col and pname_col in analyzer.raw_df.columns:
            # 매출 사전 구축을 위한 데이터 전처리
            df_clean = analyzer.raw_df.copy()
            for k in ['sales', 'dir_sales', 'indir_sales']:
                col_name = m_map.get(k)
                if col_name:
                    df_clean[col_name] = pd.to_numeric(df_clean[col_name].astype(str).str.replace(',', '').str.replace('₩', '').str.replace('원', ''), errors='coerce').fillna(0)
            
            product_sales_dict = df_clean.groupby(pname_col)[m_map.get('sales')].sum().to_dict() if m_map.get('sales') else {}
            product_dir_sales_dict = df_clean.groupby(pname_col)[m_map.get('dir_sales')].sum().to_dict() if m_map.get('dir_sales') else {}
            product_indir_sales_dict = df_clean.groupby(pname_col)[m_map.get('indir_sales')].sum().to_dict() if m_map.get('indir_sales') else {}
            
            products = df_clean[pname_col].dropna().unique().tolist()
            products = [str(p).strip() for p in products if str(p).strip() and str(p).strip() != '-']
            # 매출액 내림차순 정렬 (매출순 -> 가나다순)
            products.sort(key=lambda p: (-product_sales_dict.get(p, 0), p))
            
            # 매출 상태별 포맷팅 및 실제 상품명 매핑
            formatted_products = []
            prod_map = {}
            for p in products:
                sales_val = product_sales_dict.get(p, 0)
                dir_val = product_dir_sales_dict.get(p, 0)
                indir_val = product_indir_sales_dict.get(p, 0)
                if sales_val > 0:
                    if dir_val > 0:
                        btn_txt = f"🟢 [매출 발생] {p[:40]}... (직접: {int(dir_val):,}원 / 간접: {int(indir_val):,}원 | 총: {int(sales_val):,}원)"
                    else:
                        btn_txt = f"🟡 [간접 매출만] {p[:40]}... (직접: 0원 / 간접: {int(indir_val):,}원 | 총: {int(sales_val):,}원)"
                else:
                    btn_txt = f"⚪ [무매출] {p[:40]}..."
                formatted_products.append(btn_txt)
                prod_map[btn_txt] = p
                
            selected_formatted = st.selectbox("📦 분석할 상품명을 선택하세요", formatted_products, key="selected_product_formatter_unique")
            selected_product = prod_map.get(selected_formatted)
            
            if selected_product:
                # 해당 상품에 해당하는 행 필터링 및 서브 분석기 구동
                raw_filtered = analyzer.raw_df[analyzer.raw_df[pname_col] == selected_product].copy()
                if not raw_filtered.empty:
                    sub_analyzer = CoupangAdAnalyzer()
                    sub_analyzer.raw_df = raw_filtered
                    sub_analyzer.process()
                    
                    sub_overall = sub_analyzer.get_overall_summary()
                    sub_region_summary = sub_analyzer.get_region_summary()
                    
                    # --- [Part 1] 상단 12대 성능 요약 카드 렌더링 ---
                    st.markdown("#### 📊 상품 성능 요약 지표")
                    render_kpi_summary_cards_streamlit(sub_overall, sub_region_summary)
                    
                    # --- [Part 2] 경영 투자 나침반 가이드라인 (expander) 렌더링 ---
                    st.markdown("---")
                    st.markdown("#### 🧭 대표님을 위한 2대 광고투자 경영 나침반 가이드라인")
                    
                    roas = sub_overall.get('ROAS', 0.0) if sub_overall else 0.0
                    spend = sub_overall.get('spend', 0.0) if sub_overall else 0.0
                    sales = sub_overall.get('sales', 0.0) if sub_overall else 0.0
                    spend_ratio = (spend / sales * 100) if sales > 0 else 0.0
                    
                    q1_verdict = (
                        f"현재 이 상품의 광고 ROAS는 {roas:.1f}%입니다. "
                        + ("기준선(330%)을 초과하여 흐름이 양호한 편이나, 사입 원가와 배송비를 감안하여 '가짜 흑자' 여부를 꼭 검증하셔야 합니다!" 
                           if roas >= 330 else 
                           "기준선(330%) 미만으로 저조하여 적자 장사일 위험이 큽니다! 아래 3대 차트로 증액 여부를 냉정히 판정해 보세요.")
                    )
                    q2_verdict = (
                        f"현재 이 상품의 매출 대비 광고비 비중은 {spend_ratio:.1f}%입니다. "
                        + (f"광고비 비중이 전체 매출의 10%를 돌파({spend_ratio:.1f}%)하여 위험 수위입니다! 행동 강령에 따라 즉시 제외 키워드를 정리하고 CVR을 끌어올려 광고비 비중을 마진율 밑으로 낮추셔야 합니다." 
                           if spend_ratio > 10 else 
                           "광고비 비중이 10% 이하로 안정 영역에서 잘 방어되고 있습니다. 마진율 마지노선 이하인지 계속 모니터링하세요.")
                    )
                    
                    with st.expander(f"❓ Q1. 광고수익률(ROAS)이 좋아지면 무조건 광고비를 더 투자(증액)해도 될까요?  (판정: {q1_verdict})"):
                        q1_detail_text = (
                            "**1️⃣ [최우선 판정선 - 12번 차트: 광고 차감 후 최종 순수익 vs 광고비 추이]**\n"
                            " - [판단 기준] : 지출 광고비(빨간 선)를 우상향으로 증액했을 때, 하늘색 실선인 [진짜 최종 순이익]이 빨간 선보다 높은 위치에서 함께 평행하게 우상향하며 뻗어 올라가야만 진정한 성공 증액 상태입니다!\n"
                            " - [⚠️ 위험 신호] : 광고비 빨간 선은 쭉쭉 뻗어 올라가는데 하늘색 순이익 선이 아래로 꺾이거나 0원 밑(영하 적자 구간)으로 처박힌다면, 겉으로만 포장이 바쁘고 실제로는 '가짜 흑자 독수독과' 장사이므로 즉시 증액을 멈춰야 합니다.\n\n"
                            f"**2️⃣ [효율 검증 - 3번 차트: 광고비 vs ROAS 추이]**\n"
                            f" - [현재 상태] : 현재 상품의 평균 광고 ROAS는 {roas:.1f}%로, 흑자 기준선(330%) 대비 " + (
                                "안정권 위에 있습니다. 일별 실시간 추이에서도 무너지지 않는지 대조해 보세요." if roas >= 330 else
                                "저조하여 비효율 헛클릭 키워드에 예산이 새고 있을 가능성이 높습니다! 즉시 제외 키워드를 점검하십시오."
                            ) + "\n\n"
                            "**3️⃣ [이익 안전 마진띠 - 8번 차트: 날짜별 광고비·광고매출 추이]**\n"
                            " - [판단 기준] : 아래 빨간 실선(광고비)과 위 하늘색 실선(광고매출액) 사이의 벌어진 간격(이익 공간)이 좁혀지지 않고 점점 더 아득히 멀어지는 '확장형 대칭'을 이루고 있는지 확인하세요. 이 간격이 태평양처럼 넓어질수록 사장님의 주머니가 두둑해집니다.\n"
                            " - [⚠️ 위험 신호] : 광고비 예산을 쏟아부었는데 두 선의 간격이 서로 키스하듯 달라붙거나 심지어 교차한다면, 번 돈의 100%를 쿠팡 광고비로 기부하고 있는 비상 적자 상태이므로 절대 광고비를 1원도 올리시면 안 됩니다!"
                        )
                        st.markdown(q1_detail_text)
                        
                    with st.expander(f"❓ Q2. 광고비가 더 나가지만 판매량(주문수)도 증가하면 줄이지 말고 계속 더 투자해야 할까요?  (판정: {q2_verdict})"):
                        q2_detail_text = (
                            "**1️⃣ [집중 관찰 영역 - 11번 차트: 광고비 비중 및 광고 기여도 추이]**\n"
                            f" - [비법 분석] : 노란색 [매출 대비 광고비 비중 선]이 사장님이 계산기 탭에 적은 [내 마진율 점선(초록색)]보다 높게 치솟았다면 100% 적자 장사입니다! (현재 이 상품의 광고비 비중은 {spend_ratio:.1f}%)\n"
                            " - [행동 강령] : 특히 광고비 비중이 전체 매출의 10%를 넘어가면(빨간 땡땡이 경고선 돌파 시) 즉시 제외 키워드를 정리하고, 썸네일과 상세페이지를 뜯어고쳐 전환율(CVR)을 끌어올려 광고비 비중을 마진율 밑으로 강제로 밀어 넣으셔야 합니다!"
                        )
                        st.markdown(q2_detail_text)
                        
                    # --- [Part 3] 돋보기 AI 진단 처방전 및 상대 지수 차트 ---
                    st.markdown("---")
                    sub_pd_data = sub_analyzer.get_daily_performance()
                    if sub_pd_data and not sub_pd_data['total'].empty:
                        sub_df = sub_pd_data['total'].copy().sort_values('p_date')
                        sub_by_region = sub_pd_data.get('by_region', pd.DataFrame())
                        
                        render_magnifier_diagnosis_streamlit(sub_df, by_region_df=sub_by_region)
                        
                        st.markdown("#### 🔎 영역별 광고효율 돋보기 상대 지수 차트")
                        memos = load_json(MEMOS_FILE, [])
                        render_magnifier_chart_streamlit(sub_df, by_region_df=sub_by_region, memos=memos)
                        
                        # --- [Part 4] 상품 성과 12대 대형 추이 차트 ---
                        st.markdown("---")
                        st.markdown("#### 📈 상품 12대 광고 성과 추이 그래프")
                        sub_kw = sub_analyzer.summary_df
                        render_large_trend_chart_streamlit(sub_df, sub_kw, memos)
                else:
                    st.info("해당 상품의 일별 분석 데이터가 존재하지 않습니다.")
        else:
            st.warning("상품 목록을 식별할 수 없습니다.")

    # 5-3-3. 순익 계산기
    with sub_tool_tab3:
        st.subheader("🧮 ROAS 순익 계산기")
        st.markdown("<p style='color: #93C5FD;'>이 상품이 실제로 내 지갑을 뚱뚱하게 해주는지, 마이너스를 만드는지 계산해 줍니다.</p>", unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### 📥 제품 및 광고정보 입력")
            c_name = st.text_input("제품명", value="전기장판")
            c_cost = st.number_input("제품 원가 (사입단가, 원)", value=20000, step=100)
            c_qty = st.number_input("판매 갯수 (개)", value=30, step=1)
            c_price = st.number_input("실제 판매가격 (최종 결제액, 원)", value=42900, step=500)
            c_coupang = st.number_input("쿠팡 등록가 (할인 전 가격, 원)", value=52900, step=500)
            c_fee_pct = st.number_input("수수료율 (%)", value=11.0, step=0.1)
            c_tax_pct = st.number_input("부가세율 (%)", value=10.0, step=0.1)
            c_shipping = st.number_input("배송비/물류비 (원)", value=3000, step=100)
            c_etc_cost = st.number_input("포장/기타비용 (원)", value=500, step=50)
            c_ad_spend = st.number_input("광고비용 (원)", value=400000, step=10000)
            
        with col_c2:
            st.markdown("#### 📋 마진 분석 성과표")
            
            # 수수료 및 부가세
            fee = c_price * (c_fee_pct / 100.0)
            tax = c_price * (c_tax_pct / 100.0)
            
            # 정산금 및 순이익
            settlement_per_item = c_price - fee - tax - c_shipping
            profit_per_item = settlement_per_item - c_cost - c_etc_cost
            margin_rate = (profit_per_item / c_price * 100) if c_price > 0 else 0
            
            sales = c_price * c_qty
            roas = (sales / c_ad_spend * 100) if c_ad_spend > 0 else 0
            real_profit = (profit_per_item * c_qty) - c_ad_spend
            
            # END ROAS & 최대 사입원가
            real_end_roas = ((c_coupang * 1.1) / profit_per_item * 100) if profit_per_item > 0 else 0
            real_max_cost = c_price - fee - tax - c_shipping - c_etc_cost - (c_price * 0.2)
            real_max_cost = max(real_max_cost, 0.0)
            
            # 마진 상태 색상
            status_color = "#34D399" if real_profit > 0 else "#EF4444"
            profit_word = "흑자 (수익발생) 🟢" if real_profit > 0 else "적자 (손실발생) 🔴"
            
            st.markdown(f"""
          <div class="premium-card" style="border-color: {status_color}; background-color: rgba(15, 23, 42, 0.9);">
              <div class="card-header" style="color: white; font-size:1.2rem;">최종 결과 판정</div>
              <div class="metric-value" style="color: {status_color}; font-size: 2.2rem;">{int(real_profit):,} 원</div>
              <div style="font-weight: bold; font-size:1.1rem; color: {status_color};">{profit_word}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 세부 스펙 리스트
            st.markdown(f"""
            - **1개당 쿠팡 정산액:** `{int(settlement_per_item):,}` 원 (수수료/세금/배송비 공제 후)
            - **1개당 순이익:** `{int(profit_per_item):,}` 원 (원가 공제 후)
            - **제품 마진율:** `{margin_rate:.1f}`%
            - **총 전환매출:** `{int(sales):,}` 원 (수량 {int(c_qty)}개 기준)
            - **현재 광고 ROAS:** `{roas:.1f}`%
            - **🛡️ 앤드 로하스 (END ROAS):** `<span style='color: #EC4899; font-weight: bold;'>{real_end_roas:.1f}%</span>`
              *(광고 효율 점수가 이 수치보다 높아야 적자가 면해집니다)*
            - **🛑 20% 마진 사수 최대원가:** `<span style='color: #FBBF24; font-weight: bold;'>{int(real_max_cost):,}원</span>`
              *(마진율 20%를 지키기 위해 사입할 수 있는 최대 단가 마지노선)*
            """, unsafe_allow_html=True)

    # 5-3-4. 0.64법칙 공급가 계산기
    with sub_tool_tab4:
        st.subheader("📐 0.64법칙 공급가 계산기")
        
        # 가이드라인 섹션
        st.markdown("""
      <div class="premium-card" style="border-color: #FBBF24; background-color: rgba(30, 41, 59, 0.6); margin-bottom: 20px;">
          <h4 style="color: #FBBF24; margin-top: 0;">💡 0.64 법칙이란?</h4>
          <p style="color: #E2E8F0; line-height: 1.6;">
                초보 셀러분들이 <b>내 판매가</b>를 기준으로 얼마에 물건을 떼와야(소싱해야) 내가 원하는 마진을 남길 수 있는지 한방에 알려주는 마법의 공식입니다.<br><br>
                <b>[계산 원리]</b><br>
                판매가(100%)에서 <b>쿠팡 수수료(부가세 포함 12%)</b>와 내가 남기고 싶은 <b>내 마진(24%)</b>을 빼면 <b>64%</b>가 남습니다.<br>
                즉, <b>내 판매가의 64%</b>가 내가 지출할 수 있는 [원가 + 택배비]의 최대치가 됩니다.<br>
                여기서 배송비(택배비)를 빼주면 내가 도매처에서 사올 수 있는 <b>'실제 공급처 타겟 단가'</b>가 나옵니다!
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_rule1, col_rule2 = st.columns(2)
        with col_rule1:
            st.markdown("#### 📥 기준값 입력")
            rule_price = st.number_input("판매가 (원)", value=12300, step=100, key="rule_price")
            rule_fee = st.number_input("쿠팡 수수료율 (%, 부가세 포함)", value=12.0, step=0.1, key="rule_fee")
            rule_margin = st.number_input("내 목표 마진율 (%)", value=24.0, step=0.1, key="rule_margin")
            rule_shipping = st.number_input("배송비/택배비 (원)", value=3000, step=100, key="rule_shipping")
            rule_qty = st.number_input("예상 판매량 (개)", value=100, step=10, key="rule_qty")

        with col_rule2:
            st.markdown("#### 📋 0.64법칙 타겟 단가 분석표")
            
            # 계산 로직
            rule_ratio = (100 - rule_fee - rule_margin) / 100.0
            rule_cost_with_shipping = rule_price * rule_ratio
            rule_target_cost = rule_cost_with_shipping - rule_shipping
            rule_profit_per_item = rule_price * (rule_margin / 100.0)
            rule_total_profit = rule_profit_per_item * rule_qty
            
            st.markdown(f"""
          <div class="premium-card" style="border-color: #3B82F6; background-color: rgba(15, 23, 42, 0.9);">
              <div class="card-header" style="color: white; font-size:1.1rem;">공급처에서 받아야 하는 실제 단가</div>
              <div class="metric-value" style="color: #3B82F6; font-size: 2.2rem; margin-top: 10px;">{int(rule_target_cost):,} 원</div>
              <div style="font-weight: bold; font-size:1rem; color: #94A3B8; margin-top: 5px;">(순수 도매 타겟 가격, 택배비 차감 후)</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
          <div style="margin-top: 15px; padding: 15px; background-color: rgba(30, 41, 59, 0.5); border-radius: 10px;">
                <ul style="color: #E2E8F0; line-height: 2.0; font-size: 1.05rem; list-style-type: none; padding-left: 0;">
                    <li>📦 <b>택배비 포함원가 ({int(rule_ratio*100)}%):</b> <span style="color: #00E5FF; font-weight: bold;">{int(rule_cost_with_shipping):,}원</span></li>
                    <li>💸 <b>1개당 내 순수익 ({rule_margin}%):</b> <span style="color: #10B981; font-weight: bold;">{int(rule_profit_per_item):,}원</span></li>
                    <li>💰 <b>예상 총 수익 ({int(rule_qty)}개 판매 시):</b> <span style="color: #FBBF24; font-weight: bold;">{int(rule_total_profit):,}원</span></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    # 5-3-5. AI 시뮬레이터
    with sub_tool_tab5:
        st.subheader("🔮 AI 광고 작동원리 & 미래 시뮬레이터")
        st.markdown("<p style='color: #C084FC;'>설정하신 예산과 단가를 토대로 쿠팡 AI 마케터의 예상 행동 방안을 시뮬레이션해 줍니다.</p>", unsafe_allow_html=True)
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("#### 📥 시뮬레이션 조건 입력")
            s_budget = st.number_input("1. 일일 광고 예산 (원)", value=30000, step=5000)
            s_roas = st.number_input("2. 목표 광고 효율 (ROAS %)", value=350, step=10)
            s_cpc = st.number_input("3. 평균 CPC 단가 (원)", value=1000, step=50)
            s_price = st.number_input("4. 제품 판매 가격 (원)", value=20000, step=1000)
            s_pname = st.text_input("5. 대상 제품명 (카테고리)", value="가방백팩")
            
        with col_s2:
            st.markdown("#### 📋 AI 행동 예측 보고서")
            
            # 수학적 역산
            target_revenue = s_budget * (s_roas / 100.0)
            target_sales = target_revenue / s_price
            max_clicks = s_budget / s_cpc
            req_cvr = (target_sales / max_clicks) * 100 if max_clicks > 0 else 0
            
            cvr_realistic = 3.0
            req_clicks_realistic = target_sales / (cvr_realistic / 100.0)
            req_budget_realistic = req_clicks_realistic * s_cpc
            budget_deficit_factor = req_budget_realistic / s_budget if s_budget > 0 else 0
            
            # 1. 특명 카드
            st.markdown(f"""
          <div class="premium-card">
              <div class="card-header" style="color: #60A5FA;">🎯 쿠팡 AI가 부여받은 특명 (목표치)</div>
              <p style="margin-bottom:0; font-size:0.95rem; line-height:1.6;">
                    • <b>목표 매출액:</b> {int(target_revenue):,} 원 (일 {int(s_budget):,}원 예산으로 {s_roas:.0f}% 달성 미션)<br>
                    • <b>목표 판매량:</b> 약 {target_sales:.1f}개 ({int(s_price):,}원짜리 {s_pname} 기준)<br>
                    • <i>AI의 속마음: "나는 하루 만에 {int(s_price):,}원짜리 {s_pname}를 {target_sales:.1f}개 팔아야만 해!"</i>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # 2. 현실 분석 카드
            cvr_warning_color = "#EF4444" if req_cvr > 5.0 else "#10B981"
            status_text = "❌ 도저히 불가능 (정공법 불가)" if req_cvr > 5.0 else "✅ 운영 가능 범위"
            st.markdown(f"""
          <div class="premium-card" style="border-color: {cvr_warning_color};">
              <div class="card-header" style="color: {cvr_warning_color};">📊 AI의 현실 계산기 & 예산 대비 부족 판단</div>
              <p style="margin-bottom:0; font-size:0.95rem; line-height:1.6;">
                    • <b>예산 내 최대 클릭 한계:</b> {max_clicks:.1f} 회<br>
                    • <b>목표 달성에 필요한 극단적 CVR(전환율):</b> <span style="color:{cvr_warning_color}; font-weight:bold;">{req_cvr:.1f}%</span><br>
                    • <i>카테고리 평균 CVR은 3% 내외입니다.</i><br>
                    • <b>평균 CVR(3%) 대입 시 필요 클릭:</b> {req_clicks_realistic:.1f} 회<br>
                    • <b>평균 CVR(3%) 기준 필요 일예산:</b> {int(req_budget_realistic):,} 원 (약 {budget_deficit_factor:.1f}배 부족)<br>
                    • <b>최종 판정:</b> <span style="color:{cvr_warning_color}; font-weight:bold;">{status_text}</span>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        # 3. 처방전 & 예상 행로 (하단에 넓게)
        st.markdown("#### 💡 AI 튜닝 처방 및 예상 행로")
        col_s_bot1, col_s_bot2 = st.columns(2)
        with col_s_bot1:
            max_realistic_roas = (3.0 * s_price / s_cpc)
            max_realistic_cpc = (3.0 * s_price) / s_roas if s_roas > 0 else 0
            
            if req_cvr > 3.0:
                tune_text = f"""
                현재 조건에서 현실적인 전환율(3%)을 가정할 때 달성 가능한 최대 ROAS는 <b>{max_realistic_roas:.0f}%</b>입니다.<br>
                따라서 예산을 단순히 올리는 것으로는 목표 ROAS {s_roas:.0f}%를 채울 수 없습니다.<br><br>
                <b>👉 [처방 1] 목표 ROAS 조정 (강력 추천):</b> 목표치를 <b>{max_realistic_roas:.0f}% 이하</b>로 낮춰주어야 AI가 적극 노출시킵니다.<br>
                <b>👉 [처방 2] 평균 CPC 인하:</b> 목표 ROAS를 유지하려면 세부 키워드를 믹싱하여 CPC를 <b>{int(max_realistic_cpc):,}원 이하</b>로 조정해야 합니다.<br>
                <b>👉 [처방 3] 판매량 우선 세팅:</b> 적자를 각오하고 개수를 맞추려면 일예산을 <b>{int(req_budget_realistic):,}원</b>으로 세팅하세요.
                """
            else:
                tune_text = "🎉 현재 설정은 매우 훌륭하고 이상적인 밸런스를 가집니다! AI가 적극적으로 광고 노출 입찰에 가담할 것입니다."
                
            st.markdown(f"""
          <div class="tune-card">
              <div class="card-header" style="color:#C084FC;"> 처방전 (성공 공식)</div>
              <p style="font-size:0.92rem; line-height:1.6; margin-bottom:0;">{tune_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_s_bot2:
            # AI 잠입 행동 예측
            tail_kw1 = f"가성비 {s_pname}"
            tail_kw2 = f"실속형 {s_pname}"
            
            if max_clicks <= 30:
                sojin_time = "단 5~10분 만에"
            elif max_clicks <= 100:
                sojin_time = "오전 중 단 1~2시간 만에"
            else:
                sojin_time = "반나절도 안 돼서"
                
            if req_cvr > 10.0:
                behavior_text = f"""
                <b>🕵️‍♂️ AI의 비밀 우회 계획:</b><br>
                "목표 판매는 불가능하다. 경쟁이 빡센 메인 키워드 <i>'{s_pname}'</i>은 단가가 너무 비싸 소진이 빠르니 전면 회피한다! 대신 저렴한 비검색 영역(상품 하단)이나 경쟁이 없는 롱테일 키워드(예: <i>'{tail_kw1}', '{tail_kw2}'</i>)로 광고를 대피시킨다. 클릭은 적어져서 규모는 안 크겠지만 목표 ROAS {s_roas}%는 간신히 끼워 맞출 것이다."
                """
            elif req_cvr > 3.0:
                behavior_text = f"""
                <b>🕵️‍♂️ AI의 비밀 우회 계획:</b><br>
                "목표 ROAS가 살짝 버겁다. 피크 시간대 노출을 줄이고 간헐적으로 입찰에 들어가서 하루 예산을 {sojin_time} 다 써버리는 걸 방지하자. 가끔 CPC가 싼 외부 지면 노출을 늘려 단가를 희석해야겠다."
                """
            else:
                behavior_text = f"""
                <b>🕵️‍♂️ AI의 비밀 우회 계획:</b><br>
                "예산이 아주 편안하다! 메인 키워드 <i>'{s_pname}'</i> 영역에서 상위 노출 경쟁에 적극 참여하겠다. 매출 규모가 팽창할 테니 지켜보라구!"
                """
                
            st.markdown(f"""
          <div class="predict-card">
              <div class="card-header" style="color:#93C5FD;">🕵️‍♂️ AI 잠입 행동 예측 (우회 도피 경로)</div>
              <p style="font-size:0.92rem; line-height:1.6; margin-bottom:0;">{behavior_text}</p>
            </div>
            """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5-4. Tab 4: 📝 일별 메모
# -----------------------------------------------------------------------------
with tab_memo:
    st.subheader("📝 일별 메모 보드 및 히스토리 관리")
    memos = load_json(MEMOS_FILE, [])
    
    # 세션 상태로 현재 선택된 날짜와 텍스트 관리
    if "memo_date_val" not in st.session_state:
        st.session_state["memo_date_val"] = datetime.today().date()
    if "memo_text_val" not in st.session_state:
        st.session_state["memo_text_val"] = ""
        # 오늘 날짜에 기존 메모가 있다면 초기값 로드
        today_key = st.session_state["memo_date_val"].strftime("%Y-%m-%d")
        existing = next((m for m in memos if m['date'] == today_key), None)
        if existing:
            st.session_state["memo_text_val"] = existing['memo']

    # 메모 폼 UI (form 없이 구성하여 날짜 변경 시 실시간 텍스트 로딩 연동)
    st.markdown("#### ✍️ 일별 메모 기록/수정")
    
    col_md1, col_md2 = st.columns([2, 1])
    with col_md1:
        # 날짜가 바뀌었을 때 콜백을 통해 실시간 텍스트 로딩
        def on_date_change():
            d_str = st.session_state["memo_date_input"].strftime("%Y-%m-%d")
            existing_c = next((m for m in memos if m['date'] == d_str), None)
            if existing_c:
                st.session_state["memo_text_val"] = existing_c['memo']
            else:
                st.session_state["memo_text_val"] = ""
                
        memo_date = st.date_input(
            "메모 날짜", 
            value=st.session_state["memo_date_val"], 
            key="memo_date_input", 
            on_change=on_date_change
        )
        st.session_state["memo_date_val"] = memo_date
        
    with col_md2:
        # 상태 표시 라벨 (새 메모 vs 기존 메모 수정)
        memo_key = memo_date.strftime("%Y-%m-%d")
        existing_memo = next((m for m in memos if m['date'] == memo_key), None)
        if existing_memo:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            st.info("⚠️ 기존 메모가 존재합니다. 저장 시 덮어써집니다.")
        else:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            st.success("🟢 새 메모 입력 가능 상태입니다.")

    memo_text = st.text_area(
        "메모 내용", 
        value=st.session_state["memo_text_val"], 
        placeholder="광고 설정 변경(예: 예산 증액, ROAS 세팅 조정 등) 내역을 기록해 두세요.",
        key="memo_text_area_input"
    )
    # text_area의 값을 실시간으로 세션 상태에 싱크
    st.session_state["memo_text_val"] = memo_text
    
    col_mb1, col_mb2, col_mb3 = st.columns([1, 1, 2])
    with col_mb1:
        if st.button("💾 메모 저장", use_container_width=True, key="save_memo_action_btn"):
            if memo_text.strip():
                d_str = memo_date.strftime("%Y-%m-%d")
                existing = next((m for m in memos if m['date'] == d_str), None)
                if existing:
                    existing['memo'] = memo_text.strip()
                else:
                    new_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    memos.append({
                        "id": new_id,
                        "date": d_str,
                        "memo": memo_text.strip()
                    })
                save_json(MEMOS_FILE, memos)
                st.success("메모가 저장되었습니다!")
                st.rerun()
            else:
                st.error("메모 내용을 입력해 주세요.")
                
    with col_mb2:
        if st.button("🔄 새 메모 쓰기", use_container_width=True, key="new_memo_clear_btn"):
            st.session_state["memo_date_val"] = datetime.today().date()
            st.session_state["memo_text_val"] = ""
            st.rerun()
            
    with col_mb3:
        if existing_memo:
            if st.button("🗑️ 이 메모 삭제", use_container_width=True, key="delete_current_memo_btn", type="primary"):
                memos = [m for m in memos if m['date'] != memo_key]
                save_json(MEMOS_FILE, memos)
                st.session_state["memo_text_val"] = ""
                st.success("메모가 삭제되었습니다.")
                st.rerun()
                
    # 2. 메모 목록 조회
    st.markdown("---")
    st.markdown("#### 📋 작성된 메모 히스토리 (클릭 시 수정 로드)")
    if memos:
        sorted_memos = sorted(memos, key=lambda x: x['date'], reverse=True)
        for m in sorted_memos:
            col_m1, col_m2, col_m3 = st.columns([7, 2, 1])
            with col_m1:
                st.markdown(f"📅 **{m['date']}** | {m['memo']}")
            with col_m2:
                # 목록에서 클릭 시 상단 편집폼으로 자동 로드하는 기능 구현
                if st.button("✏️ 불러오기/수정", key=f"edit_load_{m['id']}", use_container_width=True):
                    try:
                        st.session_state["memo_date_val"] = datetime.strptime(m['date'], "%Y-%m-%d").date()
                    except:
                        st.session_state["memo_date_val"] = datetime.today().date()
                    st.session_state["memo_text_val"] = m['memo']
                    st.rerun()
            with col_m3:
                if st.button("🗑️ 삭제", key=f"del_memo_{m['id']}", use_container_width=True):
                    memos = [item for item in memos if item['id'] != m['id']]
                    save_json(MEMOS_FILE, memos)
                    # 현재 편집중이던 메모도 삭제한 거라면 에어리어 비움
                    if st.session_state["memo_date_val"].strftime("%Y-%m-%d") == m['date']:
                        st.session_state["memo_text_val"] = ""
                    st.success("메모가 삭제되었습니다.")
                    st.rerun()
            st.markdown("<div style='border-bottom: 1px solid #1E293B; margin: 10px 0;'></div>", unsafe_allow_html=True)
    else:
        st.info("기록된 메모가 존재하지 않습니다.")

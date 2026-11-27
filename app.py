import streamlit as st
import pandas as pd
import datetime
import base64
import gspread
from google.oauth2.service_account import Credentials
from streamlit_calendar import calendar

# --- ページ設定 ---
st.set_page_config(page_title="給料管理", layout="centered")

# --- 全体デザイン（OLEDダーク・ミニマル・モバイル最適化） ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

/* Streamlit標準の不要UIを非表示 */
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0px !important;
    visibility: hidden !important;
}
[data-testid="stToolbar"], #MainMenu, footer {
    display: none !important;
}

/* ベース背景・文字色 */
.stApp {
    background-color: #09090B !important;
    color: #F4F4F5 !important;
}

html, body, [class*="css"], .stMarkdown, .stTextInput, .stNumberInput,
.stSelectbox, .stButton, .stTabs, input, button, select {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Hiragino Sans",
                 "Hiragino Kaku Gothic ProN", "Plus Jakarta Sans", sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

.block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 3.5rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 760px !important;
}

/* ウィジェットラベル・キャプションの視認性を確実に確保 */
[data-testid="stWidgetLabel"] p,
.stCheckbox label span,
.stCheckbox label p {
    color: #D4D4D8 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}
[data-testid="stCaptionContainer"] p {
    color: #A1A1AA !important;
    font-size: 0.78rem !important;
}
hr {
    border-color: #232630 !important;
    margin: 0.9rem 0 !important;
}

/* ヘッダータイトル */
.app-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 1rem;
    padding: 0 0.15rem;
}
.app-title {
    font-size: 1.55rem;
    font-weight: 800;
    color: #FAFAFA;
    letter-spacing: -0.03em;
    line-height: 1.3;
}
.app-sub {
    font-size: 0.78rem;
    font-weight: 600;
    color: #71717A;
    font-variant-numeric: tabular-nums;
}

/* タブ：ダークセグメントコントロール */
.stTabs [data-baseweb="tab-list"] {
    background-color: #13151B;
    border: 1px solid #232630;
    padding: 4px;
    border-radius: 13px;
    gap: 2px;
    display: flex;
    width: 100%;
    margin-bottom: 1rem;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}
.stTabs [data-baseweb="tab"] {
    flex: 1 1 0;
    justify-content: center;
    height: 2.35rem;
    padding: 0 0.25rem !important;
    font-weight: 600;
    font-size: 0.8rem;
    color: #71717A !important;
    border-radius: 9px !important;
    border: none !important;
    background: transparent;
    white-space: nowrap;
    transition: all 0.15s ease;
}
.stTabs [aria-selected="true"] {
    background-color: #272B36 !important;
    color: #FAFAFA !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}

/* セクション見出し */
.section-header {
    font-size: 0.96rem;
    font-weight: 700;
    color: #FAFAFA;
    letter-spacing: -0.01em;
    margin: 1.1rem 0 0.6rem 0.15rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-header::before {
    content: "";
    display: inline-block;
    width: 3px;
    height: 1rem;
    background-color: #34D399;
    border-radius: 99px;
}

.sub-header {
    font-size: 0.9rem;
    font-weight: 700;
    color: #F4F4F5;
    margin: 0.2rem 0 0.45rem 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.unit-pill {
    font-size: 0.72rem;
    font-weight: 600;
    color: #A1A1AA;
    background: #1E212B;
    border: 1px solid #2C303D;
    padding: 2px 9px;
    border-radius: 99px;
    font-variant-numeric: tabular-nums;
}

/* ダークカード（フォーム・エキスパンダー） */
[data-testid="stForm"] {
    background-color: #13151B !important;
    border: 1px solid #232630 !important;
    border-radius: 16px !important;
    padding: 1.2rem 1.1rem !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
}

[data-testid="stExpander"] {
    background-color: #13151B !important;
    border: 1px solid #232630 !important;
    border-radius: 14px !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    color: #F4F4F5 !important;
    font-weight: 600 !important;
}

/* 入力欄 */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input,
.stTimeInput > div > div > input {
    background-color: #1B1E27 !important;
    border-color: #2D313F !important;
    border-radius: 10px !important;
    color: #FAFAFA !important;
    font-size: 0.92rem !important;
}
.stSelectbox > div > div {
    background-color: #1B1E27 !important;
    border-color: #2D313F !important;
    border-radius: 10px !important;
    color: #FAFAFA !important;
}
.stNumberInput button {
    background-color: #232733 !important;
    color: #E4E4E7 !important;
    border-color: #2D313F !important;
}

/* プライマリボタン（ダーク画面に映えるハイコントラスト白ボタン） */
.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button {
    width: 100%;
    background-color: #FAFAFA !important;
    color: #09090B !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    padding: 0.65rem 1.25rem !important;
    box-shadow: 0 2px 10px rgba(255, 255, 255, 0.08) !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background-color: #E4E4E7 !important;
}

/* ダウンロード・削除など通常ボタン */
.stDownloadButton > button,
.stButton > button:not([kind="primary"]) {
    background-color: #1E212B !important;
    color: #F4F4F5 !important;
    border: 1px solid #2E3240 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

/* サマリー用ダークフィンテックカード */
.hero-card {
    background: linear-gradient(145deg, #181C26 0%, #101218 100%);
    color: #FAFAFA;
    border: 1px solid #292E3D;
    border-radius: 18px;
    padding: 1.35rem 1.3rem;
    margin-bottom: 0.85rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
}
.hero-label {
    font-size: 0.76rem;
    font-weight: 600;
    color: #94A3B8;
    letter-spacing: 0.03em;
}
.hero-value {
    font-size: 2.05rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin: 0.2rem 0 0.8rem 0;
    color: #FFFFFF;
    font-variant-numeric: tabular-nums;
}
.hero-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    padding-top: 0.85rem;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
}
.hero-sub-label {
    font-size: 0.72rem;
    color: #94A3B8;
}
.hero-sub-val {
    font-size: 1.05rem;
    font-weight: 700;
    color: #E2E8F0;
    margin-top: 2px;
    font-variant-numeric: tabular-nums;
}

.stat-card {
    background: #13151B;
    border: 1px solid #232630;
    border-radius: 16px;
    padding: 1.1rem 1.15rem;
    margin-bottom: 0.85rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}
.stat-top {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 0.55rem;
}
.stat-title {
    font-size: 0.86rem;
    font-weight: 700;
    color: #FAFAFA;
}
.stat-ratio {
    font-size: 0.8rem;
    font-weight: 600;
    color: #A1A1AA;
    font-variant-numeric: tabular-nums;
}
.bar-track {
    width: 100%;
    height: 8px;
    background: #232630;
    border-radius: 99px;
    overflow: hidden;
    margin-bottom: 0.65rem;
}
.bar-fill {
    height: 100%;
    border-radius: 99px;
    transition: width 0.3s ease;
}
.stat-rem {
    font-size: 0.86rem;
    font-weight: 700;
    color: #FAFAFA;
    margin-bottom: 0.45rem;
    font-variant-numeric: tabular-nums;
}
.stat-detail {
    font-size: 0.76rem;
    color: #94A3B8;
    line-height: 1.65;
    font-variant-numeric: tabular-nums;
}

/* 選択日・期間ステータスバー */
.day-pill-bar {
    background: #13151B;
    border: 1px solid #232630;
    border-radius: 12px;
    padding: 0.65rem 0.9rem;
    margin: 0.35rem 0 0.75rem 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.82rem;
    color: #A1A1AA;
    font-variant-numeric: tabular-nums;
}
.day-pill-bar strong {
    color: #34D399;
    font-size: 0.98rem;
}

/* カレンダーiframeの角丸 */
iframe[title="streamlit_calendar.calendar"] {
    border-radius: 18px !important;
}
</style>
""", unsafe_allow_html=True)

# --- カレンダー専用CSS（ダークモード・iframe内部に直接適用） ---
CALENDAR_CSS = """
html, body {
    background-color: #09090B !important;
}
.fc {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Hiragino Sans", sans-serif !important;
    background: #13151B !important;
    border-radius: 18px !important;
    padding: 14px 10px 10px 10px !important;
    border: 1px solid #232630 !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
    color: #F4F4F5 !important;
}
.fc-header-toolbar {
    margin-bottom: 12px !important;
    padding: 0 4px !important;
}
.fc .fc-toolbar-title {
    font-size: 1.05rem !important;
    font-weight: 800 !important;
    color: #FAFAFA !important;
    letter-spacing: -0.02em !important;
}
/* モノトーンのダークナビゲーションボタン */
.fc .fc-button-primary {
    background-color: #1E212B !important;
    border: 1px solid #2C303D !important;
    color: #E4E4E7 !important;
    border-radius: 9px !important;
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    padding: 5px 10px !important;
    box-shadow: none !important;
    transition: background-color 0.15s ease !important;
}
.fc .fc-button-primary:hover,
.fc .fc-button-primary:active,
.fc .fc-button-primary:focus {
    background-color: #2B303E !important;
    color: #FFFFFF !important;
    box-shadow: none !important;
}
.fc .fc-button-primary:disabled {
    background-color: #181A22 !important;
    color: #52525B !important;
    border-color: #232630 !important;
    opacity: 1 !important;
}
.fc .fc-button-group > .fc-button {
    margin-left: 4px !important;
    border-radius: 9px !important;
}
/* 格子線を消して極細のダーク区切り線のみにする */
.fc-theme-standard .fc-scrollgrid,
.fc-theme-standard td,
.fc-theme-standard th {
    border: none !important;
}
.fc-col-header {
    border-bottom: 1px solid #1F222C !important;
}
.fc-col-header-cell {
    padding: 4px 0 8px 0 !important;
}
.fc-col-header-cell-cushion {
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    color: #71717A !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    text-decoration: none !important;
}
.fc-col-header-cell.fc-day-sun .fc-col-header-cell-cushion {
    color: #F87171 !important;
}
.fc-col-header-cell.fc-day-sat .fc-col-header-cell-cushion {
    color: #60A5FA !important;
}
.fc-daygrid-body tr {
    border-top: 1px solid #1C1F28 !important;
}
.fc-daygrid-day-frame {
    min-height: 54px !important;
    padding: 4px 1px !important;
    border-radius: 10px !important;
}
.fc-daygrid-day-top {
    justify-content: center !important;
    margin-bottom: 2px !important;
}
.fc-daygrid-day-number {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #E4E4E7 !important;
    width: 26px !important;
    height: 26px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 999px !important;
    padding: 0 !important;
    text-decoration: none !important;
    font-variant-numeric: tabular-nums !important;
}
.fc-day-sun .fc-daygrid-day-number {
    color: #F87171 !important;
}
.fc-day-sat .fc-daygrid-day-number {
    color: #60A5FA !important;
}
.fc-day-other .fc-daygrid-day-number {
    color: #3F3F46 !important;
    font-weight: 500 !important;
}
/* 当日：白丸バッジ */
.fc-day-today {
    background: transparent !important;
}
.fc-day-today .fc-daygrid-day-number {
    background-color: #FAFAFA !important;
    color: #09090B !important;
    font-weight: 800 !important;
}
/* 金額バッジ：ダーク画面で映えるエメラルド */
.fc-daygrid-event {
    background-color: rgba(16, 185, 129, 0.16) !important;
    border: 1px solid rgba(52, 211, 153, 0.25) !important;
    border-radius: 6px !important;
    padding: 1px 2px !important;
    margin: 1px 2px 0 2px !important;
    text-align: center !important;
}
.fc-daygrid-event-harness {
    margin-top: 1px !important;
}
.fc-event-title {
    color: #34D399 !important;
    font-size: 0.63rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    font-variant-numeric: tabular-nums !important;
}
/* 選択中の日付ハイライト */
.fc-bg-event {
    border-radius: 10px !important;
    opacity: 0.9 !important;
}
"""

# --- パスワード認証 ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True

    st.markdown('<div class="app-header"><div class="app-title">給料管理</div></div>', unsafe_allow_html=True)
    with st.form("login_form"):
        pwd = st.text_input("パスワード", type="password", placeholder="パスワードを入力")
        if st.form_submit_button("ログイン", type="primary"):
            if pwd == st.secrets["APP_PASSWORD"]:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("パスワードが一致しません")
    return False

if not check_password():
    st.stop()

# --- Googleスプレッドシート接続 ---
@st.cache_resource
def get_spreadsheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["SPREADSHEET_ID"])

@st.cache_data(ttl=600)
def load_df(sheet_name, columns):
    sh = get_spreadsheet()
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
        ws.append_row(columns)
    data = ws.get_all_records()
    if not data:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(data)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df

def save_df(sheet_name, df):
    sh = get_spreadsheet()
    ws = sh.worksheet(sheet_name)
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.fillna("").values.tolist())
    st.cache_data.clear()

# --- データ読み込み ---
LOG_COLS = [
    "date", "sashisu_start", "sashisu_end", "sashisu_break", "sashisu_normal_h", "sashisu_late_h", "sashisu_pay", "sashisu_trans",
    "kyoshin_loc", "kyoshin_koma", "kyoshin_pay", "kyoshin_trans",
    "toshin_normal_k", "toshin_short_k", "toshin_essay_k", "toshin_pay"
]
BONUS_COLS = ["year_month", "amount", "memo"]
ADJ_COLS = ["year_month", "employer", "amount", "memo"]
PDF_COLS = ["display_name", "employer", "year_month", "chunk_index", "data"]
SETTING_COLS = ["key", "value"]
TOSHIN_RATE_COLS = ["period_key", "normal_unit", "short_unit", "essay_unit"]

df_logs = load_df("logs", LOG_COLS)
df_bonuses = load_df("bonuses", BONUS_COLS)
df_adjs = load_df("adjustments", ADJ_COLS)
df_pdfs = load_df("payslips", PDF_COLS)
df_settings = load_df("settings", SETTING_COLS)
df_toshin_rates = load_df("toshin_rates", TOSHIN_RATE_COLS)

# --- 初期設定値の取得 ---
DEFAULT_SETTINGS = {
    "sashisu_wage": 1250,
    "sashisu_trans": 780,
    "kyoshin_koma_wage": 2268,
    "kyoshin_trans_benten": 400,
    "kyoshin_trans_noda": 880,
    "toshin_normal_unit": 3000,
    "toshin_short_unit": 800,
    "toshin_essay_unit": 1200,
    "fuyo_limit": 1030000,
    "zatsu_limit": 200000,
}

settings = DEFAULT_SETTINGS.copy()
if not df_settings.empty:
    for _, row in df_settings.iterrows():
        if row["key"] in settings:
            settings[row["key"]] = float(row["value"])

# --- 扶養計算対象期間判定関数 ---
def is_kyuyo_fuyo_ym(ym_str, target_year):
    """さしす・京進用：前年12月 〜 当年11月（当年1月〜12月振込分）"""
    ym = str(ym_str)[:7]
    prev_dec = f"{target_year - 1}-12"
    cur_months = {f"{target_year}-{m:02d}" for m in range(1, 12)}
    return ym == prev_dec or ym in cur_months

def is_toshin_fuyo_ym(ym_str, target_year):
    """東進用：当年1月 〜 当年12月（当年2月〜翌年1月振込分）"""
    ym = str(ym_str)[:7]
    return ym.startswith(f"{target_year}-")

# --- 東進 締め期間（28日〜翌月27日）判定・単価取得関数 ---
PERIOD_LABELS = [
    f"{m:02d}28〜{(m % 12) + 1:02d}27" for m in range(1, 13)
]

def get_toshin_period_key(date_str):
    dt = datetime.date.fromisoformat(str(date_str)[:10])
    if dt.day >= 28:
        start_y, start_m = dt.year, dt.month
    else:
        if dt.month == 1:
            start_y, start_m = dt.year - 1, 12
        else:
            start_y, start_m = dt.year, dt.month - 1
    end_m = (start_m % 12) + 1
    return f"{start_y}-{start_m:02d}28〜{end_m:02d}27"

def format_period_range_desc(year_val, label_str):
    start_m = int(label_str[:2])
    end_m = int(label_str[5:7])
    end_y = year_val + 1 if end_m < start_m else year_val
    return f"{year_val}/{start_m:02d}/28 〜 {end_y}/{end_m:02d}/27"

def get_toshin_units_for_period(period_key):
    if not df_toshin_rates.empty:
        matched = df_toshin_rates[df_toshin_rates["period_key"] == period_key]
        if not matched.empty:
            r = matched.iloc[0]
            return (
                int(float(r["normal_unit"])),
                int(float(r["short_unit"])),
                int(float(r["essay_unit"])),
                True
            )
    return (
        int(settings["toshin_normal_unit"]),
        int(settings["toshin_short_unit"]),
        int(settings["toshin_essay_unit"]),
        False
    )

# --- 深夜時間（22時以降）自動計算関数 ---
def calc_sashisu_hours(start_t, end_t, break_min):
    dummy = datetime.date(2000, 1, 1)
    dt_start = datetime.datetime.combine(dummy, start_t)
    dt_end = datetime.datetime.combine(dummy, end_t)
    if dt_end <= dt_start:
        dt_end += datetime.timedelta(days=1)

    dt_22 = datetime.datetime.combine(dummy, datetime.time(22, 0))
    dt_29 = datetime.datetime.combine(dummy + datetime.timedelta(days=1), datetime.time(5, 0))

    total_min = (dt_end - dt_start).total_seconds() / 60
    late_start = max(dt_start, dt_22)
    late_end = min(dt_end, dt_29)
    late_min = max(0, (late_end - late_start).total_seconds() / 60)
    normal_min = total_min - late_min

    if normal_min >= break_min:
        normal_min -= break_min
    else:
        rem = break_min - normal_min
        normal_min = 0
        late_min = max(0, late_min - rem)

    return round(normal_min / 60, 2), round(late_min / 60, 2)

# --- 年・月 独立選択ヘルパー ---
def year_month_selector(prefix_key, label_prefix=""):
    today = datetime.date.today()
    y_opts = list(range(2024, 2036))
    m_opts = [f"{m:02d}" for m in range(1, 13)]

    c1, c2, c3 = st.columns([2, 2, 1.4])
    manual = c3.checkbox("手打ち入力", key=f"{prefix_key}_manual")
    if manual:
        y_val = c1.number_input(f"{label_prefix}年", min_value=2020, max_value=2050, value=today.year, step=1, key=f"{prefix_key}_y_num")
        m_val_num = c2.number_input(f"{label_prefix}月", min_value=1, max_value=12, value=today.month, step=1, key=f"{prefix_key}_m_num")
        return f"{int(y_val)}-{int(m_val_num):02d}"
    else:
        y_idx = y_opts.index(today.year) if today.year in y_opts else 0
        y_sel = c1.selectbox(f"{label_prefix}年", y_opts, index=y_idx, key=f"{prefix_key}_y_sel")
        m_sel = c2.selectbox(f"{label_prefix}月", m_opts, index=today.month - 1, key=f"{prefix_key}_m_sel")
        return f"{y_sel}-{m_sel}"

# --- メインヘッダー ---
today_obj = datetime.date.today()
st.markdown(
    f'<div class="app-header"><div class="app-title">給料管理</div><div class="app-sub">{today_obj.strftime("%Y.%m.%d")}</div></div>',
    unsafe_allow_html=True
)

current_year = today_obj.year
year_options = list(range(2024, 2036))
default_year_idx = year_options.index(current_year) if current_year in year_options else 0

tab_cal, tab_summary, tab_adj, tab_pdf, tab_settings = st.tabs([
    "カレンダー", "集計", "調整・手当", "明細", "設定"
])

# ==========================================
# タブ1：カレンダー ＆ 日別入力
# ==========================================
with tab_cal:
    if "selected_date" not in st.session_state:
        st.session_state["selected_date"] = today_obj.strftime("%Y-%m-%d")

    events = [
        {
            "start": st.session_state["selected_date"],
            "display": "background",
            "backgroundColor": "#272C3D",
        }
    ]
    if not df_logs.empty:
        for _, r in df_logs.iterrows():
            d = str(r["date"])
            s_p = float(r["sashisu_pay"] or 0)
            k_p = float(r["kyoshin_pay"] or 0)
            t_p = float(r["toshin_pay"] or 0)
            day_total = s_p + k_p + t_p
            if day_total > 0:
                events.append({
                    "title": f"¥{int(day_total):,}",
                    "start": d,
                })

    cal_options = {
        "initialView": "dayGridMonth",
        "locale": "en",
        "headerToolbar": {"left": "title", "center": "", "right": "today prev,next"},
        "buttonText": {"today": "今日"},
        "titleFormat": {"year": "numeric", "month": "short"},
        "fixedWeekCount": False,
        "contentHeight": "auto",
        "selectable": True,
    }
    cal_state = calendar(events=events, options=cal_options, custom_css=CALENDAR_CSS, key="shift_calendar")

    def parse_cal_date(raw_str):
        if not raw_str:
            return None
        s = str(raw_str)
        if s.endswith("Z") or "+00:00" in s:
            try:
                dt_utc = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
                dt_jst = dt_utc + datetime.timedelta(hours=9)
                return dt_jst.strftime("%Y-%m-%d")
            except Exception:
                pass
        return s[:10]

    clicked_raw = None
    cal_event_obj = None
    if isinstance(cal_state, dict):
        if cal_state.get("dateClick"):
            cal_event_obj = cal_state["dateClick"]
            clicked_raw = cal_event_obj.get("dateStr") or cal_event_obj.get("date")
        elif cal_state.get("select"):
            cal_event_obj = cal_state["select"]
            clicked_raw = cal_event_obj.get("startStr") or cal_event_obj.get("start")
        elif cal_state.get("eventClick"):
            cal_event_obj = cal_state["eventClick"].get("event", {})
            clicked_raw = cal_event_obj.get("startStr") or cal_event_obj.get("start")

    cal_sig = str(cal_event_obj) if cal_event_obj else ""
    if cal_sig and cal_sig != st.session_state.get("last_cal_sig"):
        st.session_state["last_cal_sig"] = cal_sig
        parsed_date = parse_cal_date(clicked_raw)
        if parsed_date:
            st.session_state["selected_date"] = parsed_date
            st.rerun()

    picked_date = st.date_input(
        "対象日",
        value=datetime.date.fromisoformat(st.session_state["selected_date"])
    )
    if picked_date.strftime("%Y-%m-%d") != st.session_state["selected_date"]:
        st.session_state["selected_date"] = picked_date.strftime("%Y-%m-%d")
        st.rerun()

    sel_date = st.session_state["selected_date"]
    t_period_key = get_toshin_period_key(sel_date)
    tn_unit, ts_unit, te_unit, is_custom_rate = get_toshin_units_for_period(t_period_key)

    existing = df_logs[df_logs["date"] == sel_date]
    row = existing.iloc[0] if not existing.empty else None

    if row is not None:
        cur_day_sum = int(float(row["sashisu_pay"] or 0) + float(row["kyoshin_pay"] or 0) + float(row["toshin_pay"] or 0))
        cur_day_tr = int(float(row["sashisu_trans"] or 0) + float(row["kyoshin_trans"] or 0))
        st.markdown(
            f'<div class="day-pill-bar"><span>{sel_date} の登録額（交通費 ¥{cur_day_tr:,}）</span><strong>¥{cur_day_sum:,}</strong></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(f'<div class="section-header">{sel_date} の勤務入力</div>', unsafe_allow_html=True)

    with st.form("daily_form"):
        # 1. さしす
        st.markdown(
            f'<div class="sub-header"><span>さしす</span><span class="unit-pill">時給 ¥{int(settings["sashisu_wage"]):,}</span></div>',
            unsafe_allow_html=True
        )
        use_sashisu = st.checkbox("出勤あり", value=(row is not None and float(row["sashisu_pay"] or 0) > 0))
        c1, c2, c3 = st.columns(3)
        def_start = datetime.datetime.strptime(row["sashisu_start"], "%H:%M").time() if (row is not None and row["sashisu_start"]) else datetime.time(17, 0)
        def_end = datetime.datetime.strptime(row["sashisu_end"], "%H:%M").time() if (row is not None and row["sashisu_end"]) else datetime.time(23, 0)
        def_break = int(row["sashisu_break"]) if (row is not None and row["sashisu_break"] != "") else 0

        s_start = c1.time_input("開始時間", value=def_start)
        s_end = c2.time_input("終了時間", value=def_end)
        s_break = c3.number_input("休憩（分）", min_value=0, max_value=180, step=15, value=def_break)

        st.divider()

        # 2. 京進
        st.markdown(
            f'<div class="sub-header"><span>京進</span><span class="unit-pill">1コマ ¥{int(settings["kyoshin_koma_wage"]):,}</span></div>',
            unsafe_allow_html=True
        )
        loc_options = ["なし", "弁天町", "野田阪神"]
        def_loc_idx = loc_options.index(row["kyoshin_loc"]) if (row is not None and row["kyoshin_loc"] in loc_options) else 0
        def_koma = int(row["kyoshin_koma"]) if (row is not None and row["kyoshin_koma"] != "") else 0

        k1, k2 = st.columns(2)
        k_loc = k1.selectbox("教室", loc_options, index=def_loc_idx)
        k_koma = k2.number_input("コマ数", min_value=0, max_value=10, step=1, value=def_koma)

        st.divider()

        # 3. 東進
        rate_note = "設定済" if is_custom_rate else "標準"
        st.markdown(
            f'<div class="sub-header"><span>東進</span><span class="unit-pill">{t_period_key}（{rate_note}）</span></div>',
            unsafe_allow_html=True
        )
        st.caption(f"通常 ¥{tn_unit:,} ／ 短答 ¥{ts_unit:,} ／ 記述 ¥{te_unit:,}")
        t1, t2, t3 = st.columns(3)
        def_tn = float(row["toshin_normal_k"]) if (row is not None and row["toshin_normal_k"] != "") else 0.0
        def_ts = float(row["toshin_short_k"]) if (row is not None and row["toshin_short_k"] != "") else 0.0
        def_te = float(row["toshin_essay_k"]) if (row is not None and row["toshin_essay_k"] != "") else 0.0

        t_normal = t1.number_input("通常工数", min_value=0.0, step=0.5, value=def_tn)
        t_short = t2.number_input("模試（短答）", min_value=0.0, step=0.5, value=def_ts)
        t_essay = t3.number_input("模試（記述）", min_value=0.0, step=0.5, value=def_te)

        submitted = st.form_submit_button("登録・更新する", type="primary")
        if submitted:
            if use_sashisu:
                nh, lh = calc_sashisu_hours(s_start, s_end, s_break)
                s_pay = round(nh * settings["sashisu_wage"] + lh * settings["sashisu_wage"] * 1.25)
                s_trans = settings["sashisu_trans"]
                s_start_str, s_end_str = s_start.strftime("%H:%M"), s_end.strftime("%H:%M")
            else:
                nh, lh, s_pay, s_trans, s_start_str, s_end_str = 0, 0, 0, 0, "", ""

            if k_loc != "なし" and k_koma > 0:
                k_pay = round(k_koma * settings["kyoshin_koma_wage"])
                k_trans = settings["kyoshin_trans_benten"] if k_loc == "弁天町" else settings["kyoshin_trans_noda"]
            else:
                k_loc, k_koma, k_pay, k_trans = "なし", 0, 0, 0

            t_pay = round(
                t_normal * tn_unit
                + t_short * ts_unit
                + t_essay * te_unit
            )

            new_row = {
                "date": sel_date,
                "sashisu_start": s_start_str, "sashisu_end": s_end_str, "sashisu_break": s_break,
                "sashisu_normal_h": nh, "sashisu_late_h": lh, "sashisu_pay": s_pay, "sashisu_trans": s_trans,
                "kyoshin_loc": k_loc, "kyoshin_koma": k_koma, "kyoshin_pay": k_pay, "kyoshin_trans": k_trans,
                "toshin_normal_k": t_normal, "toshin_short_k": t_short, "toshin_essay_k": t_essay, "toshin_pay": t_pay,
            }

            df_logs = df_logs[df_logs["date"] != sel_date]
            if s_pay > 0 or k_pay > 0 or t_pay > 0:
                df_logs = pd.concat([df_logs, pd.DataFrame([new_row])], ignore_index=True)
            df_logs = df_logs.sort_values("date")
            save_df("logs", df_logs)
            st.success(f"{sel_date} のデータを保存しました。")
            st.rerun()

# ==========================================
# タブ2：集計・扶養
# ==========================================
with tab_summary:
    target_year = st.selectbox("対象年（西暦）", year_options, index=default_year_idx, key="sum_year")
    y_str = str(target_year)

    num_cols = ["sashisu_pay", "sashisu_trans", "kyoshin_pay", "kyoshin_trans", "toshin_pay"]
    for c in num_cols:
        df_logs[c] = pd.to_numeric(df_logs[c], errors="coerce").fillna(0)
    df_bonuses["amount"] = pd.to_numeric(df_bonuses["amount"], errors="coerce").fillna(0)
    df_adjs["amount"] = pd.to_numeric(df_adjs["amount"], errors="coerce").fillna(0)

    # さしす・京進（前年12月〜当年11月 稼働分 ＝ 当年1月〜12月振込）
    df_logs_kyuyo = df_logs[df_logs["date"].apply(lambda d: is_kyuyo_fuyo_ym(d, target_year)).astype(bool)].copy()
    df_bonuses_fuyo = df_bonuses[df_bonuses["year_month"].apply(lambda ym: is_kyuyo_fuyo_ym(ym, target_year)).astype(bool)].copy()
    df_adjs_kyuyo = df_adjs[df_adjs["year_month"].apply(lambda ym: is_kyuyo_fuyo_ym(ym, target_year)).astype(bool)].copy()

    # 東進（当年1月〜当年12月 稼働分 ＝ 当年2月〜翌年1月振込）
    df_logs_toshin = df_logs[df_logs["date"].apply(lambda d: is_toshin_fuyo_ym(d, target_year)).astype(bool)].copy()
    df_adjs_toshin = df_adjs[df_adjs["year_month"].apply(lambda ym: is_toshin_fuyo_ym(ym, target_year)).astype(bool)].copy()

    adj_sashisu = df_adjs_kyuyo[df_adjs_kyuyo["employer"].isin(["さしす", "さしす（給料）"])]["amount"].sum()
    adj_kyoshin = df_adjs_kyuyo[df_adjs_kyuyo["employer"].isin(["京進", "京進（給料）"])]["amount"].sum()
    adj_toshin = df_adjs_toshin[df_adjs_toshin["employer"].isin(["東進", "東進（報酬）"])]["amount"].sum()

    adj_trans_sashisu = df_adjs_kyuyo[df_adjs_kyuyo["employer"] == "さしす（交通費）"]["amount"].sum()
    adj_trans_kyoshin = df_adjs_kyuyo[df_adjs_kyuyo["employer"] == "京進（交通費）"]["amount"].sum()
    adj_trans_toshin = df_adjs_toshin[df_adjs_toshin["employer"] == "東進（交通費）"]["amount"].sum()
    adj_trans_other = df_adjs_kyuyo[df_adjs_kyuyo["employer"] == "交通費"]["amount"].sum()

    y_sashisu = df_logs_kyuyo["sashisu_pay"].sum() + adj_sashisu
    y_kyoshin = df_logs_kyuyo["kyoshin_pay"].sum() + df_bonuses_fuyo["amount"].sum() + adj_kyoshin
    y_toshin = df_logs_toshin["toshin_pay"].sum() + adj_toshin
    y_fuyo_total = y_sashisu + y_kyoshin + y_toshin

    y_trans_sashisu = df_logs_kyuyo["sashisu_trans"].sum() + adj_trans_sashisu
    y_trans_kyoshin = df_logs_kyuyo["kyoshin_trans"].sum() + adj_trans_kyoshin
    y_trans_toshin = adj_trans_toshin
    y_trans_total = y_trans_sashisu + y_trans_kyoshin + y_trans_toshin + adj_trans_other

    # ヒーローサマリーカード
    st.markdown(f"""
<div class="hero-card">
  <div class="hero-label">{target_year}年 扶養対象 合計（交通費抜）</div>
  <div class="hero-value">¥{int(y_fuyo_total):,}</div>
  <div class="hero-grid">
    <div>
      <div class="hero-sub-label">交通費 合計</div>
      <div class="hero-sub-val">¥{int(y_trans_total):,}</div>
    </div>
    <div>
      <div class="hero-sub-label">年間 合計（交通費込）</div>
      <div class="hero-sub-val">¥{int(y_fuyo_total + y_trans_total):,}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # 扶養上限ゲージカード
    fuyo_limit = max(1, settings["fuyo_limit"])
    fuyo_rem = fuyo_limit - y_fuyo_total
    fuyo_pct = min(100.0, max(0.0, (y_fuyo_total / fuyo_limit) * 100))
    fuyo_color = "#EF4444" if fuyo_pct >= 100 else ("#F59E0B" if fuyo_pct >= 85 else "#34D399")

    st.markdown(f"""
<div class="stat-card">
  <div class="stat-top">
    <span class="stat-title">扶養上限チェック（合算）</span>
    <span class="stat-ratio">¥{int(y_fuyo_total):,} / ¥{int(fuyo_limit):,}</span>
  </div>
  <div class="bar-track"><div class="bar-fill" style="width:{fuyo_pct:.1f}%; background:{fuyo_color};"></div></div>
  <div class="stat-rem">上限まで残り ¥{int(fuyo_rem):,}</div>
  <div class="stat-detail">
    さしす（{target_year - 1}/12〜{target_year}/11稼働）：¥{int(y_sashisu):,}<br>
    京進（{target_year - 1}/12〜{target_year}/11稼働・手当込）：¥{int(y_kyoshin):,}<br>
    東進（{target_year}/01〜{target_year}/12稼働）：¥{int(y_toshin):,}
  </div>
</div>
""", unsafe_allow_html=True)

    # 東進 雑所得上限カード
    zatsu_limit = max(1, settings["zatsu_limit"])
    zatsu_rem = zatsu_limit - y_toshin
    zatsu_pct = min(100.0, max(0.0, (y_toshin / zatsu_limit) * 100))
    zatsu_color = "#EF4444" if zatsu_pct >= 100 else ("#F59E0B" if zatsu_pct >= 85 else "#818CF8")

    extra_tr = f" ／ その他 ¥{int(adj_trans_other):,}" if adj_trans_other != 0 else ""
    st.markdown(f"""
<div class="stat-card">
  <div class="stat-top">
    <span class="stat-title">業務委託 雑所得（東進単体）</span>
    <span class="stat-ratio">¥{int(y_toshin):,} / ¥{int(zatsu_limit):,}</span>
  </div>
  <div class="bar-track"><div class="bar-fill" style="width:{zatsu_pct:.1f}%; background:{zatsu_color};"></div></div>
  <div class="stat-rem">上限まで残り ¥{int(zatsu_rem):,}</div>
  <div class="stat-detail">
    交通費内訳：さしす ¥{int(y_trans_sashisu):,} ／ 京進 ¥{int(y_trans_kyoshin):,} ／ 東進 ¥{int(y_trans_toshin):,}{extra_tr}
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f'<div class="section-header">{target_year}年 月別集計（稼働月ベース）</div>', unsafe_allow_html=True)
    df_y_cal = df_logs[df_logs["date"].astype(str).str.startswith(y_str)].copy()
    df_by_cal = df_bonuses[df_bonuses["year_month"].astype(str).str.startswith(y_str)].copy()
    df_ay_cal = df_adjs[df_adjs["year_month"].astype(str).str.startswith(y_str)].copy()

    if not df_y_cal.empty or not df_by_cal.empty or not df_ay_cal.empty:
        df_y_cal["ym"] = df_y_cal["date"].astype(str).str.slice(0, 7)
        m_logs = df_y_cal.groupby("ym")[num_cols].sum().reset_index()
        m_bonus = df_by_cal.groupby("year_month")["amount"].sum().reset_index().rename(columns={"year_month": "ym", "amount": "特別手当"})

        trans_emp_list = ["さしす（交通費）", "京進（交通費）", "東進（交通費）", "交通費"]
        m_pay_adj = df_ay_cal[~df_ay_cal["employer"].isin(trans_emp_list)].groupby("year_month")["amount"].sum().reset_index().rename(columns={"year_month": "ym", "amount": "給料調整"})
        m_trans_adj = df_ay_cal[df_ay_cal["employer"].isin(trans_emp_list)].groupby("year_month")["amount"].sum().reset_index().rename(columns={"year_month": "ym", "amount": "交通費調整"})

        m_all = pd.merge(m_logs, m_bonus, on="ym", how="outer")
        m_all = pd.merge(m_all, m_pay_adj, on="ym", how="outer")
        m_all = pd.merge(m_all, m_trans_adj, on="ym", how="outer").fillna(0).sort_values("ym")

        m_all["交通費計"] = m_all["sashisu_trans"] + m_all["kyoshin_trans"] + m_all["交通費調整"]
        m_all["稼働給料計"] = m_all["sashisu_pay"] + m_all["kyoshin_pay"] + m_all["toshin_pay"] + m_all["特別手当"] + m_all["給料調整"]
        m_all["合計（交通費込）"] = m_all["稼働給料計"] + m_all["交通費計"]

        disp_cols = ["ym", "sashisu_pay", "kyoshin_pay", "toshin_pay", "特別手当", "給料調整", "稼働給料計", "交通費計", "合計（交通費込）"]
        m_disp = m_all[disp_cols].rename(columns={
            "ym": "稼働年月",
            "sashisu_pay": "さしす",
            "kyoshin_pay": "京進",
            "toshin_pay": "東進",
        })
        st.dataframe(m_disp.set_index("稼働年月").astype(int), use_container_width=True)
    else:
        st.info("表示するデータがありません。")

# ==========================================
# タブ3：調整・手当
# ==========================================
with tab_adj:
    st.markdown('<div class="section-header">金額調整</div>', unsafe_allow_html=True)
    st.caption("振込額との差額をプラスまたはマイナスで入力します。交通費項目は交通費合計にのみ反映されます。")

    a_ym = year_month_selector("adj")
    with st.form("adj_form"):
        a1, a2 = st.columns(2)
        a_emp = a1.selectbox(
            "項目・勤務先",
            ["さしす（給料）", "京進（給料）", "東進（報酬）", "さしす（交通費）", "京進（交通費）", "東進（交通費）"]
        )
        a_amt = a2.number_input("調整額（円・マイナス可）", step=10, value=0)
        a_memo = st.text_input("メモ（例: 端数調整、定期代差額など）")
        if st.form_submit_button("登録する", type="primary"):
            if a_amt != 0:
                new_a = pd.DataFrame([{"year_month": a_ym, "employer": a_emp, "amount": a_amt, "memo": a_memo}])
                df_adjs = pd.concat([df_adjs, new_a], ignore_index=True)
                save_df("adjustments", df_adjs)
                st.success(f"{a_ym} の調整額を登録しました。")
                st.rerun()

    if not df_adjs.empty:
        disp_adjs = df_adjs.rename(columns={"year_month": "年月", "employer": "項目・勤務先", "amount": "金額", "memo": "メモ"})
        st.dataframe(disp_adjs, use_container_width=True)

    st.markdown('<div class="section-header">特別手当</div>', unsafe_allow_html=True)
    st.caption("京進の特別手当を登録します（扶養対象額に加算されます）。")

    b_ym = year_month_selector("bonus")
    with st.form("bonus_form"):
        b_amt = st.number_input("金額（円）", min_value=0, step=500, value=0)
        b_memo = st.text_input("メモ（例: 講習手当、紹介手当など）")
        if st.form_submit_button("登録する", type="primary"):
            if b_amt > 0:
                new_b = pd.DataFrame([{"year_month": b_ym, "amount": b_amt, "memo": b_memo}])
                df_bonuses = pd.concat([df_bonuses, new_b], ignore_index=True)
                save_df("bonuses", df_bonuses)
                st.success(f"{b_ym} の特別手当を登録しました。")
                st.rerun()

    if not df_bonuses.empty:
        disp_bonuses = df_bonuses.rename(columns={"year_month": "年月", "amount": "金額", "memo": "メモ"})
        st.dataframe(disp_bonuses, use_container_width=True)

# ==========================================
# タブ4：給料明細
# ==========================================
with tab_pdf:
    st.markdown('<div class="section-header">給料明細の登録</div>', unsafe_allow_html=True)
    with st.form("pdf_upload_form"):
        p1, p2, p3 = st.columns(3)
        p_emp = p1.selectbox("勤務先", ["さしす", "京進", "東進"], key="pdf_emp")
        p_year = p2.selectbox("年（西暦）", year_options, index=default_year_idx, key="pdf_y")
        p_month = p3.selectbox("月", [f"{m:02d}" for m in range(1, 13)], index=today_obj.month - 1, key="pdf_m")
        uploaded_file = st.file_uploader("PDFファイルを選択", type=["pdf"])

        if st.form_submit_button("保存する", type="primary"):
            if uploaded_file is not None:
                pdf_bytes = uploaded_file.read()
                b64_str = base64.b64encode(pdf_bytes).decode("utf-8")
                ym_str = f"{p_year}-{p_month}"
                disp_name = f"{p_emp}_{ym_str}"

                if not df_pdfs.empty:
                    df_pdfs = df_pdfs[df_pdfs["display_name"] != disp_name]

                chunk_size = 40000
                chunks = [b64_str[i:i + chunk_size] for i in range(0, len(b64_str), chunk_size)]
                new_rows = [
                    {
                        "display_name": disp_name,
                        "employer": p_emp,
                        "year_month": ym_str,
                        "chunk_index": idx,
                        "data": ch
                    }
                    for idx, ch in enumerate(chunks)
                ]
                df_pdfs = pd.concat([df_pdfs, pd.DataFrame(new_rows)], ignore_index=True)
                save_df("payslips", df_pdfs)
                st.success(f"「{disp_name}」を保存しました。")
                st.rerun()
            else:
                st.warning("PDFファイルを選択してください。")

    st.markdown('<div class="section-header">保存済みの給料明細</div>', unsafe_allow_html=True)
    f1, f2 = st.columns(2)
    filter_year = f1.selectbox("年（西暦）", ["すべて"] + [str(y) for y in year_options], index=year_options.index(current_year) + 1 if current_year in year_options else 0)
    filter_emp = f2.selectbox("勤務先", ["すべて", "さしす", "京進", "東進"])

    if not df_pdfs.empty:
        meta_df = df_pdfs[["display_name", "employer", "year_month"]].drop_duplicates().sort_values("year_month", ascending=False)
        if filter_year != "すべて":
            meta_df = meta_df[meta_df["year_month"].astype(str).str.startswith(filter_year)]
        if filter_emp != "すべて":
            meta_df = meta_df[meta_df["employer"] == filter_emp]

        if meta_df.empty:
            st.info("該当する給料明細がありません。")
        else:
            for _, m_row in meta_df.iterrows():
                d_name = m_row["display_name"]
                with st.expander(d_name):
                    sub = df_pdfs[df_pdfs["display_name"] == d_name].sort_values("chunk_index")
                    full_b64 = "".join(sub["data"].astype(str).tolist())
                    raw_bytes = base64.b64decode(full_b64)

                    c_dl, c_del = st.columns([3, 1])
                    c_dl.download_button(
                        label="PDFを開く / ダウンロード",
                        data=raw_bytes,
                        file_name=f"{d_name}.pdf",
                        mime="application/pdf",
                        key=f"dl_{d_name}"
                    )
                    if c_del.button("削除", key=f"del_{d_name}"):
                        df_pdfs = df_pdfs[df_pdfs["display_name"] != d_name]
                        save_df("payslips", df_pdfs)
                        st.rerun()

                    pdf_iframe = f'<iframe src="data:application/pdf;base64,{full_b64}" width="100%" height="500" type="application/pdf"></iframe>'
                    st.markdown(pdf_iframe, unsafe_allow_html=True)
    else:
        st.info("保存済みの給料明細はありません。")

# ==========================================
# タブ5：設定
# ==========================================
with tab_settings:
    st.markdown('<div class="section-header">東進 期間別単価設定（28日〜翌月27日）</div>', unsafe_allow_html=True)
    st.caption("年と期間を選ぶと現在の設定単価が表示されます。更新すると該当期間の既存データも自動再計算されます。")

    cur_period_key = get_toshin_period_key(today_obj.strftime("%Y-%m-%d"))
    cur_p_year = int(cur_period_key[:4])
    cur_p_label = cur_period_key[5:]

    tp1, tp2 = st.columns(2)
    sel_t_year = tp1.selectbox(
        "対象年",
        year_options,
        index=year_options.index(cur_p_year) if cur_p_year in year_options else default_year_idx,
        key="toshin_rate_year"
    )
    sel_t_label = tp2.selectbox(
        "締め期間",
        PERIOD_LABELS,
        index=PERIOD_LABELS.index(cur_p_label) if cur_p_label in PERIOD_LABELS else 0,
        key="toshin_rate_period"
    )

    target_period_key = f"{sel_t_year}-{sel_t_label}"
    range_desc = format_period_range_desc(sel_t_year, sel_t_label)
    cur_tn, cur_ts, cur_te, has_saved_rate = get_toshin_units_for_period(target_period_key)

    status_badge = "設定済単価" if has_saved_rate else "標準単価（未設定）"
    st.markdown(
        f'<div class="day-pill-bar"><span>{range_desc}</span><span class="unit-pill">{status_badge}</span></div>',
        unsafe_allow_html=True
    )

    with st.form("toshin_period_rate_form"):
        tr1, tr2, tr3 = st.columns(3)
        in_tn = tr1.number_input("通常採点（円）", min_value=0, value=cur_tn, step=100, key=f"in_tn_{target_period_key}")
        in_ts = tr2.number_input("模試・短答（円）", min_value=0, value=cur_ts, step=100, key=f"in_ts_{target_period_key}")
        in_te = tr3.number_input("模試・記述（円）", min_value=0, value=cur_te, step=100, key=f"in_te_{target_period_key}")

        if st.form_submit_button("この期間の東進単価を保存・反映", type="primary"):
            if not df_toshin_rates.empty:
                df_toshin_rates = df_toshin_rates[df_toshin_rates["period_key"] != target_period_key]
            new_rate_row = pd.DataFrame([{
                "period_key": target_period_key,
                "normal_unit": in_tn,
                "short_unit": in_ts,
                "essay_unit": in_te,
            }])
            df_toshin_rates = pd.concat([df_toshin_rates, new_rate_row], ignore_index=True).sort_values("period_key")
            save_df("toshin_rates", df_toshin_rates)

            if not df_logs.empty:
                updated_count = 0
                for idx in df_logs.index:
                    d_val = str(df_logs.loc[idx, "date"])
                    if get_toshin_period_key(d_val) == target_period_key:
                        tn = float(df_logs.loc[idx, "toshin_normal_k"] or 0)
                        ts = float(df_logs.loc[idx, "toshin_short_k"] or 0)
                        te = float(df_logs.loc[idx, "toshin_essay_k"] or 0)
                        df_logs.loc[idx, "toshin_pay"] = round(tn * in_tn + ts * in_ts + te * in_te)
                        updated_count += 1
                if updated_count > 0:
                    save_df("logs", df_logs)

            st.success(f"{range_desc} の東進単価を保存しました。")
            st.rerun()

    st.markdown('<div class="section-header">基本時給・交通費・年間上限</div>', unsafe_allow_html=True)
    with st.form("settings_main_form"):
        new_settings = {}
        st.markdown('<div class="sub-header"><span>さしす</span></div>', unsafe_allow_html=True)
        sc1, sc2 = st.columns(2)
        new_settings["sashisu_wage"] = sc1.number_input("時給（円）", value=int(settings["sashisu_wage"]), step=10)
        new_settings["sashisu_trans"] = sc2.number_input("往復交通費（円）", value=int(settings["sashisu_trans"]), step=10)

        st.divider()
        st.markdown('<div class="sub-header"><span>京進</span></div>', unsafe_allow_html=True)
        kc1, kc2, kc3 = st.columns(3)
        new_settings["kyoshin_koma_wage"] = kc1.number_input("1コマ給（円）", value=int(settings["kyoshin_koma_wage"]), step=10)
        new_settings["kyoshin_trans_benten"] = kc2.number_input("弁天町 交通費（円）", value=int(settings["kyoshin_trans_benten"]), step=10)
        new_settings["kyoshin_trans_noda"] = kc3.number_input("野田阪神 交通費（円）", value=int(settings["kyoshin_trans_noda"]), step=10)

        st.divider()
        st.markdown('<div class="sub-header"><span>東進 標準単価（未設定期間用）</span></div>', unsafe_allow_html=True)
        tc1, tc2, tc3 = st.columns(3)
        new_settings["toshin_normal_unit"] = tc1.number_input("通常採点（円）", value=int(settings["toshin_normal_unit"]), step=100)
        new_settings["toshin_short_unit"] = tc2.number_input("模試・短答（円）", value=int(settings["toshin_short_unit"]), step=100)
        new_settings["toshin_essay_unit"] = tc3.number_input("模試・記述（円）", value=int(settings["toshin_essay_unit"]), step=100)

        st.divider()
        st.markdown('<div class="sub-header"><span>年間上限</span></div>', unsafe_allow_html=True)
        lc1, lc2 = st.columns(2)
        new_settings["fuyo_limit"] = lc1.number_input("扶養上限（円）", value=int(settings["fuyo_limit"]), step=10000)
        new_settings["zatsu_limit"] = lc2.number_input("業務委託 雑所得上限（円）", value=int(settings["zatsu_limit"]), step=10000)

        if st.form_submit_button("基本設定を保存する", type="primary"):
            save_s = pd.DataFrame([{"key": k, "value": v} for k, v in new_settings.items()])
            save_df("settings", save_s)
            st.success("基本設定を保存しました。")
            st.rerun()

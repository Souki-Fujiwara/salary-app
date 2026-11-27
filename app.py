import streamlit as st
import pandas as pd
import datetime
import base64
import gspread
from google.oauth2.service_account import Credentials
from streamlit_calendar import calendar

# --- ページ設定 ---
st.set_page_config(page_title="給料計算アプリ", page_icon="💰", layout="centered")

# --- パスワード認証 ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True

    st.title("🔒 ログイン")
    pwd = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if pwd == st.secrets["APP_PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("パスワードが違います")
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

sh = get_spreadsheet()

def load_df(sheet_name, columns):
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
        ws.append_row(columns)
    data = ws.get_all_records()
    if not data:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(data)

def save_df(sheet_name, df):
    ws = sh.worksheet(sheet_name)
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.fillna("").values.tolist())

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

df_logs = load_df("logs", LOG_COLS)
df_bonuses = load_df("bonuses", BONUS_COLS)
df_adjs = load_df("adjustments", ADJ_COLS)
df_pdfs = load_df("payslips", PDF_COLS)
df_settings = load_df("settings", SETTING_COLS)

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

# --- サイドバー：設定変更 ---
with st.sidebar:
    st.header("⚙️ 単価・上限設定")
    st.caption("東進の月別単価や毎年の扶養上限はここで変更できます")
    new_settings = {}
    new_settings["fuyo_limit"] = st.number_input("給与所得 扶養上限 (円)", value=int(settings["fuyo_limit"]), step=10000)
    new_settings["zatsu_limit"] = st.number_input("業務委託(東進) 雑所得上限 (円)", value=int(settings["zatsu_limit"]), step=10000)
    st.divider()
    new_settings["sashisu_wage"] = st.number_input("さしす 時給 (円)", value=int(settings["sashisu_wage"]), step=10)
    new_settings["sashisu_trans"] = st.number_input("さしす 往復交通費 (円)", value=int(settings["sashisu_trans"]), step=10)
    new_settings["kyoshin_koma_wage"] = st.number_input("京進 1コマ給 (円)", value=int(settings["kyoshin_koma_wage"]), step=10)
    new_settings["kyoshin_trans_benten"] = st.number_input("京進 弁天町 交通費 (円)", value=int(settings["kyoshin_trans_benten"]), step=10)
    new_settings["kyoshin_trans_noda"] = st.number_input("京進 野田阪神 交通費 (円)", value=int(settings["kyoshin_trans_noda"]), step=10)
    st.divider()
    new_settings["toshin_normal_unit"] = st.number_input("東進 通常採点 単価 (円)", value=int(settings["toshin_normal_unit"]), step=100)
    new_settings["toshin_short_unit"] = st.number_input("東進 模試(短答) 単価 (円)", value=int(settings["toshin_short_unit"]), step=100)
    new_settings["toshin_essay_unit"] = st.number_input("東進 模試(記述) 単価 (円)", value=int(settings["toshin_essay_unit"]), step=100)

    if st.button("設定を保存", type="primary"):
        save_s = pd.DataFrame([{"key": k, "value": v} for k, v in new_settings.items()])
        save_df("settings", save_s)
        st.success("設定を保存しました！")
        st.rerun()

# --- メイン画面 ---
st.title("💰 バイト給料・シフト管理")

current_year = datetime.date.today().year
year_options = list(range(2024, 2036))
default_year_idx = year_options.index(current_year) if current_year in year_options else 0

tab_cal, tab_summary, tab_adj, tab_pdf = st.tabs([
    "📅 カレンダー", "📊 集計・扶養", "⚖️ 特別手当・調整", "📄 給料明細PDF"
])

# ==========================================
# タブ1：カレンダー ＆ 日別入力
# ==========================================
with tab_cal:
    events = []
    if not df_logs.empty:
        for _, r in df_logs.iterrows():
            d = str(r["date"])
            s_p = float(r["sashisu_pay"] or 0)
            k_p = float(r["kyoshin_pay"] or 0)
            t_p = float(r["toshin_pay"] or 0)
            day_total = s_p + k_p + t_p  # 交通費抜きの合計
            if day_total > 0:
                events.append({
                    "title": f"¥{int(day_total):,}",
                    "start": d,
                    "color": "#2E86C1"
                })

    cal_options = {
        "initialView": "dayGridMonth",
        "locale": "ja",
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
        "selectable": True,
    }
    cal_state = calendar(events=events, options=cal_options, key="shift_calendar")

    if "selected_date" not in st.session_state:
        st.session_state["selected_date"] = datetime.date.today().strftime("%Y-%m-%d")

    if cal_state.get("dateClick"):
        st.session_state["selected_date"] = cal_state["dateClick"]["dateStr"][:10]
    elif cal_state.get("eventClick"):
        st.session_state["selected_date"] = cal_state["eventClick"]["event"]["start"][:10]

    sel_date = st.session_state["selected_date"]
    st.subheader(f"📝 {sel_date} のシフト・工数入力")

    existing = df_logs[df_logs["date"] == sel_date]
    row = existing.iloc[0] if not existing.empty else None

    with st.form("daily_form"):
        # 1. さしす
        st.markdown("#### 🏮 さしす（居酒屋）")
        use_sashisu = st.checkbox("さしすに出勤した", value=(row is not None and float(row["sashisu_pay"] or 0) > 0))
        c1, c2, c3 = st.columns(3)
        def_start = datetime.datetime.strptime(row["sashisu_start"], "%H:%M").time() if (row is not None and row["sashisu_start"]) else datetime.time(17, 0)
        def_end = datetime.datetime.strptime(row["sashisu_end"], "%H:%M").time() if (row is not None and row["sashisu_end"]) else datetime.time(23, 0)
        def_break = int(row["sashisu_break"]) if (row is not None and row["sashisu_break"] != "") else 0

        s_start = c1.time_input("開始時間", value=def_start)
        s_end = c2.time_input("終了時間", value=def_end)
        s_break = c3.number_input("休憩(分)", min_value=0, max_value=180, step=15, value=def_break)

        # 2. 京進
        st.markdown("#### 🏫 京進（塾）")
        loc_options = ["なし", "弁天町", "野田阪神"]
        def_loc_idx = loc_options.index(row["kyoshin_loc"]) if (row is not None and row["kyoshin_loc"] in loc_options) else 0
        def_koma = int(row["kyoshin_koma"]) if (row is not None and row["kyoshin_koma"] != "") else 0

        k1, k2 = st.columns(2)
        k_loc = k1.selectbox("出勤場所", loc_options, index=def_loc_idx)
        k_koma = k2.number_input("コマ数", min_value=0, max_value=10, step=1, value=def_koma)

        # 3. 東進
        st.markdown("#### ✍️ 東進（採点バイト・工数）")
        t1, t2, t3 = st.columns(3)
        def_tn = float(row["toshin_normal_k"]) if (row is not None and row["toshin_normal_k"] != "") else 0.0
        def_ts = float(row["toshin_short_k"]) if (row is not None and row["toshin_short_k"] != "") else 0.0
        def_te = float(row["toshin_essay_k"]) if (row is not None and row["toshin_essay_k"] != "") else 0.0

        t_normal = t1.number_input("通常工数", min_value=0.0, step=0.5, value=def_tn)
        t_short = t2.number_input("模試(短答)", min_value=0.0, step=0.5, value=def_ts)
        t_essay = t3.number_input("模試(記述)", min_value=0.0, step=0.5, value=def_te)

        submitted = st.form_submit_button("この日のデータを登録・更新", type="primary")
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
                t_normal * settings["toshin_normal_unit"]
                + t_short * settings["toshin_short_unit"]
                + t_essay * settings["toshin_essay_unit"]
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
            st.success(f"{sel_date} のデータを保存しました！")
            st.rerun()

# ==========================================
# タブ2：月別・年間集計 ＆ 扶養・雑所得ゲージ
# ==========================================
with tab_summary:
    target_year = st.selectbox("対象年（西暦）", year_options, index=default_year_idx, key="sum_year")
    y_str = str(target_year)

    num_cols = ["sashisu_pay", "sashisu_trans", "kyoshin_pay", "kyoshin_trans", "toshin_pay"]
    for c in num_cols:
        df_logs[c] = pd.to_numeric(df_logs[c], errors="coerce").fillna(0)
    df_bonuses["amount"] = pd.to_numeric(df_bonuses["amount"], errors="coerce").fillna(0)
    df_adjs["amount"] = pd.to_numeric(df_adjs["amount"], errors="coerce").fillna(0)

    df_y = df_logs[df_logs["date"].astype(str).str.startswith(y_str)].copy()
    df_by = df_bonuses[df_bonuses["year_month"].astype(str).str.startswith(y_str)].copy()
    df_ay = df_adjs[df_adjs["year_month"].astype(str).str.startswith(y_str)].copy()

    # 調整額の合算
    adj_sashisu = df_ay[df_ay["employer"] == "さしす"]["amount"].sum()
    adj_kyoshin = df_ay[df_ay["employer"] == "京進"]["amount"].sum()
    adj_toshin = df_ay[df_ay["employer"] == "東進"]["amount"].sum()

    y_sashisu = df_y["sashisu_pay"].sum() + adj_sashisu
    y_kyoshin = df_y["kyoshin_pay"].sum() + df_by["amount"].sum() + adj_kyoshin
    y_kyuyo_total = y_sashisu + y_kyoshin
    y_toshin = df_y["toshin_pay"].sum() + adj_toshin
    y_trans = df_y["sashisu_trans"].sum() + df_y["kyoshin_trans"].sum()

    st.subheader(f"📈 {target_year}年 年間累計 ＆ 上限チェック")

    fuyo_limit = settings["fuyo_limit"]
    fuyo_rem = fuyo_limit - y_kyuyo_total
    st.write(f"**給与所得（さしす＋京進・手当/調整込）**: ¥{int(y_kyuyo_total):,} / 上限 ¥{int(fuyo_limit):,}")
    st.progress(min(1.0, max(0.0, y_kyuyo_total / fuyo_limit)))
    st.caption(f"扶養上限まで残り：**¥{int(fuyo_rem):,}** （※交通費 ¥{int(y_trans):,} は含まず）")

    zatsu_limit = settings["zatsu_limit"]
    zatsu_rem = zatsu_limit - y_toshin
    st.write(f"**業務委託（東進・調整込）**: ¥{int(y_toshin):,} / 上限 ¥{int(zatsu_limit):,}")
    st.progress(min(1.0, max(0.0, y_toshin / zatsu_limit)))
    st.caption(f"雑所得上限まで残り：**¥{int(zatsu_rem):,}**")

    st.divider()
    st.subheader("📅 月別集計（調整額反映済）")
    if not df_y.empty or not df_by.empty or not df_ay.empty:
        df_y["ym"] = df_y["date"].astype(str).str.slice(0, 7)
        m_logs = df_y.groupby("ym")[num_cols].sum().reset_index()
        m_bonus = df_by.groupby("year_month")["amount"].sum().reset_index().rename(columns={"year_month": "ym", "amount": "特別手当"})
        m_adj = df_ay.groupby("year_month")["amount"].sum().reset_index().rename(columns={"year_month": "ym", "amount": "差額調整"})

        m_all = pd.merge(m_logs, m_bonus, on="ym", how="outer")
        m_all = pd.merge(m_all, m_adj, on="ym", how="outer").fillna(0).sort_values("ym")
        m_all["合計(交通費込)"] = (
            m_all["sashisu_pay"] + m_all["sashisu_trans"] +
            m_all["kyoshin_pay"] + m_all["kyoshin_trans"] +
            m_all["toshin_pay"] + m_all["特別手当"] + m_all["差額調整"]
        )
        m_all = m_all.rename(columns={
            "ym": "年月", "sashisu_pay": "さしす", "kyoshin_pay": "京進",
            "toshin_pay": "東進", "sashisu_trans": "さしす交通費", "kyoshin_trans": "京進交通費"
        })
        st.dataframe(m_all.set_index("年月").astype(int), use_container_width=True)
    else:
        st.info("まだデータがありません。")

# ==========================================
# タブ3：京進 特別手当 ＆ ズレた金額の調整
# ==========================================
with tab_adj:
    st.subheader("⚖️ ズレた金額（差額）の手打ち調整")
    st.caption("実際の振込額とズレた分をプラスまたはマイナス（例: -150, 300）で入力してください。")
    with st.form("adj_form"):
        a1, a2 = st.columns(2)
        a_ym = a1.text_input("対象年月 (例: 2026-11)", value=datetime.date.today().strftime("%Y-%m"))
        a_emp = a2.selectbox("勤務先", ["さしす", "京進", "東進"])
        a_amt = st.number_input("調整額 (円・マイナス入力可)", step=10, value=0)
        a_memo = st.text_input("メモ (例: 端数ズレ調整、源泉徴収など)")
        if st.form_submit_button("調整額を登録", type="primary"):
            if a_amt != 0:
                new_a = pd.DataFrame([{"year_month": a_ym, "employer": a_emp, "amount": a_amt, "memo": a_memo}])
                df_adjs = pd.concat([df_adjs, new_a], ignore_index=True)
                save_df("adjustments", df_adjs)
                st.success("調整額を登録しました！")
                st.rerun()

    if not df_adjs.empty:
        st.dataframe(df_adjs, use_container_width=True)

    st.divider()
    st.subheader("🎁 京進 特別手当の登録")
    with st.form("bonus_form"):
        b_ym = st.text_input("対象年月 (例: 2026-11)", value=datetime.date.today().strftime("%Y-%m"), key="b_ym")
        b_amt = st.number_input("金額 (円)", min_value=0, step=500, value=0)
        b_memo = st.text_input("メモ (例: 講習手当、紹介手当など)")
        if st.form_submit_button("特別手当を追加", type="primary"):
            if b_amt > 0:
                new_b = pd.DataFrame([{"year_month": b_ym, "amount": b_amt, "memo": b_memo}])
                df_bonuses = pd.concat([df_bonuses, new_b], ignore_index=True)
                save_df("bonuses", df_bonuses)
                st.success("特別手当を登録しました！")
                st.rerun()

    if not df_bonuses.empty:
        st.dataframe(df_bonuses, use_container_width=True)

# ==========================================
# タブ4：給料明細PDFの保存・閲覧
# ==========================================
with tab_pdf:
    st.subheader("📄 給料明細PDFの登録")
    with st.form("pdf_upload_form"):
        p1, p2, p3 = st.columns(3)
        p_emp = p1.selectbox("勤務先", ["さしす", "京進", "東進"], key="pdf_emp")
        p_year = p2.selectbox("年（西暦）", year_options, index=default_year_idx, key="pdf_y")
        p_month = p3.selectbox("月", [f"{m:02d}" for m in range(1, 13)], index=datetime.date.today().month - 1, key="pdf_m")
        uploaded_file = st.file_uploader("給料明細PDFを選択", type=["pdf"])

        if st.form_submit_button("PDFを保存", type="primary"):
            if uploaded_file is not None:
                pdf_bytes = uploaded_file.read()
                b64_str = base64.b64encode(pdf_bytes).decode("utf-8")
                ym_str = f"{p_year}-{p_month}"
                disp_name = f"{p_emp}_{ym_str}"

                # 既存の同名データがあれば上書き
                if not df_pdfs.empty:
                    df_pdfs = df_pdfs[df_pdfs["display_name"] != disp_name]

                # スプレッドシートの1セル上限(5万文字)対策として4万文字ずつ分割保存
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
                st.success(f"「{disp_name}」を保存しました！")
                st.rerun()
            else:
                st.warning("PDFファイルを選択してください。")

    st.divider()
    st.subheader("📂 保存済みの給料明細")
    f1, f2 = st.columns(2)
    filter_year = f1.selectbox("表示する年（西暦）", ["すべて"] + [str(y) for y in year_options], index=year_options.index(current_year) + 1 if current_year in year_options else 0)
    filter_emp = f2.selectbox("勤務先で絞り込み", ["すべて", "さしす", "京進", "東進"])

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
                with st.expander(f"📄 {d_name}"):
                    sub = df_pdfs[df_pdfs["display_name"] == d_name].sort_values("chunk_index")
                    full_b64 = "".join(sub["data"].astype(str).tolist())
                    raw_bytes = base64.b64decode(full_b64)

                    c_dl, c_del = st.columns([3, 1])
                    c_dl.download_button(
                        label="📱 PDFを開く / ダウンロード",
                        data=raw_bytes,
                        file_name=f"{d_name}.pdf",
                        mime="application/pdf",
                        key=f"dl_{d_name}"
                    )
                    if c_del.button("削除", key=f"del_{d_name}"):
                        df_pdfs = df_pdfs[df_pdfs["display_name"] != d_name]
                        save_df("payslips", df_pdfs)
                        st.rerun()

                    # PCブラウザ向けのインラインプレビュー
                    pdf_iframe = f'<iframe src="data:application/pdf;base64,{full_b64}" width="100%" height="500" type="application/pdf"></iframe>'
                    st.markdown(pdf_iframe, unsafe_allow_html=True)
    else:
        st.info("まだ給料明細が登録されていません。")

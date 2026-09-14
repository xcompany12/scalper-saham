import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import time

st.set_page_config(
    page_title="ScalpTick Fast Action", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .hero-card {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .badge-ready {
        background-color: #dcfce7; color: #15803d;
        padding: 4px 10px; border-radius: 20px; font-weight: 700; font-size: 0.8rem;
    }
    .badge-watch {
        background-color: #fef9c3; color: #854d0e;
        padding: 4px 10px; border-radius: 20px; font-weight: 700; font-size: 0.8rem;
    }
    .time-banner {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        color: #334155;
        margin-bottom: 15px;
    }
    .step-box {
        background-color: #f1f5f9;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 12px;
        font-size: 0.88rem;
        color: #1e293b;
    }
</style>
""", unsafe_allow_html=True)

# State Management
if "custom_stocks" not in st.session_state:
    st.session_state.custom_stocks = []
if "hidden_stocks" not in st.session_state:
    st.session_state.hidden_stocks = []
if "locked_ticker" not in st.session_state:
    st.session_state.locked_ticker = None

# Waktu Jakarta & Status Bursa
jkt_tz = pytz.timezone("Asia/Jakarta")
now_jkt = datetime.now(jkt_tz)
current_time_str = now_jkt.strftime("%d/%m/%Y | %H:%M:%S WIB")

is_weekday = now_jkt.weekday() < 5
hour_val = now_jkt.hour + now_jkt.minute / 60.0
market_open = is_weekday and (9.0 <= hour_val <= 16.0)
market_status_badge = "🟢 BURSA BUKA" if market_open else "🔴 BURSA TUTUP"

st.title("⚡ ScalpTick Fast Action")
st.caption("Fokus Top Saham Teraktif & Eksekusi Split (+2T / +4T / -3T)")

# Top Bar
c_banner, c_toggle = st.columns([2, 1])
with c_banner:
    st.markdown(f"""
    <div class="time-banner">
        🕒 <b>Waktu:</b> {current_time_str} &nbsp;|&nbsp; <b>Status:</b> {market_status_badge}
    </div>
    """, unsafe_allow_html=True)
with c_toggle:
    auto_refresh = st.toggle("⚡ Auto-Sync (30s)", value=True)

# Input Saham Dadakan
with st.expander("➕ Tambah Saham Dadakan (Running Trade)", expanded=False):
    col_in, col_add, col_rst = st.columns([3, 1, 1])
    with col_in:
        new_ticker = st.text_input("Kode Emiten BEI:", placeholder="Contoh: KIJA, DAAZ").upper().strip()
    with col_add:
        st.write("")
        st.write("")
        if st.button("Tambah", use_container_width=True):
            if new_ticker and len(new_ticker) == 4 and new_ticker not in st.session_state.custom_stocks:
                st.session_state.custom_stocks.insert(0, new_ticker)
                st.session_state.locked_ticker = new_ticker
                st.cache_data.clear()
                st.rerun()
    with col_rst:
        st.write("")
        st.write("")
        if st.button("Reset All", use_container_width=True):
            st.session_state.custom_stocks = []
            st.session_state.hidden_stocks = []
            st.cache_data.clear()
            st.rerun()

BASE_RADAR_POOL = [
    "BUMI", "BRMS", "DEWA", "ENRG", "DOID", "MEDC", "ELSA", "RAJA", "TOBA", "BULL",
    "GOTO", "WIFI", "INET", "STRK", "HUMI", "AYAM", "KIJA", "JKON", "WIKA", "PTPP",
    "ADRO", "PTBA", "ANTM", "INCO", "TINS", "HRUM", "MBMA", "NCKL", "PANI", "CUAN",
    "BABP", "BBKP", "ARTO", "BBYB", "BRIS", "ASRI", "LPKR", "PWON", "BSDE", "SMRA"
]
ACTIVE_RADAR_POOL = list(dict.fromkeys(st.session_state.custom_stocks + BASE_RADAR_POOL))

def get_tick_size(price):
    if price < 200:
        return 1
    elif price < 500:
        return 2
    elif price < 2000:
        return 5
    elif price < 5000:
        return 10
    else:
        return 25

@st.cache_data(ttl=30)
def fetch_scalp_data(tickers):
    results = []
    formatted = [f"{t}.JK" for t in tickers]
    
    try:
        daily_data = yf.download(formatted, period="5d", interval="1d", group_by="ticker", threads=True)
    except Exception:
        return pd.DataFrame()

    today_str = datetime.now(pytz.timezone("Asia/Jakarta")).strftime('%Y-%m-%d')

    for t in tickers:
        sym = f"{t}.JK"
        try:
            df_daily = daily_data[sym].dropna() if len(tickers) > 1 else daily_data.dropna()
            if len(df_daily) < 1:
                continue

            last_candle_date = df_daily.index[-1].strftime('%Y-%m-%d')

            if last_candle_date == today_str and len(df_daily) >= 2:
                prev_day = df_daily.iloc[-2]
                today = df_daily.iloc[-1]
                open_p = int(today['Open'])
                high_p = int(today['High'])
                low_p = int(today['Low'])
                last_p = int(today['Close'])
                prev_close = int(prev_day['Close'])
                prev_low = int(prev_day['Low'])
                vol = int(today['Volume'])
            else:
                prev_day = df_daily.iloc[-1]
                prev_close = int(prev_day['Close'])
                prev_low = int(prev_day['Low'])
                
                t_obj = yf.Ticker(sym)
                df_intra = t_obj.history(period="1d", interval="1m")
                
                if not df_intra.empty:
                    open_p = int(df_intra.iloc[0]['Open'])
                    high_p = int(df_intra['High'].max())
                    low_p = int(df_intra['Low'].min())
                    last_p = int(df_intra.iloc[-1]['Close'])
                    vol = int(df_intra['Volume'].sum())
                else:
                    if len(df_daily) >= 2:
                        prev_day = df_daily.iloc[-2]
                        today = df_daily.iloc[-1]
                        open_p = int(today['Open'])
                        high_p = int(today['High'])
                        low_p = int(today['Low'])
                        last_p = int(today['Close'])
                        prev_close = int(prev_day['Close'])
                        prev_low = int(prev_day['Low'])
                        vol = int(today['Volume'])
                    else:
                        continue

            if vol <= 0 or open_p == 0:
                continue

            tick = get_tick_size(open_p)
            rentang_tick = ((high_p - open_p) + (open_p - prev_low)) / tick
            potensi_pct = (rentang_tick * tick / open_p) * 100
            change_day_pct = ((last_p - prev_close) / prev_close) * 100

            badge = "🟢 Siap Tempur" if potensi_pct >= 3.0 and rentang_tick >= 4.0 else "🟡 Pantau"
            color_class = "badge-ready" if "Siap" in badge else "badge-watch"

            results.append({
                "Saham": t,
                "Badge": badge,
                "Color": color_class,
                "Open": open_p,
                "Saat Ini": last_p,
                "Change %": round(change_day_pct, 2),
                "Potensi (%)": round(potensi_pct, 1),
                "Ruang (Tick)": round(rentang_tick, 1),
                "Volume (Lot)": vol // 100,
                "Tick Size": tick,
                "Entry Rekomendasi": f"{open_p} - {open_p + tick}"
            })
        except Exception:
            continue

    res_df = pd.DataFrame(results)
    if not res_df.empty:
        res_df = res_df.sort_values(by="Potensi (%)", ascending=False).reset_index(drop=True)
    return res_df

with st.spinner("Menyaring data pasar..."):
    df_raw = fetch_scalp_data(ACTIVE_RADAR_POOL)

if df_raw.empty:
    st.warning("Belum ada data transaksi aktif di pasar.")
else:
    # Filter buang saham yang di-blacklist user
    custom_in_df = df_raw[df_raw["Saham"].isin(st.session_state.custom_stocks)]
    base_top = df_raw[~df_raw["Saham"].isin(st.session_state.custom_stocks)].head(5)
    df_focus = pd.concat([custom_in_df, base_top]).drop_duplicates(subset=["Saham"]).reset_index(drop=True)

    # Filter out hidden stocks
    if st.session_state.hidden_stocks:
        df_focus = df_focus[~df_focus["Saham"].isin(st.session_state.hidden_stocks)].reset_index(drop=True)

    # Selector Fokus Terkunci
    stock_codes = df_focus["Saham"].tolist()
    default_idx = 0
    if st.session_state.locked_ticker in stock_codes:
        default_idx = stock_codes.index(st.session_state.locked_ticker)

    def on_change_ticker():
        st.session_state.locked_ticker = st.session_state.focus_selector.split(" ")[0]

    select_labels = [f"{r['Saham']} ({r['Badge']}) | Vol: {r['Volume (Lot)']:,} Lot | Potensi: +{r['Potensi (%)']}%" for _, r in df_focus.iterrows()]
    selected_label = st.selectbox(
        "🎯 Pilih Saham Fokus Eksekusi Pagi:", 
        options=select_labels, 
        index=default_idx, 
        key="focus_selector",
        on_change=on_change_ticker
    )

    current_code = selected_label.split(" ")[0]
    st.session_state.locked_ticker = current_code
    active_stock = df_focus[df_focus["Saham"] == current_code].iloc[0]

    # HERO CARD
    st.markdown(f"""
    <div class="hero-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h1 style="margin:0; font-size: 1.8rem; color:#0f172a;">{active_stock['Saham']}</h1>
            <span class="{active_stock['Color']}">{active_stock['Badge']}</span>
        </div>
        <p style="margin:6px 0 0 0; color:#475569; font-size:0.9rem;">
            Open: <b>Rp {active_stock['Open']:,}</b> | Saat Ini: <b>Rp {active_stock['Saat Ini']:,} ({active_stock['Change %']}%)</b> | Vol: <b>{active_stock['Volume (Lot)']:,} Lot</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # KALKULATOR EKSEKUSI
    st.markdown("### 🧮 Eksekusi Split Plan Otomatis")
    default_matched = int(active_stock['Saat Ini']) if active_stock['Saat Ini'] > 0 else int(active_stock['Open'])

    c_entry_in, c_help = st.columns([2, 1])
    with c_entry_in:
        entry_val = st.number_input(
            f"Harga Matched ({active_stock['Saham']}):", 
            min_value=1, 
            max_value=100000, 
            value=default_matched, 
            step=get_tick_size(default_matched),
            key=f"in_entry_{active_stock['Saham']}"
        )
    with c_help:
        st.write("")
        st.caption(f"Fraksi: **Rp {get_tick_size(entry_val)}/tick**\nZona: **Rp {active_stock['Entry Rekomendasi']}**")

    curr_tick = get_tick_size(entry_val)
    tp1 = entry_val + (2 * curr_tick)
    tp2 = entry_val + (4 * curr_tick)
    sl = entry_val - (3 * curr_tick)

    gain1 = ((tp1 - entry_val) / entry_val) * 100
    gain2 = ((tp2 - entry_val) / entry_val) * 100
    loss = ((sl - entry_val) / entry_val) * 100

    col_tp1, col_tp2, col_sl = st.columns(3)
    col_tp1.metric("🎯 TP 1 (Porsi 50%)", f"Rp {tp1:,}", delta=f"+{gain1:.2f}% (+2T)")
    col_tp2.metric("🚀 TP 2 (Porsi 50%)", f"Rp {tp2:,}", delta=f"+{gain2:.2f}% (+4T)")
    col_sl.metric("🛡️ Cut Loss (100%)", f"Rp {sl:,}", delta=f"{loss:.2f}% (-3T)", delta_color="inverse")

    st.markdown("---")

    # ==================== FITUR EDIT / FILTER TABEL ====================
    st.write(f"### 📋 Daftar Saham Paling Layak Pantau ({len(df_focus)} Emiten)")

    with st.expander("⚙️ Edit Tampilan Tabel (Buang Saham / Pilih Kolom)", expanded=False):
        c_del, c_col = st.columns(2)
        with c_del:
            # Dropdown buang saham yang tidak mau dilihat
            all_visible_stocks = df_focus["Saham"].tolist()
            stocks_to_hide = st.multiselect(
                "Buang Saham dari Tabel:",
                options=all_visible_stocks,
                default=st.session_state.hidden_stocks,
                help="Pilih saham yang mau dihilangkan (misal: BBCA)"
            )
            if stocks_to_hide != st.session_state.hidden_stocks:
                st.session_state.hidden_stocks = stocks_to_hide
                st.rerun()

        with c_col:
            # Checklist kolom yang mau dimunculkan
            available_cols = ["Saham", "Badge", "Open", "Saat Ini", "Entry Rekomendasi", "Potensi (%)", "Volume (Lot)"]
            selected_cols = st.multiselect(
                "Pilih Kolom Tampil:",
                options=available_cols,
                default=["Saham", "Open", "Saat Ini", "Potensi (%)", "Volume (Lot)"]
            )

    # Tampilkan tabel yang sudah disaring
    if not selected_cols:
        selected_cols = ["Saham", "Saat Ini", "Potensi (%)"]

    clean_table = df_focus[selected_cols]

    def highlight_clean(row):
        if "Potensi (%)" in row:
            val = row["Potensi (%)"]
            if val >= 3.0:
                return ['background-color: #f0fdf4; color: #14532d; font-weight: 500;'] * len(row)
        return ['background-color: #fafafa; color: #52525b;'] * len(row)

    format_dict = {}
    if "Open" in selected_cols: format_dict["Open"] = "Rp {:,.0f}"
    if "Saat Ini" in selected_cols: format_dict["Saat Ini"] = "Rp {:,.0f}"
    if "Potensi (%)" in selected_cols: format_dict["Potensi (%)"] = "+{:.1f}%"
    if "Volume (Lot)" in selected_cols: format_dict["Volume (Lot)"] = "{:,.0f}"

    styled = clean_table.style.apply(highlight_clean, axis=1).format(format_dict)
    st.dataframe(styled, use_container_width=True, hide_index=True)

if auto_refresh:
    time.sleep(30)
    st.rerun()

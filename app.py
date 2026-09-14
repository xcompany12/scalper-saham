import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import time

st.set_page_config(
    page_title="ScalpTick Pro Radar", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .card-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge-prio {
        background-color: #dcfce7; color: #166534;
        padding: 4px 10px; border-radius: 20px; font-weight: 700; font-size: 0.8rem;
    }
    .badge-mid {
        background-color: #fef9c3; color: #854d0e;
        padding: 4px 10px; border-radius: 20px; font-weight: 700; font-size: 0.8rem;
    }
    .badge-low {
        background-color: #fee2e2; color: #991b1b;
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
</style>
""", unsafe_allow_html=True)

# Inisialisasi memori sesi agar saham fokus & input tidak hilang
if "custom_stocks" not in st.session_state:
    st.session_state.custom_stocks = []
if "locked_ticker" not in st.session_state:
    st.session_state.locked_ticker = None
if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = time.time()

# Waktu Jakarta & Status Bursa
jkt_tz = pytz.timezone("Asia/Jakarta")
now_jkt = datetime.now(jkt_tz)
current_time_str = now_jkt.strftime("%d/%m/%Y | %H:%M:%S WIB")

is_weekday = now_jkt.weekday() < 5
hour_val = now_jkt.hour + now_jkt.minute / 60.0
market_open = is_weekday and (9.0 <= hour_val <= 16.0)
market_status_badge = "🟢 BURSA BUKA" if market_open else "🔴 BURSA TUTUP"

st.title("⚡ ScalpTick Pro Radar")
st.caption("Live Radar & Kalkulator Eksekusi Anti-Reset (IDX)")

# Pool Saham Inti Likuid
BASE_RADAR_POOL = [
    "BUMI", "BRMS", "DEWA", "ENRG", "DOID", "MEDC", "ELSA", "RAJA", "TOBA", "BULL",
    "GOTO", "WIFI", "INET", "STRK", "HUMI", "AYAM", "KIJA", "JKON", "WIKA", "PTPP",
    "ADRO", "PTBA", "ANTM", "INCO", "TINS", "HRUM", "MBMA", "NCKL", "PANI", "CUAN",
    "BABP", "BBKP", "ARTO", "BBYB", "BRIS", "ASRI", "LPKR", "PWON", "BSDE", "SMRA",
    "GIAA", "IRRA", "KAEF", "SMDR", "PPRE"
]

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

def highlight_soft(row):
    val = row["Potensi (%)"]
    if val >= 3.0:
        return ['background-color: #f0fdf4; color: #14532d; font-weight: 500;'] * len(row)
    elif val >= 1.5:
        return ['background-color: #fefce8; color: #713f12; font-weight: 500;'] * len(row)
    else:
        return ['background-color: #fafafa; color: #a1a1aa;'] * len(row)

# ==================== KONTROL AUTO-REFRESH ====================
c_banner, c_toggle = st.columns([2, 1])
with c_banner:
    st.markdown(f"""
    <div class="time-banner">
        🕒 <b>Pindai:</b> {current_time_str} &nbsp;|&nbsp; <b>Status:</b> {market_status_badge}
    </div>
    """, unsafe_allow_html=True)
with c_toggle:
    auto_refresh = st.toggle("⚡ Auto-Sync (30s)", value=True, help="Update harga live otomatis tanpa ubah pilihan saham")

# ==================== INPUT SAHAM DADAKAN ====================
with st.expander("➕ Tambah Saham Dadakan (Running Trade)", expanded=False):
    col_in, col_add, col_rst = st.columns([3, 1, 1])
    with col_in:
        new_ticker = st.text_input("Kode Saham BEI:", placeholder="Contoh: PUDP, TOSK, DAAZ").upper().strip()
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
        if st.button("Reset", use_container_width=True):
            st.session_state.custom_stocks = []
            st.cache_data.clear()
            st.rerun()

ACTIVE_RADAR_POOL = list(dict.fromkeys(st.session_state.custom_stocks + BASE_RADAR_POOL))

# Tombol Manual Refresh & Sortir
col_btn, col_sort = st.columns([1, 2])
with col_btn:
    if st.button("🔄 Scan Manual", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with col_sort:
    sort_option = st.selectbox(
        "Urutkan:",
        ["🔥 Potensi Rentang Tertinggi", "📈 Volume Transaksi Terbanyak"]
    )

@st.cache_data(ttl=30)
def fetch_top_active_data(tickers):
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
                data_status = "Live"
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
                    data_status = "Live 1m"
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
                        data_status = "Close Kemarin"
                    else:
                        continue

            if vol <= 0 or open_p == 0:
                continue

            tick = get_tick_size(open_p)
            rentang_tick = ((high_p - open_p) + (open_p - prev_low)) / tick
            potensi_pct = (rentang_tick * tick / open_p) * 100

            zona_beli = f"{open_p - tick} - {open_p}"
            target_tp = open_p + (3 * tick)
            cut_loss = open_p - (3 * tick)

            gain_pct = ((target_tp - open_p) / open_p) * 100
            loss_pct = ((cut_loss - open_p) / open_p) * 100
            change_day_pct = ((last_p - prev_close) / prev_close) * 100

            if potensi_pct >= 3.0 and rentang_tick >= 4.0:
                badge = "🟢 Prioritas"
                color_tag = "badge-prio"
            elif potensi_pct >= 1.5:
                badge = "🟡 Pantau"
                color_tag = "badge-mid"
            else:
                badge = "🔴 Rendah"
                color_tag = "badge-low"

            results.append({
                "Saham": t,
                "Status": badge,
                "ColorTag": color_tag,
                "Data": data_status,
                "Open": open_p,
                "Saat Ini": last_p,
                "Change %": round(change_day_pct, 2),
                "Entry": zona_beli,
                "TP (+3T)": target_tp,
                "Cut Loss (-3T)": cut_loss,
                "Potensi (%)": round(potensi_pct, 1),
                "Ruang (Tick)": round(rentang_tick, 1),
                "Gain %": round(gain_pct, 2),
                "Loss %": round(loss_pct, 2),
                "Volume (Lot)": vol // 100,
                "Tick Size": tick
            })
        except Exception:
            continue

    res_df = pd.DataFrame(results)
    return res_df

with st.spinner("Memindai data..."):
    df_data = fetch_top_active_data(ACTIVE_RADAR_POOL)

if df_data.empty:
    st.warning("Belum ada data transaksi aktif yang masuk.")
else:
    if "Volume" in sort_option:
        df_data = df_data.sort_values(by="Volume (Lot)", ascending=False).reset_index(drop=True)
    else:
        df_data = df_data.sort_values(by="Potensi (%)", ascending=False).reset_index(drop=True)

    st.write("### 📌 Saham Pilihan Terpilih")
    stock_codes = df_data["Saham"].tolist()

    # Kunci index pilihan saham agar tidak terpental saat data refresh
    default_idx = 0
    if st.session_state.locked_ticker in stock_codes:
        default_idx = stock_codes.index(st.session_state.locked_ticker)

    def on_stock_change():
        st.session_state.locked_ticker = st.session_state.active_selector.split(" ")[0]

    stock_options = [f"{r['Saham']} ({r['Status']}) | Vol: {r['Volume (Lot)']:,} Lot" for _, r in df_data.iterrows()]
    selected_option = st.selectbox(
        "Sentuh untuk ganti saham fokus:", 
        options=stock_options, 
        index=default_idx, 
        key="active_selector", 
        on_change=on_stock_change
    )
    
    current_selected_code = selected_option.split(" ")[0]
    st.session_state.locked_ticker = current_selected_code
    stock = df_data[df_data["Saham"] == current_selected_code].iloc[0]

    # Kartu Data Saham Terkunci
    st.markdown(f"""
    <div class="card-box">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin:0; color:#0f172a;">{stock['Saham']}</h2>
            <span class="{stock['ColorTag']}">{stock['Status']}</span>
        </div>
        <p style="margin:6px 0 0 0; color:#475569; font-size:0.88rem;">
            Volume: <b>{stock['Volume (Lot)']:,} Lot</b> | Status: <b>{stock['Data']}</b> | Rentang: <b>+{stock['Potensi (%)']}%</b> ({stock['Ruang (Tick)']}T)
        </p>
    </div>
    """, unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    f1.metric("Harga Open", f"Rp {stock['Open']:,}")
    f2.metric("Harga Saat Ini", f"Rp {stock['Saat Ini']:,}", delta=f"{stock['Change %']}%")

    # Kalkulator Eksekusi Real-Time
    st.markdown("#### 🧮 Live Execution Calculator")
    st.caption("Hitung target otomatis (fokus saham tetap terkunci):")

    default_entry = int(stock['Saat Ini']) if stock['Saat Ini'] > 0 else int(stock['Open'])
    
    col_entry, col_sl_setting = st.columns([2, 1])
    with col_entry:
        calc_entry = st.number_input(
            f"Harga Matched ({stock['Saham']}):", 
            min_value=1, 
            max_value=100000, 
            value=default_entry, 
            step=get_tick_size(default_entry),
            key=f"entry_{stock['Saham']}"
        )
    with col_sl_setting:
        sl_ticks = st.selectbox(
            "Toleransi SL:", 
            [3, 4, 2], 
            index=0, 
            format_func=lambda x: f"-{x} Tick",
            key=f"sl_{stock['Saham']}"
        )

    custom_tick = get_tick_size(calc_entry)
    calc_tp1 = calc_entry + (3 * custom_tick)
    calc_tp2 = calc_entry + (5 * custom_tick)
    calc_sl = calc_entry - (sl_ticks * custom_tick)

    calc_gain1 = ((calc_tp1 - calc_entry) / calc_entry) * 100
    calc_gain2 = ((calc_tp2 - calc_entry) / calc_entry) * 100
    calc_loss = ((calc_sl - calc_entry) / calc_entry) * 100
    rr_ratio = abs(calc_gain1 / calc_loss) if calc_loss != 0 else 1.0

    c_tp, c_sl = st.columns(2)
    c_tp.metric("Target TP (+3 Tick)", f"Rp {calc_tp1:,}", delta=f"+{calc_gain1:.2f}%")
    c_sl.metric(f"Cut Loss (-{sl_ticks} Tick)", f"Rp {calc_sl:,}", delta=f"{calc_loss:.2f}%", delta_color="inverse")

    st.caption(f"🎯 **Target Agresif (+5T):** Rp {calc_tp2:,} (+{calc_gain2:.2f}%) | **R:R Ratio:** 1 : {rr_ratio:.2f} | **Fraksi:** Rp {custom_tick}/tick")

    st.divider()

    # Tabel Ringkasan
    st.write(f"### 📋 Ringkasan Saham Paling Ramai ({len(df_data)} Emiten)")
    display_cols = ["Saham", "Status", "Open", "Saat Ini", "Entry", "TP (+3T)", "Cut Loss (-3T)", "Potensi (%)", "Volume (Lot)"]
    tabel_ringkas = df_data[display_cols]

    styled_table = tabel_ringkas.style.apply(highlight_soft, axis=1)\
                                      .format({
                                          "Open": "Rp {:,.0f}",
                                          "Saat Ini": "Rp {:,.0f}", 
                                          "TP (+3T)": "Rp {:,.0f}", 
                                          "Cut Loss (-3T)": "Rp {:,.0f}", 
                                          "Potensi (%)": "+{:.1f}%",
                                          "Volume (Lot)": "{:,.0f}"
                                      })
    st.dataframe(styled_table, use_container_width=True, hide_index=True)

# Loop Otomatis 30 Detik Tanpa Mengganggu Interaksi User
if auto_refresh:
    time.sleep(30)
    st.rerun()

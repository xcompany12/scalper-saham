import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(
    page_title="ScalpTick Live Radar", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom Styling
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
        background-color: #f1f5f9;
        border-left: 4px solid #3b82f6;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        color: #334155;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Status Waktu Jakarta
jkt_tz = pytz.timezone("Asia/Jakarta")
now_jkt = datetime.now(jkt_tz)
current_time_str = now_jkt.strftime("%d/%m/%Y | %H:%M:%S WIB")

is_weekday = now_jkt.weekday() < 5
hour_val = now_jkt.hour + now_jkt.minute / 60.0
market_open = is_weekday and (9.0 <= hour_val <= 16.0)
market_status_badge = "🟢 BURSA BUKA" if market_open else "🔴 BURSA TUTUP"

st.title("⚡ ScalpTick Live Radar")
st.caption("Pusat Radar Saham Volatil & Kalkulator Eksekusi 2–3 Tick (IDX)")

st.markdown(f"""
<div class="time-banner">
    🕒 <b>Waktu Pindai:</b> {current_time_str} &nbsp;|&nbsp; <b>Status:</b> {market_status_badge}
</div>
""", unsafe_allow_html=True)

# 3 Sektor Pilihan Inti
FOCUSED_SECTORS = {
    "🔥 Scalping Teraktif & Momentum": [
        "JKON", "BABP", "BRMS", "BUMI", "GOTO", 
        "DEWA", "ENRG", "DOID", "MEDC", "KIJA"
    ],
    "⛏️ Komoditas & Energi (Likuid)": [
        "ADRO", "PTBA", "ANTM", "INCO", "BRMS", 
        "ELSA", "TINS", "HRUM", "BULL", "MEDC"
    ],
    "🏢 Properti, Infra & Digital": [
        "WIFI", "INET", "STRK", "HUMI", "WIKA", 
        "PTPP", "BSDE", "PWON", "KIJA", "JKON"
    ]
}

EXTRA_TICKERS = [
    "AYAM", "STRK", "HUMI", "IRRA", "KAEF", "GIAA", "PPRE", 
    "WEHA", "MPMX", "ASRI", "LPKR", "DILD", "TOBA", "RAJA", 
    "BULL", "ELSA", "WTON", "TOTL", "SMDR", "PUDP"
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

@st.cache_data(ttl=60)
def fetch_focused_data(tickers):
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
                prev_low = int(prev_day['Low'])
                vol = int(today['Volume'])
                data_date = today.name.strftime('%d/%m/%Y (Live)')
            else:
                prev_day = df_daily.iloc[-1]
                prev_low = int(prev_day['Low'])
                
                t_obj = yf.Ticker(sym)
                df_intra = t_obj.history(period="1d", interval="1m")
                
                if not df_intra.empty:
                    open_p = int(df_intra.iloc[0]['Open'])
                    high_p = int(df_intra['High'].max())
                    low_p = int(df_intra['Low'].min())
                    last_p = int(df_intra.iloc[-1]['Close'])
                    vol = int(df_intra['Volume'].sum())
                    data_date = df_intra.index[-1].strftime('%d/%m/%Y (Live)')
                else:
                    if len(df_daily) >= 2:
                        prev_day = df_daily.iloc[-2]
                        today = df_daily.iloc[-1]
                        open_p = int(today['Open'])
                        high_p = int(today['High'])
                        low_p = int(today['Low'])
                        last_p = int(today['Close'])
                        prev_low = int(prev_day['Low'])
                        vol = int(today['Volume'])
                        data_date = today.name.strftime('%d/%m/%Y')
                    else:
                        continue

            if vol <= 0 or open_p == 0:
                continue

            tick = get_tick_size(open_p)
            rentang_tick = ((high_p - open_p) + (open_p - prev_low)) / tick
            potensi_pct = (rentang_tick * tick / open_p) * 100

            zona_beli = f"{open_p - tick} - {open_p}"
            target_tp1 = open_p + (3 * tick)
            target_tp2 = open_p + (5 * tick)
            cut_loss = open_p - (2 * tick)

            gain_pct = ((target_tp1 - open_p) / open_p) * 100
            loss_pct = ((cut_loss - open_p) / open_p) * 100

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
                "Tanggal Data": data_date,
                "Open": open_p,
                "Close/Last": last_p,
                "Badge": badge,
                "ColorTag": color_tag,
                "Potensi (%)": round(potensi_pct, 1),
                "Ruang (Tick)": round(rentang_tick, 1),
                "Zona Beli": zona_beli,
                "Target TP": target_tp1,
                "TP 2": target_tp2,
                "Cut Loss": cut_loss,
                "Gain %": round(gain_pct, 2),
                "Loss %": round(loss_pct, 2),
                "Volume": vol // 100,
                "Tick Size": tick
            })
        except Exception:
            continue

    res_df = pd.DataFrame(results)
    if not res_df.empty:
        res_df = res_df.sort_values(by="Potensi (%)", ascending=False).reset_index(drop=True)
    return res_df

tab1, tab2 = st.tabs(["📊 Radar 3 Sektor Utama", "⚡ Saham Cadangan Lapis 2 & 3"])

# ==================== TAB 1: RADAR 3 SEKTOR ====================
with tab1:
    c_sec, c_rf = st.columns([3, 1])
    with c_sec:
        selected_sector = st.selectbox("Pilih Sektor Fokus:", list(FOCUSED_SECTORS.keys()))
    with c_rf:
        st.write("")
        st.write("")
        if st.button("🔄 Scan", key="btn_sec", use_container_width=True):
            st.cache_data.clear()

    tickers_to_scan = FOCUSED_SECTORS[selected_sector]

    with st.spinner("Memindai sektor..."):
        df_data = fetch_focused_data(tickers_to_scan)

    if df_data.empty:
        st.warning("Data transaksi belum masuk atau pasar sedang libur.")
    else:
        st.write("### 📌 Detail Kartu Eksekusi")
        stock_options = [f"{r['Saham']} ({r['Badge']})" for _, r in df_data.iterrows()]
        selected_option = st.selectbox("Sentuh untuk ganti saham:", options=stock_options, index=0)
        selected_code = selected_option.split(" ")[0]
        stock = df_data[df_data["Saham"] == selected_code].iloc[0]

        st.markdown(f"""
        <div class="card-box">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2 style="margin:0; color:#0f172a;">{stock['Saham']}</h2>
                <span class="{stock['ColorTag']}">{stock['Badge']}</span>
            </div>
            <p style="margin:6px 0 0 0; color:#475569; font-size:0.88rem;">
                Tanggal Data: <b>{stock['Tanggal Data']}</b> | Ruang: <b>+{stock['Potensi (%)']}%</b> ({stock['Ruang (Tick)']} Tick) | Vol: <b>{stock['Volume']:,} Lot</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

        oc1, oc2 = st.columns(2)
        oc1.metric("Harga Open", f"Rp {stock['Open']}")
        oc2.metric("Harga Close / Last", f"Rp {stock['Close/Last']}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Zona Beli", f"Rp {stock['Zona Beli']}")
        c2.metric("Target TP (+3T)", f"Rp {stock['Target TP']}", delta=f"+{stock['Gain %']}%")
        c3.metric("Cut Loss (-2T)", f"Rp {stock['Cut Loss']}", delta=f"{stock['Loss %']}%", delta_color="inverse")
        st.caption(f"🎯 **TP 2 (+5 Tick):** Rp {stock['TP 2']} | **Fraksi:** Rp {stock['Tick Size']}/tick")

        st.divider()

        st.write("### 📋 Tabel Perbandingan (Open vs Close)")
        display_cols = ["Saham", "Open", "Close/Last", "Zona Beli", "Target TP", "Cut Loss", "Potensi (%)"]
        tabel_ringkas = df_data[display_cols]

        styled_table = tabel_ringkas.style.apply(highlight_soft, axis=1)\
                                          .format({
                                              "Open": "Rp {:,.0f}",
                                              "Close/Last": "Rp {:,.0f}", 
                                              "Target TP": "Rp {:,.0f}", 
                                              "Cut Loss": "Rp {:,.0f}", 
                                              "Potensi (%)": "+{:.1f}%"
                                          })
        st.dataframe(styled_table, use_container_width=True, hide_index=True)

# ==================== TAB 2: SAHAM CADANGAN ====================
with tab2:
    st.write("### ⚡ Saham Alternatif Volatil")
    st.caption("Pilihan saham cadangan otomatis tanpa perlu ketik kode")

    if st.button("🔄 Scan Saham Cadangan", key="btn_extra", use_container_width=True):
        st.cache_data.clear()

    with st.spinner("Memindai 20 saham cadangan..."):
        df_extra = fetch_focused_data(EXTRA_TICKERS)

    if df_extra.empty:
        st.warning("Data transaksi belum tersedia.")
    else:
        st.write("### 📌 Detail Kartu Saham Cadangan")
        extra_options = [f"{r['Saham']} ({r['Badge']})" for _, r in df_extra.iterrows()]
        selected_extra = st.selectbox("Pilih Saham:", options=extra_options, index=0)
        extra_code = selected_extra.split(" ")[0]
        ex_stock = df_extra[df_extra["Saham"] == extra_code].iloc[0]

        st.markdown(f"""
        <div class="card-box">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2 style="margin:0; color:#0f172a;">{ex_stock['Saham']}</h2>
                <span class="{ex_stock['ColorTag']}">{ex_stock['Badge']}</span>
            </div>
            <p style="margin:6px 0 0 0; color:#475569; font-size:0.88rem;">
                Tanggal Data: <b>{ex_stock['Tanggal Data']}</b> | Ruang: <b>+{ex_stock['Potensi (%)']}%</b> ({ex_stock['Ruang (Tick)']} Tick) | Vol: <b>{ex_stock['Volume']:,} Lot</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

        eoc1, eoc2 = st.columns(2)
        eoc1.metric("Harga Open", f"Rp {ex_stock['Open']}")
        eoc2.metric("Harga Close / Last", f"Rp {ex_stock['Close/Last']}")

        ec1, ec2, ec3 = st.columns(3)
        ec1.metric("Zona Beli", f"Rp {ex_stock['Zona Beli']}")
        ec2.metric("Target TP (+3T)", f"Rp {ex_stock['Target TP']}", delta=f"+{ex_stock['Gain %']}%")
        ec3.metric("Cut Loss (-2T)", f"Rp {ex_stock['Cut Loss']}", delta=f"{ex_stock['Loss %']}%", delta_color="inverse")
        st.caption(f"🎯 **TP 2 (+5 Tick):** Rp {ex_stock['TP 2']} | **Fraksi:** Rp {ex_stock['Tick Size']}/tick")

        st.divider()

        st.write("### 📋 Tabel Perbandingan Saham Cadangan")
        display_extra_cols = ["Saham", "Open", "Close/Last", "Zona Beli", "Target TP", "Cut Loss", "Potensi (%)"]
        tabel_extra = df_extra[display_extra_cols]

        styled_extra_table = tabel_extra.style.apply(highlight_soft, axis=1)\
                                              .format({
                                                  "Open": "Rp {:,.0f}",
                                                  "Close/Last": "Rp {:,.0f}", 
                                                  "Target TP": "Rp {:,.0f}", 
                                                  "Cut Loss": "Rp {:,.0f}", 
                                                  "Potensi (%)": "+{:.1f}%"
                                              })
        st.dataframe(styled_extra_table, use_container_width=True, hide_index=True)

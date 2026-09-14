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

# Custom Styling agar rapi di HP/iPad
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 100%; }
    .card-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge-prio {
        background-color: #dcfce7; color: #166534;
        padding: 3px 8px; border-radius: 15px; font-weight: 700; font-size: 0.75rem;
    }
    .badge-mid {
        background-color: #fef9c3; color: #854d0e;
        padding: 3px 8px; border-radius: 15px; font-weight: 700; font-size: 0.75rem;
    }
    .badge-low {
        background-color: #fee2e2; color: #991b1b;
        padding: 3px 8px; border-radius: 15px; font-weight: 700; font-size: 0.75rem;
    }
    .time-banner {
        background-color: #f1f5f9;
        border-left: 4px solid #3b82f6;
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        color: #334155;
        margin-bottom: 12px;
    }
    /* Memperbaiki agar tabel tidak berantakan di mobile */
    table { font-size: 0.85rem !important; width: 100% !important; }
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

st.title("⚡ ScalpTick Fast Action")
st.markdown(f"""
<div class="time-banner">
    🕒 {current_time_str} &nbsp;|&nbsp; <b>{market_status_badge}</b>
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

@st.cache_data(ttl=180)
def fetch_focused_data(tickers):
    results = []
    formatted = [f"{t}.JK" for t in tickers]
    try:
        data = yf.download(formatted, period="5d", interval="1d", group_by="ticker", threads=True)
    except Exception:
        return pd.DataFrame()

    for t in tickers:
        sym = f"{t}.JK"
        try:
            df = data[sym].dropna() if len(tickers) > 1 else data.dropna()
            if len(df) >= 2:
                prev_day = df.iloc[-2]
                today = df.iloc[-1]

                data_date = today.name.strftime('%d/%m/%Y')
                last_p = int(today['Close'])
                open_p = int(today['Open'])
                high_p = int(today['High'])
                prev_low = int(prev_day['Low'])
                vol = int(today['Volume'])

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
                    "Tanggal": data_date,
                    "Open": open_p,
                    "Last": last_p,
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

tab1, tab2 = st.tabs(["📊 Radar Sektor", "⚡ Cadangan Lapis 2/3"])

# ==================== TAB 1 ====================
with tab1:
    c_sec, c_rf = st.columns([3, 1])
    with c_sec:
        selected_sector = st.selectbox("Pilih Sektor:", list(FOCUSED_SECTORS.keys()), key="sel_sec")
    with c_rf:
        st.write("")
        st.write("")
        if st.button("🔄 Scan", key="btn_s1", use_container_width=True):
            st.cache_data.clear()

    tickers_to_scan = FOCUSED_SECTORS[selected_sector]

    with st.spinner("Memindai..."):
        df_data = fetch_focused_data(tickers_to_scan)

    if df_data.empty:
        st.warning("Data belum tersedia.")
    else:
        st.write("### 🎯 Pilih Saham Eksekusi")
        stock_options = [f"{r['Saham']} ({r['Badge']})" for _, r in df_data.iterrows()]
        selected_option = st.selectbox("Sentuh untuk ganti:", options=stock_options, index=0, key="sel_stk1")
        selected_code = selected_option.split(" ")[0]
        stock = df_data[df_data["Saham"] == selected_code].iloc[0]

        st.markdown(f"""
        <div class="card-box">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin:0; color:#0f172a;">{stock['Saham']}</h3>
                <span class="{stock['ColorTag']}">{stock['Badge']}</span>
            </div>
            <p style="margin:4px 0 0 0; color:#475569; font-size:0.8rem;">
                Tgl: {stock['Tanggal']} | Ruang: <b>+{stock['Potensi (%)']}%</b> ({stock['Ruang (Tick)']}T) | Vol: <b>{stock['Volume']:,} Lot</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

        oc1, oc2 = st.columns(2)
        oc1.metric("Open", f"Rp {stock['Open']}")
        oc2.metric("Last / Close", f"Rp {stock['Last']}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Zona Beli", f"Rp {stock['Zona Beli']}")
        c2.metric("Target TP (+3T)", f"Rp {stock['Target TP']}", delta=f"+{stock['Gain %']}%")
        c3.metric("Cut Loss (-2T)", f"Rp {stock['Cut Loss']}", delta=f"{stock['Loss %']}%", delta_color="inverse")
        st.caption(f"🎯 **TP 2 (+5T):** Rp {stock['TP 2']} | **Fraksi:** Rp {stock['Tick Size']}/t")

        st.divider()
        st.write("### 📋 Daftar Ringkas Sektor")
        
        # Tampilkan sebagai kartu list ringkas agar tidak patah-patah di layar HP
        for _, row in df_data.iterrows():
            st.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:8px 12px; border-radius:8px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <b>{row['Saham']}</b> <span style="font-size:0.75rem; color:#64748b;">(Open: Rp {row['Open']})</span><br>
                    <span style="font-size:0.8rem; color:#0369a1;">Beli: <b>{row['Zona Beli']}</b> | TP: <b>{row['Target TP']}</b> | SL: <b>{row['Cut Loss']}</b></span>
                </div>
                <div style="text-align:right;">
                    <span class="{row['ColorTag']}">{row['Badge']}</span><br>
                    <span style="font-size:0.8rem; font-weight:600; color:#15803d;">+{row['Potensi (%)']}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ==================== TAB 2 ====================
with tab2:
    st.write("### ⚡ Cadangan Lapis 2 & 3")
    if st.button("🔄 Scan Cadangan", key="btn_s2", use_container_width=True):
        st.cache_data.clear()

    with st.spinner("Memindai..."):
        df_extra = fetch_focused_data(EXTRA_TICKERS)

    if df_extra.empty:
        st.warning("Data belum tersedia.")
    else:
        extra_options = [f"{r['Saham']} ({r['Badge']})" for _, r in df_extra.iterrows()]
        selected_extra = st.selectbox("Pilih Cadangan:", options=extra_options, index=0, key="sel_stk2")
        extra_code = selected_extra.split(" ")[0]
        ex_stock = df_extra[df_extra["Saham"] == extra_code].iloc[0]

        st.markdown(f"""
        <div class="card-box">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin:0; color:#0f172a;">{ex_stock['Saham']}</h3>
                <span class="{ex_stock['ColorTag']}">{ex_stock['Badge']}</span>
            </div>
            <p style="margin:4px 0 0 0; color:#475569; font-size:0.8rem;">
                Tgl: {ex_stock['Tanggal']} | Ruang: <b>+{ex_stock['Potensi (%)']}%</b> ({ex_stock['Ruang (Tick)']}T) | Vol: <b>{ex_stock['Volume']:,} Lot</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

        eoc1, eoc2 = st.columns(2)
        eoc1.metric("Open", f"Rp {ex_stock['Open']}")
        eoc2.metric("Last / Close", f"Rp {ex_stock['Last']}")

        ec1, ec2, ec3 = st.columns(3)
        ec1.metric("Zona Beli", f"Rp {ex_stock['Zona Beli']}")
        ec2.metric("Target TP (+3T)", f"Rp {ex_stock['Target TP']}", delta=f"+{ex_stock['Gain %']}%")
        ec3.metric("Cut Loss (-2T)", f"Rp {ex_stock['Cut Loss']}", delta=f"{ex_stock['Loss %']}%", delta_color="inverse")
        st.caption(f"🎯 **TP 2 (+5T):** Rp {ex_stock['TP 2']} | **Fraksi:** Rp {ex_stock['Tick Size']}/t")

        st.divider()
        st.write("### 📋 Daftar Ringkas Cadangan")

        for _, row in df_extra.iterrows():
            st.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:8px 12px; border-radius:8px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <b>{row['Saham']}</b> <span style="font-size:0.75rem; color:#64748b;">(Open: Rp {row['Open']})</span><br>
                    <span style="font-size:0.8rem; color:#0369a1;">Beli: <b>{row['Zona Beli']}</b> | TP: <b>{row['Target TP']}</b> | SL: <b>{row['Cut Loss']}</b></span>
                </div>
                <div style="text-align:right;">
                    <span class="{row['ColorTag']}">{row['Badge']}</span><br>
                    <span style="font-size:0.8rem; font-weight:600; color:#15803d;">+{row['Potensi (%)']}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

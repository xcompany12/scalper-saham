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

# Preset Sektor Default
DEFAULT_SECTORS = {
    "🔥 Scalping Teraktif & Momentum": [
        "BRMS", "DOID", "KIJA", "ENRG", "MEDC", 
        "BUMI", "DEWA", "JKON", "BABP", "GOTO"
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

# Inisialisasi daftar kustom di Session State
if "sector_stocks" not in st.session_state:
    st.session_state.sector_stocks = {k: list(v) for k, v in DEFAULT_SECTORS.items()}

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
    if not tickers:
        return pd.DataFrame()
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

# Kontrol Sektor
c_sec, c_rf = st.columns([3, 1])
with c_sec:
    selected_sector = st.selectbox("Pilih Sektor:", list(st.session_state.sector_stocks.keys()))
with c_rf:
    st.write("")
    st.write("")
    if st.button("🔄 Scan", use_container_width=True):
        st.cache_data.clear()

current_tickers = st.session_state.sector_stocks[selected_sector]

with st.spinner("Memindai emiten..."):
    df_data = fetch_focused_data(current_tickers)

if df_data.empty:
    st.warning("Belum ada data saham yang aktif pada daftar ini.")
else:
    st.write("### 🎯 Panel Eksekusi Kilat")
    
    # Dropdown pemilihan saham
    stock_options = [f"{r['Saham']} — {r['Badge']} (+{r['Potensi (%)']}%)" for _, r in df_data.iterrows()]
    selected_option = st.selectbox("Pilih Saham Pantauan:", options=stock_options, index=0)
    selected_code = selected_option.split(" ")[0]
    stock = df_data[df_data["Saham"] == selected_code].iloc[0]

    # Kartu HUD Eksekusi Modern & Bersih
    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; margin: 12px 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04);">
        <!-- Header: Saham & Status -->
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 12px; margin-bottom: 14px;">
            <div>
                <span style="font-size: 1.6rem; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;">{stock['Saham']}</span>
                <span style="font-size: 0.85rem; color: #64748b; margin-left: 8px;">Open: <b>Rp {stock['Open']}</b> | Last: <b>Rp {stock['Last']}</b></span>
            </div>
            <div>
                <span class="{stock['ColorTag']}" style="font-size: 0.8rem; padding: 5px 12px; border-radius: 20px;">{stock['Badge']}</span>
            </div>
        </div>

        <!-- 3 Kotak Aksi Utama (Beli, TP, Cut Loss) -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-bottom: 14px;">
            <!-- Box Zona Beli -->
            <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px; padding: 12px; text-align: center;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #0369a1; text-transform: uppercase;">🛒 Zona Beli</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #0c4a6e; margin-top: 4px;">Rp {stock['Zona Beli']}</div>
                <div style="font-size: 0.7rem; color: #0284c7;">Antre di Bid</div>
            </div>

            <!-- Box Target TP -->
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 12px; text-align: center;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #15803d; text-transform: uppercase;">🎯 Target TP (+3T)</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #14532d; margin-top: 4px;">Rp {stock['Target TP']}</div>
                <div style="font-size: 0.75rem; font-weight: 700; color: #16a34a;">+{stock['Gain %']}%</div>
            </div>

            <!-- Box Cut Loss -->
            <div style="background: #fff1f2; border: 1px solid #fecdd3; border-radius: 10px; padding: 12px; text-align: center;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #be123c; text-transform: uppercase;">🛡️ Cut Loss (-2T)</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #881337; margin-top: 4px;">Rp {stock['Cut Loss']}</div>
                <div style="font-size: 0.75rem; font-weight: 700; color: #e11d48;">{stock['Loss %']}%</div>
            </div>
        </div>

        <!-- Detail Tambahan / Footer Card -->
        <div style="background: #f8fafc; border-radius: 8px; padding: 8px 12px; display: flex; justify-content: space-between; font-size: 0.78rem; color: #475569;">
            <span>🚀 <b>TP 2 (+5T):</b> Rp {stock['TP 2']}</span>
            <span>📏 <b>Fraksi:</b> Rp {stock['Tick Size']}/tick</span>
            <span>📊 <b>Volume:</b> {stock['Volume']:,} Lot</span>
        </div>
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

# ==================== KELOLA & EDIT TABEL ====================
st.write("### 📋 Daftar Ringkas Sektor")

with st.expander("⚙️ Edit Saham Tabel (Tambah / Hapus)", expanded=False):
    col_add1, col_add2 = st.columns([3, 1])
    with col_add1:
        new_ticker = st.text_input("Tambah Saham Baru:", placeholder="Contoh: COCO, LAPD").strip().upper()
    with col_add2:
        st.write("")
        st.write("")
        if st.button("➕ Tambah", use_container_width=True):
            if new_ticker and new_ticker not in st.session_state.sector_stocks[selected_sector]:
                st.session_state.sector_stocks[selected_sector].append(new_ticker)
                st.cache_data.clear()
                st.rerun()

    # Multiselect untuk hapus saham (cukup klik silang 'x')
    updated_list = st.multiselect(
        "Saham Aktif di Tabel Ini (Klik 'x' untuk hapus):",
        options=st.session_state.sector_stocks[selected_sector],
        default=st.session_state.sector_stocks[selected_sector]
    )
    
    if updated_list != st.session_state.sector_stocks[selected_sector]:
        st.session_state.sector_stocks[selected_sector] = updated_list
        st.cache_data.clear()
        st.rerun()

    if st.button("↩️ Reset ke Bawaan"):
        st.session_state.sector_stocks[selected_sector] = list(DEFAULT_SECTORS[selected_sector])
        st.cache_data.clear()
        st.rerun()

# Menampilkan kartu saham ringkas
if not df_data.empty:
    for _, row in df_data.iterrows():
        st.markdown(f"""
        <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:10px 14px; border-radius:10px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <b style="font-size:1rem; color:#0f172a;">{row['Saham']}</b> <span style="font-size:0.8rem; color:#64748b;">(Open: Rp {row['Open']})</span><br>
                <span style="font-size:0.82rem; color:#0369a1;">Beli: <b>{row['Zona Beli']}</b> | TP: <b>{row['Target TP']}</b> | SL: <b>{row['Cut Loss']}</b></span>
            </div>
            <div style="text-align:right;">
                <span class="{row['ColorTag']}">{row['Badge']}</span><br>
                <span style="font-size:0.82rem; font-weight:700; color:#15803d;">+{row['Potensi (%)']}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(
    page_title="ScalpTick Screener", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS agar tampilan clean, font modern, dan ramah layar HP
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    .status-badge {
        padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ ScalpTick Screener")
st.caption("Peta Eksekusi Cuan 2–3 Tick Saham Indonesia")

DEFAULT_TICKERS = [
    "JKON", "BABP", "BRMS", "BUMI", "GOTO", 
    "DEWA", "ENRG", "DOID", "MEDC", "KIJA",
    "PANI", "INET", "STRK", "HUMI", "WIFI"
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

# Sidebar untuk kustomisasi saham
with st.sidebar:
    st.header("⚙️ Pengaturan")
    user_tickers = st.text_area("Watchlist:", value=", ".join(DEFAULT_TICKERS))
    tickers_list = [t.strip().upper() for t in user_tickers.split(",") if t.strip()]

# Tombol Refresh Utama
col_btn, col_blank = st.columns([1, 1])
with col_btn:
    if st.button("🔄 Refresh Data (09.02 WIB)", use_container_width=True):
        st.cache_data.clear()

@st.cache_data(ttl=300)
def fetch_screen_data(tickers):
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

                # Parameter Eksekusi Langsung
                zona_beli = f"{open_p - tick} - {open_p}"
                target_tp = open_p + (3 * tick)
                cut_loss = open_p - (2 * tick)

                # Status Kategori
                if potensi_pct >= 3.0 and rentang_tick >= 4.0:
                    status = "🟢 Prioritas"
                elif potensi_pct >= 1.5:
                    status = "🟡 Pantau"
                else:
                    status = "⚪ Lewati"

                results.append({
                    "Saham": t,
                    "Harga": last_p,
                    "Status": status,
                    "Potensi": round(potensi_pct, 1),
                    "Zona Beli": zona_beli,
                    "Target TP": target_tp,
                    "Cut Loss": cut_loss,
                    "Ruang": round(rentang_tick, 1),
                    "Raw_Potensi": potensi_pct
                })
        except Exception:
            continue

    res_df = pd.DataFrame(results)
    if not res_df.empty:
        res_df = res_df.sort_values(by="Raw_Potensi", ascending=False).reset_index(drop=True)
    return res_df

with st.spinner("Memindai radar saham..."):
    df_data = fetch_screen_data(tickers_list)

if df_data.empty:
    st.warning("Data belum tersedia. Silakan periksa koneksi atau tunggu jam bursa.")
else:
    # 1. KARTU REKOMENDASI TERATAS (FOKUS UTAMA)
    top_stock = df_data.iloc[0]
    st.subheader("🎯 Target Pilihan Pagi Ini")
    
    with st.container():
        st.markdown(f"### **{top_stock['Saham']}** &nbsp; `{top_stock['Status']}`")
        m1, m2, m3 = st.columns(3)
        m1.metric("Area Beli", f"Rp {top_stock['Zona Beli']}")
        m2.metric("Target Jual (TP)", f"Rp {top_stock['Target TP']}", delta="+3 Tick")
        m3.metric("Batas Rugi (SL)", f"Rp {top_stock['Cut Loss']}", delta="-2 Tick", delta_color="inverse")
        st.caption(f"Potensi rentang gerak: **+{top_stock['Potensi']}%** ({top_stock['Ruang']} Tick). *Wajib cek antrean Bid tebal sebelum antre!*")

    st.divider()

    # 2. TABEL RINGKAS SIAP EKSEKUSI
    st.subheader("📋 Daftar Pantauan Cepat")
    
    tabel_ringkas = df_data[["Saham", "Status", "Harga", "Zona Beli", "Target TP", "Cut Loss", "Potensi"]]

    # Pewarnaan baris elegan & soft
    def highlight_status(row):
        val = row["Potensi"]
        if val >= 3.0:
            return ['background-color: #e8f5e9; color: #1b5e20;'] * len(row)  # Hijau lembut
        elif val >= 1.5:
            return ['background-color: #fffde7; color: #f57f17;'] * len(row)  # Kuning lembut
        else:
            return ['background-color: #fafafa; color: #9e9e9e;'] * len(row)  # Abu-abu netral

    styled_table = tabel_ringkas.style.apply(highlight_status, axis=1)\
                                      .format({"Harga": "Rp {:,.0f}", "Target TP": "Rp {:,.0f}", "Cut Loss": "Rp {:,.0f}", "Potensi": "+{:.1f}%"})

    st.dataframe(
        styled_table,
        use_container_width=True,
        hide_index=True
    )

    st.info("💡 **Tips Pagi:** Jika saham teratas antrean Bid-nya tipis, langsung lirik baris berstatus **🟢 Prioritas** di bawahnya.")

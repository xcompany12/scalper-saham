import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(
    page_title="ScalpTick Live Hub", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom Styling Elegan & Responsif Mobile
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
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .badge-mid {
        background-color: #fef9c3;
        color: #854d0e;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .badge-low {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ ScalpTick Live Hub")
st.caption("Auto-Screener & Kalkulator Eksekusi Dinamis (IDX)")

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

with st.sidebar:
    st.header("⚙️ Pengaturan")
    user_tickers = st.text_area("Watchlist:", value=", ".join(DEFAULT_TICKERS))
    tickers_list = [t.strip().upper() for t in user_tickers.split(",") if t.strip()]

if st.button("🔄 Refresh Data Real-Time", use_container_width=True):
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
                low_p = int(today['Low'])
                prev_low = int(prev_day['Low'])
                vol = int(today['Volume'])

                if vol <= 0 or open_p == 0:
                    continue

                tick = get_tick_size(open_p)
                rentang_tick = ((high_p - open_p) + (open_p - prev_low)) / tick
                potensi_pct = (rentang_tick * tick / open_p) * 100

                # Parameter Eksekusi
                zona_beli = f"{open_p - tick} - {open_p}"
                target_tp1 = open_p + (3 * tick)
                target_tp2 = open_p + (5 * tick)
                cut_loss = open_p - (2 * tick)

                # Persentase Gain / Loss
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
                    "Harga": last_p,
                    "Open": open_p,
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

with st.spinner("Memindai dinamika pasar..."):
    df_data = fetch_screen_data(tickers_list)

if df_data.empty:
    st.warning("Data belum tersedia. Silakan periksa daftar ticker.")
else:
    st.write("### 📌 Pilih Saham untuk Detail Eksekusi")
    
    # Selector Pilihan Saham
    stock_options = [f"{r['Saham']} ({r['Badge']})" for _, r in df_data.iterrows()]
    selected_option = st.selectbox(
        "Sentuh untuk mengganti saham:", 
        options=stock_options,
        index=0
    )
    
    selected_code = selected_option.split(" ")[0]
    stock = df_data[df_data["Saham"] == selected_code].iloc[0]

    # Kartu Ringkas Utama
    st.markdown(f"""
    <div class="card-box">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin:0; color:#0f172a;">{stock['Saham']} <span style="font-size:1.1rem; color:#64748b;">Rp {stock['Harga']}</span></h2>
            <span class="{stock['ColorTag']}">{stock['Badge']}</span>
        </div>
        <p style="margin:6px 0 0 0; color:#475569; font-size:0.9rem;">
            Potensi Ruang Gerak: <b>+{stock['Potensi (%)']}%</b> ({stock['Ruang (Tick)']} Tick) | Vol: <b>{stock['Volume']:,} Lot</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 3 Metrik Inti (Sudah diperbaiki key-nya)
    c1, c2, c3 = st.columns(3)
    c1.metric("Zona Beli", f"Rp {stock['Zona Beli']}")
    c2.metric("Target TP (+3T)", f"Rp {stock['Target TP']}", delta=f"+{stock['Gain %']}%")
    c3.metric("Cut Loss (-2T)", f"Rp {stock['Cut Loss']}", delta=f"{stock['Loss %']}%", delta_color="inverse")

    st.caption(f"🎯 **TP 2 (Agresif / +5 Tick):** Rp {stock['TP 2']} | **Fraksi Tick:** Rp {stock['Tick Size']}")

    st.divider()

    # Tabel Ringkas Semua Saham
    st.write("### 📋 Ringkasan Semua Saham")
    
    display_cols = ["Saham", "Badge", "Harga", "Zona Beli", "Target TP", "Cut Loss", "Potensi (%)"]
    tabel_ringkas = df_data[display_cols]

    def highlight_soft(row):
        val = row["Potensi (%)"]
        if val >= 3.0:
            return ['background-color: #f0fdf4; color: #14532d; font-weight: 500;'] * len(row)
        elif val >= 1.5:
            return ['background-color: #fefce8; color: #713f12; font-weight: 500;'] * len(row)
        else:
            return ['background-color: #fafafa; color: #a1a1aa;'] * len(row)

    styled_table = tabel_ringkas.style.apply(highlight_soft, axis=1)\
                                      .format({
                                          "Harga": "Rp {:,.0f}", 
                                          "Target TP": "Rp {:,.0f}", 
                                          "Cut Loss": "Rp {:,.0f}", 
                                          "Potensi (%)": "+{:.1f}%"
                                      })

    st.dataframe(styled_table, use_container_width=True, hide_index=True)
    st.caption("💡 *Tabel otomatis diurutkan dari potensi gerak paling lebar ke paling sempit.*")

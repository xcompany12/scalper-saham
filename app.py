import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="ScalpTick Screener", layout="centered")

st.title("🔥 Top Scalping Screener (IDX)")
st.caption("Auto-Filter Saham Potensi Ruang Gerak Tick Lebar")

# Daftar Saham Watchlist (Bisa kamu tambah/kurangi sesuka hati)
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

# Sidebar untuk kustomisasi watchlist
st.sidebar.header("Pengaturan Watchlist")
user_tickers_input = st.sidebar.text_area(
    "Daftar Saham (pisahkan koma):", 
    value=", ".join(DEFAULT_TICKERS)
)
tickers_list = [t.strip().upper() for t in user_tickers_input.split(",") if t.strip()]

# Tombol Refresh Data
if st.button("🔄 Scan Pasar Sekarang"):
    st.cache_data.clear()

@st.cache_data(ttl=300) # Simpan cache 5 menit agar tidak lemot
def scan_stocks(tickers):
    results = []
    formatted_tickers = [f"{t}.JK" for t in tickers]
    
    # Download data sekaligus agar cepat
    try:
        data = yf.download(formatted_tickers, period="5d", interval="1d", group_by="ticker", threads=True)
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

                # Abaikan saham tidur / tidak ada transaksi
                if vol <= 0 or open_p == 0:
                    continue

                tick_size = get_tick_size(open_p)

                # Rumus Laba Tick Excel: ((High - Open) + (Open - Low_kemarin)) / Tick
                rentang_tick = ((high_p - open_p) + (open_p - prev_low)) / tick_size
                prov = rentang_tick - 0.5
                lb2 = prov - 2.0

                results.append({
                    "Saham": t,
                    "Harga": last_p,
                    "Open": open_p,
                    "Ruang Tick": round(rentang_tick, 1),
                    "LB 2%": round(lb2, 1),
                    "Volume (Lot)": vol // 100,
                    "High": high_p,
                    "Low": low_p,
                    "Prev Low": prev_low,
                    "Tick Size": tick_size
                })
        except Exception:
            continue

    df_res = pd.DataFrame(results)
    if not df_res.empty:
        # Urutkan dari ruang gerak tick paling lebar
        df_res = df_res.sort_values(by="Ruang Tick", ascending=False)
    return df_res

with st.spinner("Sedang memindai saham-saham aktif..."):
    df_screener = scan_stocks(tickers_list)

if df_screener.empty:
    st.warning("Belum ada data yang berhasil dimuat. Periksa koneksi atau daftar ticker.")
else:
    st.subheader("📋 Peringkat Potensi Harian")
    st.write("Saham dengan ruang tick $\ge 4$ memiliki potensi cuan paling lebar:")
    
    # Tampilkan tabel ringkas di halaman depan
    display_cols = ["Saham", "Harga", "Ruang Tick", "LB 2%", "Volume (Lot)"]
    st.dataframe(df_screener[display_cols].reset_index(drop=True), use_container_width=True)

    st.divider()

    # Pilihan Saham untuk melihat detail eksekusi
    selected_stock = st.selectbox("Pilih Saham untuk Detail Entry & SL:", df_screener["Saham"].tolist())
    
    row = df_screener[df_screener["Saham"] == selected_stock].iloc[0]
    
    entry_p = int(row["Open"])
    tick = int(row["Tick Size"])
    tp1 = entry_p + (3 * tick)
    tp2 = entry_p + (5 * tick)
    sl = entry_p - (2 * tick)
    
    loss_pct = ((sl - entry_p) / entry_p) * 100
    gain_pct = ((tp1 - entry_p) / entry_p) * 100

    st.subheader(f"🎯 Rekomendasi Eksekusi: {selected_stock}")
    st.info(f"""
    * **Zona Beli (Buy Area) :** Rp {entry_p - tick} - Rp {entry_p} *(Dekat Open / Low)*
    * **Target Profit 1 (Net ~2%) :** Rp {tp1} (+{gain_pct:.2f}%)
    * **Target Profit 2 (Net ~3%) :** Rp {tp2}
    * **Batas Cut Loss Disiplin :** Rp {sl} ({loss_pct:.2f}%)
    * **Nilai 1 Fraksi (Tick) :** Rp {tick}
    """)

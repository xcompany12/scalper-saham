import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="ScalpTick Screener", layout="centered")

st.title("📈 ScalpTick Screener")
st.caption("Kalkulator Prediksi & Rekomendasi Fraksi Tick Otomatis")

# Input Saham
ticker_input = st.text_input("Kode Saham (IDX):", value="JKON").upper().strip()
ticker_symbol = f"{ticker_input}.JK"

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

try:
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period="5d", interval="1d")

    if len(df) >= 2:
        prev_day = df.iloc[-2]
        today = df.iloc[-1]

        last_price = int(today['Close'])
        open_price = int(today['Open'])
        high_price = int(today['High'])
        low_price = int(today['Low'])
        prev_low = int(prev_day['Low'])
        volume = int(today['Volume'])

        tick_size = get_tick_size(open_price)

        # Perhitungan Rumus Laba Tick Excel
        rentang_tick = ((high_price - open_price) + (open_price - prev_low)) / tick_size
        prov_fee = rentang_tick - 0.5

        # Level Rekomendasi
        entry_price = open_price
        tp1_price = entry_price + (3 * tick_size)
        tp2_price = entry_price + (5 * tick_size)
        sl_price = entry_price - (2 * tick_size)

        loss_pct = ((sl_price - entry_price) / entry_price) * 100
        gain_tp1_pct = ((tp1_price - entry_price) / entry_price) * 100

        st.subheader(f"Ringkasan: {ticker_input}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Harga Terkini", f"Rp {last_price}")
        c2.metric("Open Hari Ini", f"Rp {open_price}")
        c3.metric("Low Kemarin", f"Rp {prev_low}")

        st.divider()

        if rentang_tick >= 4:
            st.success(f"🔥 POTENSI TINGGI: Ruang gerak {rentang_tick:.1f} Tick")
        else:
            st.warning(f"⚠️ VOLATILITAS RENDAH: Ruang gerak {rentang_tick:.1f} Tick")

        st.subheader("🎯 Rekomendasi Eksekusi")
        st.info(f"""
        * **Area Entry Beli :** Rp {entry_price - tick_size} - Rp {entry_price}
        * **Target Profit 1 (Net ~2%) :** Rp {tp1_price} (+{gain_tp1_pct:.2f}%)
        * **Target Profit 2 (Net ~3%) :** Rp {tp2_price}
        * **Batas Cut Loss :** Rp {sl_price} ({loss_pct:.2f}%)
        """)

        st.caption(f"Volume transaksi berjalan: {volume:,} lembar")
    else:
        st.error("Data saham tidak cukup untuk dianalisis.")

except Exception as e:
    st.error(f"Gagal mengambil data saham: {e}")

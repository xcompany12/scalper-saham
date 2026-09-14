import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(
    page_title="ScalpTick Full IDX", 
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

st.title("⚡ ScalpTick Full IDX Radar")
st.caption("Pusat Radar Saham IDX: Pantauan Harga Real-Time & Rencana Eksekusi")

st.markdown(f"""
<div class="time-banner">
    🕒 <b>Waktu Pindai:</b> {current_time_str} &nbsp;|&nbsp; <b>Status:</b> {market_status_badge}
</div>
""", unsafe_allow_html=True)

FULL_IDX_POOLS = {
    "Kelompok A - B (100+ Emiten)": [
        "AALI", "ABBA", "ABDA", "ABMM", "ACES", "ACST", "ADHI", "ADMF", "ADMR", "ADRO", 
        "AGAR", "AGII", "AGRO", "AGRS", "AHAP", "AIMS", "AISA", "AKKU", "AKPI", "AKRA", 
        "AKSI", "ALDO", "ALKA", "ALMI", "ALTO", "AMAR", "AMFG", "AMIN", "AMMN", "AMOR", 
        "ANDI", "ANJT", "ANTM", "APEX", "APIC", "APII", "APLI", "APLN", "ARCI", "ARGO", 
        "ARII", "ARKA", "ARMY", "ARNA", "ARTA", "ARTI", "ARTO", "ASBI", "ASDF", "ASDM", 
        "ASGR", "ASHA", "ASII", "ASJT", "ASLC", "ASMI", "ASPI", "ASRI", "ASRM", "ASSA", 
        "ATAP", "ATIC", "AUTO", "AVIA", "AWAN", "AXIO", "AYAM", "AYLS", "BABP", "BACA", 
        "BAJA", "BALI", "BANK", "BAPA", "BAPI", "BATA", "BAUT", "BBCA", "BBHI", "BBKP", 
        "BBLD", "BBMD", "BBNI", "BBRI", "BBRM", "BBSS", "BBTN", "BBYB", "BCAP", "BCIC", 
        "BCIP", "BDMN", "BEBS", "BEEF", "BEER", "BELI", "BELL", "BESS", "BEST", "BFIN"
    ],
    "Kelompok C - G (100+ Emiten)": [
        "CAMP", "CANI", "CARE", "CARS", "CASA", "CASH", "CASS", "CBMF", "CCSI", "CEKA", 
        "CENT", "CFIN", "CHEM", "CHIP", "CINT", "CITA", "CITY", "CLAY", "CLEO", "CLPI", 
        "CMNP", "CMNT", "CMPP", "CMRY", "CNKO", "CNMA", "CNTX", "COAL", "COCO", "CPIN", 
        "CPRI", "CPRO", "CRAB", "CRSN", "CSAP", "CSIS", "CSMI", "CSRA", "CTBN", "CTRA", 
        "CTTH", "CUAN", "CYBR", "DAAZ", "DADA", "DART", "DAYA", "DCII", "DEAL", "DEFI", 
        "DELTA", "DEPO", "DEWA", "DFAM", "DGIK", "DGNS", "DIGI", "DILD", "DIVA", "DKFT", 
        "DLTA", "DMAS", "DMMX", "DMND", "DNAR", "DNET", "DOID", "DOPC", "DPNS", "DPUM", 
        "DRMA", "DSFI", "DSNG", "DSSA", "DUCK", "DUTI", "DVLA", "DWGL", "DYAN", "EAST", 
        "ECII", "EDGE", "ELIT", "ELPI", "ELSA", "ELTY", "EMDE", "EMTK", "ENAK", "ENRG", 
        "ENVY", "EPMT", "ERAA", "ERTX", "ESIP", "ESSA", "ESTA", "ESTI", "ETWA", "EURO", 
        "EXCL", "FAPA", "FAST", "FASW", "FILM", "FIMP", "FIRE", "FISH", "FITT", "FLMC", 
        "FMII", "FOOD", "FORU", "FPNI", "FREN", "FWCT", "GEMS", "GGRP", "GHON", "GIAA", 
        "GJTL", "GLOB", "GLVA", "GMFI", "GMTD", "GOLD", "GOLL", "GOOD", "GOTO", "GPRA"
    ],
    "Kelompok H - M (100+ Emiten)": [
        "HADE", "HAIS", "HAJJ", "HALO", "HATM", "HDFA", "HDIT", "HDTX", "HEAL", "HELI", 
        "HERO", "HEXA", "HITS", "HKMU", "HMSP", "HOKI", "HOME", "HOMI", "HOPO", "HOTL", 
        "HRME", "HRTA", "HRUM", "HUMI", "IATA", "IBFN", "IBOS", "IBST", "ICBP", "ICON", 
        "IDEA", "IDPR", "IFII", "IFSH", "IGAR", "IIKP", "IKAI", "IKAN", "IKBI", "IMAS", 
        "IMJS", "IMPC", "INAF", "INAI", "INCF", "INCI", "INCO", "INDF", "INDO", "INDR", 
        "INDX", "INDY", "INET", "INGU", "INKP", "INNO", "INPC", "INPP", "INPS", "INRU", 
        "INTA", "INTD", "INTP", "IOTF", "IPAC", "IPCC", "IPCM", "IPPE", "IPTV", "IRRA", 
        "ISAP", "ISAT", "ISSP", "ITIC", "ITMA", "ITMG", "JARR", "JAST", "JAYA", "JECC", 
        "JGLE", "JIHD", "JKON", "JMAS", "JPFA", "JRPT", "JSMR", "JSPT", "JTPE", "KAEF", 
        "KAYU", "KBAG", "KBLI", "KBLM", "KBLV", "KDSI", "KDTN", "KEEN", "KEJU", "KIAS", 
        "KICI", "KIJA", "KINO", "KIOS", "KJEN", "KKGI", "KLAS", "KLBF", "KMDS", "KMTR", 
        "KMYA", "KOBX", "KOIN", "KOKA", "KONI", "KOPI", "KOTA", "KPAL", "KPAS", "KPIG", 
        "KRAS", "KREN", "KRYA", "KTIC", "KUAS", "LFLO", "LION", "LIVE", "LMAX", "LMAS", 
        "LMPI", "LMSH", "LOPI", "LPGI", "LPIN", "LPKR", "LPLI", "LPPF", "LPPS", "LRNA", 
        "LSIP", "LTLS", "LUCK", "LUCY", "MABA", "MAHA", "MAIN", "MAPA", "MAPB", "MAPI", 
        "MARI", "MARK", "MASA", "MAXI", "MBAP", "MBMA", "MBSS", "MBTO", "MCAS", "MCOL", 
        "MCOR", "MDIA", "MDKA", "MDKI", "MDLN", "MDRN", "MEDC", "MEGA", "MENN", "MERK", 
        "META", "MFIN", "MFMI", "MGLV", "MGNA", "MGRO", "MICE", "MIDI", "MIKA", "MIRA", 
        "MITI", "MKNT", "MKPI", "MKTR", "MLBI", "MLIA", "MLPL", "MLPT", "MMIX", "MMLP", 
        "MNCN", "MOLI", "MPIX", "MPMX", "MPOW", "MPPA", "MPRO", "MRAT", "MREI", "MSIN", 
        "MSKY", "MSTI", "MTDL", "MTEL", "MTFN", "MTLA", "MTMH", "MTPS", "MTSM", "MTWI", 
        "MUTU", "MYOH", "MYOR", "MYRX", "MYTX"
    ],
    "Kelompok N - S (100+ Emiten)": [
        "NAIK", "NANO", "NASA", "NASI", "NATO", "NBIX", "NCKL", "NDIN", "NDRF", "NEST", 
        "NETV", "NFCX", "NICE", "NICK", "NICL", "NIKL", "NINE", "NIPS", "NIRO", "NISP", 
        "NOBU", "NPGF", "NRCA", "NSSS", "NTBK", "NUSA", "NZIA", "OASA", "OBMD", "OCAP", 
        "OCDA", "OILS", "OKAS", "OLIV", "OMED", "OMRE", "OPMS", "PADA", "PADW", "PAMG", 
        "PANI", "PANR", "PANS", "PBID", "PBSA", "PCAR", "PDES", "PDPP", "PEGE", "PEHA", 
        "PEVE", "PGAS", "PGLI", "PGUN", "PICO", "PIPA", "PJAA", "PKPK", "PLAS", "PLIN", 
        "PMJS", "PMMP", "PNBN", "PNBS", "PNGO", "PNIN", "PNLF", "PNSE", "POLA", "POLI", 
        "POLL", "POLU", "POLY", "POOL", "PORT", "POWR", "PPGL", "PPRE", "PPRO", "PRAS", 
        "PRDA", "PRIM", "PSAB", "PSAT", "PSDN", "PSGO", "PSKT", "PSSI", "PTBA", "PTDU", 
        "PTIS", "PTON", "PTPW", "PTRO", "PTSN", "PTSP", "PUDP", "PURA", "PURE", "PURI", 
        "PWON", "PYFA", "PZZA", "RAAM", "RAFI", "RAJA", "RALS", "RAMA", "RANC", "RBMS", 
        "RCCC", "RDTX", "REAL", "RELF", "RELI", "RICY", "RIGS", "RIMO", "RISE", "RMKE", 
        "RMKO", "ROCK", "RODA", "ROKI", "RONY", "ROTI", "RSGK", "RUIS", "RUNS", "SAFE", 
        "SAME", "SAMF", "SAPX", "SATU", "SBAT", "SBMA", "SCCO", "SCMA", "SCNP", "SDMU", 
        "SDPC", "SDRA", "SEMA", "SGER", "SGRO", "SHID", "SHIP", "SICO", "SILO", "SIMP", 
        "SINI", "SIPD", "SKBM", "SKLT", "SKRN", "SLIS", "SMAR", "SMBR", "SMCB", "SMDM", 
        "SMDR", "SMGA", "SMGR", "SMIL", "SMKL", "SMKM", "SMMA", "SMMT", "SMRA", "SMRU", 
        "SMSM", "SNLK", "SOBI", "SOFA", "SOHO", "SONA", "SOSS", "SOTS", "SPMA", "SPTO", 
        "SRTG", "SSIA", "SSMS", "SSTM", "STAR", "STAA", "STRK", "SUGI", "SULI", "SUMI", 
        "SUNR", "SUPR", "SURE", "SWAT", "SWID"
    ],
    "Kelompok T - Z (100+ Emiten)": [
        "TALF", "TAMA", "TAMU", "TAPG", "TARA", "TAXI", "TBIG", "TBLA", "TBMS", "TCID", 
        "TCPI", "TDPM", "TEBE", "TECH", "TELE", "TFAS", "TFCO", "TGKA", "TGRA", "TIFA", 
        "TIMS", "TINS", "TIRA", "TIRT", "TKIM", "TLDN", "TLKM", "TMAS", "TMPO", "TNCA", 
        "TOBA", "TOOL", "TOPP", "TOSK", "TOTL", "TOTO", "TOWR", "TOYS", "TPMA", "TRAM", 
        "TRGU", "TRIL", "TRIM", "TRIN", "TRIS", "TRJA", "TRON", "TRST", "TRUE", "TRUK", 
        "TRUS", "TSPC", "TUGU", "TYRE", "UANG", "UCID", "UDNG", "UFOE", "ULTJ", "UNIC", 
        "UNIQ", "UNIT", "UNSP", "UNTR", "UNVR", "URBN", "UVCR", "VAST", "VICI", "VICO", 
        "VINS", "VIP", "VIVA", "VOKS", "VRNA", "WAPO", "WEGE", "WEHA", "WICO", "WIFI", 
        "WIKA", "WINS", "WIRG", "WMPP", "WMUU", "WOOD", "WOWS", "WSBP", "WTON", "YELO", 
        "YPAS", "YULE", "ZATA", "ZBRA", "ZINC", "ZONE", "ZYRX"
    ]
}

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

c_sec, c_rf = st.columns([3, 1])
with c_sec:
    selected_pool = st.selectbox("Pilih Kelompok Saham:", list(FULL_IDX_POOLS.keys()))
with c_rf:
    st.write("")
    st.write("")
    if st.button("🔄 Scan Pasar", use_container_width=True):
        st.cache_data.clear()

tickers_to_scan = FULL_IDX_POOLS[selected_pool]

@st.cache_data(ttl=60)
def fetch_full_data(tickers):
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

            # Level Eksekusi
            zona_beli = f"{open_p - tick} - {open_p}"
            target_tp1 = open_p + (3 * tick)
            cut_loss = open_p - (2 * tick)

            gain_pct = ((target_tp1 - open_p) / open_p) * 100
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
                "TP (+3T)": target_tp1,
                "Cut Loss": cut_loss,
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
    if not res_df.empty:
        res_df = res_df.sort_values(by="Potensi (%)", ascending=False).reset_index(drop=True)
    return res_df

with st.spinner(f"Memindai emiten aktif di {selected_pool}..."):
    df_data = fetch_full_data(tickers_to_scan)

if df_data.empty:
    st.warning("Belum ada data transaksi aktif di kelompok ini.")
else:
    st.write("### 📌 Detail Kartu Saham Terpilih")
    stock_options = [f"{r['Saham']} ({r['Status']}) - Potensi: +{r['Potensi (%)']}%" for _, r in df_data.iterrows()]
    selected_option = st.selectbox("Sentuh untuk ganti saham:", options=stock_options, index=0)
    selected_code = selected_option.split(" ")[0]
    stock = df_data[df_data["Saham"] == selected_code].iloc[0]

    st.markdown(f"""
    <div class="card-box">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin:0; color:#0f172a;">{stock['Saham']}</h2>
            <span class="{stock['ColorTag']}">{stock['Status']}</span>
        </div>
        <p style="margin:6px 0 0 0; color:#475569; font-size:0.88rem;">
            Status Data: <b>{stock['Data']}</b> | Volume: <b>{stock['Volume (Lot)']:,} Lot</b> | Fraksi: <b>Rp {stock['Tick Size']}/tick</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # BARIS 1: FAKTA PASAR HARI INI
    st.markdown("**1. Fakta Harga Pasar Saat Ini**")
    f1, f2, f3 = st.columns(3)
    f1.metric("Harga Open (Buka)", f"Rp {stock['Open']:,}")
    f2.metric("Harga Saat Ini (Running)", f"Rp {stock['Saat Ini']:,}", delta=f"{stock['Change %']}%")
    f3.metric("Potensi Rentang", f"+{stock['Potensi (%)']}%", delta=f"{stock['Ruang (Tick)']} Tick")

    # BARIS 2: RENCANA EKSEKUSI
    st.markdown("**2. Rencana Tindakan Order**")
    e1, e2, e3 = st.columns(3)
    e1.metric("Zona Entry (Beli)", f"Rp {stock['Entry']}")
    e2.metric("Target TP (+3T)", f"Rp {stock['TP (+3T)']:,}", delta=f"+{stock['Gain %']}%")
    e3.metric("Cut Loss (-2T)", f"Rp {stock['Cut Loss']:,}", delta=f"{stock['Loss %']}%", delta_color="inverse")

    st.divider()

    # TABEL LENGKAP
    st.write(f"### 📋 Ringkasan Emiten Aktif ({len(df_data)} Saham)")
    display_cols = ["Saham", "Status", "Open", "Saat Ini", "Entry", "TP (+3T)", "Cut Loss", "Potensi (%)"]
    tabel_ringkas = df_data[display_cols]

    styled_table = tabel_ringkas.style.apply(highlight_soft, axis=1)\
                                      .format({
                                          "Open": "Rp {:,.0f}",
                                          "Saat Ini": "Rp {:,.0f}", 
                                          "TP (+3T)": "Rp {:,.0f}", 
                                          "Cut Loss": "Rp {:,.0f}", 
                                          "Potensi (%)": "+{:.1f}%"
                                      })
    st.dataframe(styled_table, use_container_width=True, hide_index=True)

# ================================================================
# IDX SWING SCREENER — STREAMLIT WEB APP
# File: app.py
# Deskripsi: Tampilan web interaktif untuk screener IDX
#            Dijalankan via Streamlit Cloud (tidak perlu install)
# ================================================================

import streamlit as st
import pandas as pd
from datetime import datetime
from screener import run_screener, IDX_UNIVERSE, DEFAULT_PARAMS

# ================================================================
# KONFIGURASI HALAMAN
# ================================================================

st.set_page_config(
    page_title = "IDX Swing Screener",
    page_icon  = "📈",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ================================================================
# CUSTOM CSS — Tampilan profesional & bersih
# ================================================================

st.markdown("""
<style>
    /* Font & Background */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Header utama */
    .main-header {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: rgba(255,255,255,0.65);
        margin: 0.4rem 0 0 0;
        font-size: 0.9rem;
    }

    /* Badge signal */
    .badge-pullback {
        background: rgba(0,200,100,0.15);
        color: #00c864;
        border: 1px solid rgba(0,200,100,0.3);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-breakout {
        background: rgba(82,130,255,0.15);
        color: #5282ff;
        border: 1px solid rgba(82,130,255,0.3);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Card metric */
    .metric-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        text-align: center;
    }

    /* Disclaimer box */
    .disclaimer {
        background: rgba(255,200,0,0.08);
        border: 1px solid rgba(255,200,0,0.2);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        color: rgba(255,255,255,0.6);
        font-size: 0.8rem;
        margin-top: 1rem;
    }

    /* Dataframe styling override */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0d1117;
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    /* Tombol scan */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00c864, #00a050);
        border: none;
        color: white;
        font-weight: 600;
        font-size: 1rem;
        padding: 0.6rem 0;
        border-radius: 10px;
        transition: all 0.2s;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(0,200,100,0.3);
    }
</style>
""", unsafe_allow_html=True)


# ================================================================
# HEADER
# ================================================================

st.markdown("""
<div class="main-header">
    <h1>📈 IDX Swing Screener</h1>
    <p>
        Sistem screening otomatis saham IDX berbasis analisis teknikal &nbsp;·&nbsp;
        EMA Stack (21/89/200) · ADX · RSI · Volume · ATR Regime &nbsp;·&nbsp;
        Data: Yahoo Finance (delayed ~15 menit)
    </p>
</div>
""", unsafe_allow_html=True)


# ================================================================
# SIDEBAR — PANEL PARAMETER
# ================================================================

with st.sidebar:
    st.markdown("## ⚙️ Parameter Sistem")
    st.markdown("---")

    # ── EMA Settings ─────────────────────────────────────────
    st.markdown("### 📊 EMA")
    ema_s = st.number_input(
        "EMA Short (Pullback Zone)",
        value=21, min_value=5, max_value=50,
        help="EMA cepat — zona pullback entry"
    )
    ema_m = st.number_input(
        "EMA Mid (Swing Bias)",
        value=89, min_value=20, max_value=150,
        help="EMA menengah — konfirmasi bias swing"
    )
    ema_l = st.number_input(
        "EMA Long (Primary Trend)",
        value=200, min_value=100, max_value=300,
        help="EMA panjang — filter trend primer"
    )

    st.markdown("### 📈 ADX")
    adx_thresh = st.slider(
        "Minimum ADX",
        min_value=10.0, max_value=40.0,
        value=18.0, step=0.5,
        help="Semakin tinggi = filter pasar trending lebih ketat"
    )

    st.markdown("### ⚡ RSI")
    col_rsi1, col_rsi2 = st.columns(2)
    with col_rsi1:
        rsi_lo = st.number_input("RSI Min", value=38, min_value=20, max_value=50)
    with col_rsi2:
        rsi_hi = st.number_input("RSI Max", value=55, min_value=45, max_value=70)

    st.markdown("### 🛡️ Risk / ATR")
    sl_mult = st.slider(
        "SL ATR Multiplier",
        min_value=1.0, max_value=3.5,
        value=2.0, step=0.1,
        help="Semakin besar = stop loss lebih longgar"
    )
    tp1_rr = st.slider("TP1 Risk:Reward", 1.0, 3.0, 1.5, 0.1)
    tp2_rr = st.slider("TP2 Risk:Reward", 1.5, 5.0, 2.5, 0.1)

    st.markdown("### 📦 Volume")
    vol_pb = st.slider("Vol Multiplier Pullback", 1.0, 2.5, 1.2, 0.1)
    vol_bo = st.slider("Vol Multiplier Breakout", 1.0, 3.0, 1.5, 0.1)

    st.markdown("---")
    st.markdown("### 🔽 Filter Tampilan")
    filter_setup = st.multiselect(
        "Tampilkan Setup:",
        options=["A — Pullback", "B — Breakout"],
        default=["A — Pullback", "B — Breakout"],
    )
    min_adx_show = st.slider(
        "Min ADX untuk ditampilkan",
        0.0, 40.0, 0.0, 0.5
    )
    max_risk_show = st.slider(
        "Max Risk % per trade",
        0.5, 3.0, 3.0, 0.1
    )

    st.markdown("---")
    st.caption("💡 Parameter diubah → klik SCAN lagi untuk update hasil")

# ================================================================
# SUSUN PARAMS DARI SIDEBAR
# ================================================================

PARAMS = DEFAULT_PARAMS.copy()
PARAMS.update({
    "ema_short"    : int(ema_s),
    "ema_mid"      : int(ema_m),
    "ema_long"     : int(ema_l),
    "adx_thresh"   : float(adx_thresh),
    "rsi_lo"       : float(rsi_lo),
    "rsi_hi"       : float(rsi_hi),
    "sl_mult"      : float(sl_mult),
    "tp1_rr"       : float(tp1_rr),
    "tp2_rr"       : float(tp2_rr),
    "vol_pb_mult"  : float(vol_pb),
    "vol_bo_mult"  : float(vol_bo),
})


# ================================================================
# AREA UTAMA — SCAN BUTTON & STATUS
# ================================================================

col_btn, col_info1, col_info2, col_info3 = st.columns([3, 1, 1, 1])

with col_btn:
    scan_clicked = st.button(
        "🔍  SCAN IDX SEKARANG",
        type="primary",
        use_container_width=True,
    )

with col_info1:
    st.metric("Universe", f"{len(IDX_UNIVERSE)} saham")

with col_info2:
    st.metric("Timeframe", "Daily")

with col_info3:
    now = datetime.now().strftime("%H:%M WIB")
    st.metric("Waktu", now)


# ================================================================
# LOGIKA SCAN
# ================================================================

if scan_clicked:
    st.divider()

    # ── Progress Bar ─────────────────────────────────────────
    progress_bar = st.progress(0, text="Memulai scan...")
    status_txt   = st.empty()

    def on_progress(current, total, ticker):
        pct  = current / total
        name = ticker.replace(".JK", "")
        progress_bar.progress(pct, text=f"Scanning {name}... ({current}/{total})")
        status_txt.caption(f"⏳ Memproses: **{name}**")

    # ── Jalankan Screener ─────────────────────────────────────
    with st.spinner(""):
        df_all = run_screener(
            universe          = IDX_UNIVERSE,
            params            = PARAMS,
            progress_callback = on_progress,
        )

    # Bersihkan progress setelah selesai
    progress_bar.empty()
    status_txt.empty()

    # ── Waktu Selesai ─────────────────────────────────────────
    finish_time = datetime.now().strftime("%H:%M:%S WIB")

    # ================================================================
    # HASIL: TIDAK ADA SINYAL
    # ================================================================

    if df_all.empty:
        st.warning(
            "⚠️ **Tidak ada saham yang memenuhi semua kriteria saat ini.**\n\n"
            "Kemungkinan penyebab:\n"
            "- Pasar IDX sedang dalam kondisi sideways (ADX rendah)\n"
            "- Tidak ada pullback valid ke zona EMA 21–89\n"
            "- Tidak ada breakout dengan konfirmasi volume yang cukup\n\n"
            "**Saran:** Coba turunkan ADX Minimum di sidebar, atau periksa kembali besok."
        )

    # ================================================================
    # HASIL: ADA SINYAL
    # ================================================================

    else:
        # ── Apply Filter Sidebar ──────────────────────────────
        df_show = df_all.copy()

        if filter_setup:
            df_show = df_show[df_show["Setup"].isin(filter_setup)]

        df_show = df_show[df_show["ADX"] >= min_adx_show]
        df_show = df_show[df_show["Risk %"] <= max_risk_show]

        # ── Summary Cards ─────────────────────────────────────
        st.markdown(
            f"### ✅ {len(df_show)} Saham Ditemukan  "
            f"<span style='font-size:0.85rem; color:rgba(255,255,255,0.45);'>"
            f"Scan selesai: {finish_time}</span>",
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4, m5 = st.columns(5)

        n_bo  = len(df_show[df_show["Setup"] == "B — Breakout"])
        n_pb  = len(df_show[df_show["Setup"] == "A — Pullback"])
        avg_adx  = round(df_show["ADX"].mean(), 1) if len(df_show) else "-"
        avg_risk = round(df_show["Risk %"].mean(), 2) if len(df_show) else "-"

        m1.metric("Total Sinyal",    len(df_show))
        m2.metric("🔵 Breakout",     n_bo)
        m3.metric("🟢 Pullback",     n_pb)
        m4.metric("Avg ADX",         avg_adx)
        m5.metric("Avg Risk %",      f"{avg_risk}%")

        st.divider()

        # ── Tabel Utama ───────────────────────────────────────
        st.markdown("#### 📋 Ringkasan Seluruh Sinyal")

        display_cols = [
            "Ticker", "Signal", "Close",
            "ADX", "RSI", "ATR Ratio", "Vol / MA",
            "EMA Stack", "Stop Loss", "TP1 (50%)", "TP2 (30%)", "Risk %",
        ]

        # Format & Style tabel
        df_display = df_show[display_cols].copy()

        def color_signal(val):
            if "BREAKOUT" in str(val):
                return "color: #5282ff; font-weight: 600"
            elif "PULLBACK" in str(val):
                return "color: #00c864; font-weight: 600"
            return ""

        def color_risk(val):
            try:
                v = float(val)
                if v <= 1.0:   return "color: #00c864"
                elif v <= 2.0: return "color: #f5a623"
                else:          return "color: #ff5c5c"
            except:
                return ""

        def color_ema(val):
            if "Aligned" in str(val): return "color: #00c864"
            return "color: #f5a623"

        styled_df = df_display.style\
            .applymap(color_signal, subset=["Signal"])\
            .applymap(color_risk,   subset=["Risk %"])\
            .applymap(color_ema,    subset=["EMA Stack"])\
            .format({
                "Close"     : "Rp {:,.0f}",
                "Stop Loss" : "Rp {:,.0f}",
                "TP1 (50%)" : "Rp {:,.0f}",
                "TP2 (30%)" : "Rp {:,.0f}",
                "Risk %"    : "{:.2f}%",
                "ADX"       : "{:.1f}",
                "RSI"       : "{:.1f}",
                "ATR Ratio" : "{:.2f}",
                "Vol / MA"  : "{:.2f}x",
            })

        st.dataframe(
            styled_df,
            use_container_width=True,
            height=min(400, 60 + len(df_show) * 38),
        )

        st.divider()

        # ── Kartu Detail Per Saham ────────────────────────────
        st.markdown("#### 🔎 Detail Analisis & Link Chart")
        st.caption(
            "Klik nama saham untuk memperluas detail. "
            "Klik tombol TradingView untuk verifikasi chart secara manual."
        )

        for idx_row, row in df_show.iterrows():

            is_bo   = "BREAKOUT" in str(row["Signal"])
            color   = "#5282ff" if is_bo else "#00c864"
            label   = f"**{row['Ticker']}** &nbsp;|&nbsp; " \
                      f"{row['Signal']} &nbsp;|&nbsp; " \
                      f"Close: Rp {row['Close']:,.0f} &nbsp;|&nbsp; " \
                      f"Risk: {row['Risk %']}%"

            with st.expander(
                f"{row['Ticker']}  ·  {row['Signal']}  ·  "
                f"Close Rp {row['Close']:,.0f}  ·  Risk {row['Risk %']}%"
            ):
                # Baris 1: Harga
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(
                    "💰 Close",
                    f"Rp {row['Close']:,.0f}"
                )
                c2.metric(
                    "🛑 Stop Loss",
                    f"Rp {row['Stop Loss']:,.0f}",
                    delta=f"−{row['Risk %']}%",
                    delta_color="inverse"
                )
                c3.metric(
                    "🎯 TP1 (50% posisi)",
                    f"Rp {row['TP1 (50%)']:,.0f}",
                    delta=f"+{round((row['TP1 (50%)']/row['Close']-1)*100, 1)}%"
                )
                c4.metric(
                    "🎯 TP2 (30% posisi)",
                    f"Rp {row['TP2 (30%)']:,.0f}",
                    delta=f"+{round((row['TP2 (30%)']/row['Close']-1)*100, 1)}%"
                )

                st.markdown("")

                # Baris 2: Indikator
                c5, c6, c7, c8, c9 = st.columns(5)
                c5.metric("ADX",       f"{row['ADX']}")
                c6.metric("RSI",       f"{row['RSI']}")
                c7.metric("ATR Ratio", f"{row['ATR Ratio']}")
                c8.metric("Vol / MA",  f"{row['Vol / MA']}x")
                c9.metric("EMA Stack", row["EMA Stack"])

                st.markdown("")

                # Panduan eksekusi ringkas
                st.markdown(
                    f"""
                    **📋 Panduan Eksekusi (Mirae M-Stock):**
                    - **Buy Limit:** Rp {row['Close']:,.0f} (atau di bawah close sedikit)
                    - **Stop Loss (Automatic Order <=):** Rp {row['Stop Loss']:,.0f}
                    - **Take Profit TP1 (Automatic Order =>):** Rp {row['TP1 (50%)']:,.0f} → tutup 50% posisi
                    - **Take Profit TP2:** Rp {row['TP2 (30%)']:,.0f} → tutup 30% posisi
                    - **Sisa 20%:** Gunakan Trailing Stop di M-Stock
                    - **Masa berlaku Automatic Order:** Maksimal 7 hari (perbarui jika belum ter-trigger)
                    """
                )

                # Tombol TradingView
                st.link_button(
                    f"📊 Buka {row['Ticker']} di TradingView →",
                    row["TV Link"],
                    use_container_width=True,
                )

        # ── Export CSV ────────────────────────────────────────
        st.divider()
        st.markdown("#### ⬇️ Export Hasil")

        csv_data = df_show.drop(columns=["TV Link"], errors="ignore")\
                          .to_csv(index=False)\
                          .encode("utf-8")

        st.download_button(
            label     = "📥 Download Hasil sebagai CSV",
            data      = csv_data,
            file_name = f"IDX_Swing_Signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime      = "text/csv",
            use_container_width=False,
        )
        st.caption("File CSV bisa dibuka di Excel atau Google Sheets.")


# ================================================================
# SECTION: PETUNJUK SINGKAT (jika belum scan)
# ================================================================

if not scan_clicked:
    st.divider()
    st.markdown("### 📖 Cara Menggunakan")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("""
        **1️⃣ Atur Parameter (Opsional)**

        Di sidebar kiri, kamu bisa mengubah parameter seperti:
        - Threshold ADX (default: 18)
        - Band RSI untuk pullback (default: 38–55)
        - Risk:Reward TP1 dan TP2
        - Filter volume

        Biarkan default jika baru pertama kali menggunakan.
        """)

    with col_b:
        st.markdown("""
        **2️⃣ Klik SCAN IDX SEKARANG**

        Screener akan:
        - Mengambil data dari Yahoo Finance
        - Menghitung EMA, ADX, RSI, ATR, Volume
        - Mengevaluasi sinyal Pullback & Breakout
        - Menampilkan kandidat yang valid

        Proses memakan waktu 1–3 menit.
        """)

    with col_c:
        st.markdown("""
        **3️⃣ Verifikasi & Eksekusi**

        Setelah sinyal muncul:
        - Klik tombol **TradingView** untuk cek chart
        - Konfirmasi sinyal secara visual
        - Catat SL dan TP dari kartu detail
        - Masukkan order di **Mirae M-Stock** (HP)
        """)

    st.divider()

# ================================================================
# DISCLAIMER
# ================================================================

st.markdown("""
<div class="disclaimer">
    ⚠️ <strong>Disclaimer:</strong>
    Screener ini adalah alat bantu analisis teknikal pribadi, bukan rekomendasi investasi.
    Data bersumber dari Yahoo Finance dengan delay ~15 menit dan mungkin tidak selalu akurat untuk semua saham IDX.
    Selalu lakukan verifikasi mandiri sebelum mengambil keputusan trading.
    Past performance tidak menjamin hasil di masa depan.
</div>
""", unsafe_allow_html=True)

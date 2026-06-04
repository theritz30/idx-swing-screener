# ================================================================
# IDX SWING SCREENER — ENGINE UTAMA
# File: screener.py
# Deskripsi: Mengambil data dari Yahoo Finance, menghitung semua
#            indikator teknikal, dan mengevaluasi sinyal trading
#            berdasarkan sistem EMA + ADX + RSI + Volume + ATR
# ================================================================

import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ================================================================
# UNIVERSE SAHAM IDX
# Format Yahoo Finance: KODESAHAM.JK
# Mencakup LQ45 + IDX80 + beberapa saham liquid pilihan
# ================================================================

IDX_UNIVERSE = [
    # ── Perbankan ───────────────────────────────────────────────
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BRIS.JK",
    "BJBR.JK", "BNGA.JK", "BTPS.JK",

    # ── Telekomunikasi & Teknologi ──────────────────────────────
    "TLKM.JK", "EXCL.JK", "ISAT.JK", "FREN.JK",

    # ── Konsumer & Retail ───────────────────────────────────────
    "UNVR.JK", "ICBP.JK", "INDF.JK", "MYOR.JK",
    "ACES.JK", "LPPF.JK", "AMRT.JK", "SIDO.JK",

    # ── Properti & Konstruksi ───────────────────────────────────
    "BSDE.JK", "CTRA.JK", "PWON.JK", "SMRA.JK",
    "WIKA.JK", "WSKT.JK", "ADHI.JK",

    # ── Energi, Tambang & Komoditas ─────────────────────────────
    "ADRO.JK", "PTBA.JK", "INCO.JK", "ANTM.JK",
    "MDKA.JK", "HRUM.JK", "ITMG.JK", "BYAN.JK",
    "MEDC.JK", "PGAS.JK",

    # ── Infrastruktur & Utilitas ────────────────────────────────
    "JSMR.JK", "TOWR.JK", "TBIG.JK",

    # ── Otomotif & Industri ─────────────────────────────────────
    "ASII.JK", "AUTO.JK", "SMSM.JK",

    # ── Healthcare & Farmasi ────────────────────────────────────
    "KLBF.JK", "MIKA.JK", "HEAL.JK", "SIDO.JK",

    # ── Media & Entertainment ───────────────────────────────────
    "SCMA.JK", "EMTK.JK",

    # ── Semen & Material Bangunan ───────────────────────────────
    "SMGR.JK", "INTP.JK",

    # ── Agribusiness ────────────────────────────────────────────
    "AALI.JK", "SIMP.JK", "LSIP.JK",

    # ── Keuangan Non-Bank ───────────────────────────────────────
    "BBLD.JK", "WOMF.JK",

    # ── Lainnya (Liquid & Aktif) ────────────────────────────────
    "GOTO.JK", "BUKA.JK", "FILM.JK",
]

# ================================================================
# PARAMETER SISTEM TRADING
# Semua parameter bisa di-override dari sidebar Streamlit
# ================================================================

DEFAULT_PARAMS = {
    # EMA
    "ema_short"     : 21,
    "ema_mid"       : 89,
    "ema_long"      : 200,

    # ADX
    "adx_period"    : 14,
    "adx_thresh"    : 18.0,

    # RSI
    "rsi_period"    : 14,
    "rsi_lo"        : 38.0,
    "rsi_hi"        : 55.0,

    # ATR & Risk
    "atr_period"    : 14,
    "sl_mult"       : 2.0,
    "tp1_rr"        : 1.5,
    "tp2_rr"        : 2.5,

    # Volume
    "vol_ma_period" : 20,
    "vol_pb_mult"   : 1.2,
    "vol_bo_mult"   : 1.5,

    # ATR Ratio Filter
    "atr_ratio_min" : 0.7,
    "atr_ratio_max" : 2.0,

    # Data
    "lookback_days" : 420,
}


# ================================================================
# FUNGSI: AMBIL DATA OHLCV DARI YAHOO FINANCE
# ================================================================

def fetch_ohlcv(ticker: str, params: dict) -> pd.DataFrame | None:
    """
    Mengambil data harga historis dari Yahoo Finance.

    Args:
        ticker  : Kode saham format Yahoo (misal: 'BBCA.JK')
        params  : Dictionary parameter sistem

    Returns:
        DataFrame dengan kolom open/high/low/close/volume
        atau None jika gagal / data tidak cukup
    """
    try:
        end_date   = datetime.today()
        start_date = end_date - timedelta(days=params["lookback_days"])

        raw = yf.download(
            tickers      = ticker,
            start        = start_date.strftime("%Y-%m-%d"),
            end          = end_date.strftime("%Y-%m-%d"),
            interval     = "1d",
            progress     = False,
            auto_adjust  = True,
            multi_level_index = False,
        )

        # Validasi data minimum (butuh minimal 250 bar untuk EMA 200)
        if raw is None or len(raw) < 250:
            return None

        # Normalkan nama kolom ke lowercase
        raw.columns = [str(c).lower().strip() for c in raw.columns]
        raw.dropna(inplace=True)

        return raw

    except Exception:
        return None


# ================================================================
# FUNGSI: HITUNG SEMUA INDIKATOR TEKNIKAL
# ================================================================

def add_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Menambahkan semua kolom indikator ke DataFrame.

    Indikator yang dihitung:
    - EMA 21, 89, 200
    - ADX 14
    - RSI 14
    - ATR 14 + ATR Ratio
    - Volume MA 20
    - MACD (12,26,9)
    - Swing High/Low (rolling 10 bar)
    """
    p = params

    # ── EMA ──────────────────────────────────────────────────
    df["ema21"]  = ta.ema(df["close"], length=p["ema_short"])
    df["ema89"]  = ta.ema(df["close"], length=p["ema_mid"])
    df["ema200"] = ta.ema(df["close"], length=p["ema_long"])

    # ── ADX ──────────────────────────────────────────────────
    adx_df     = ta.adx(df["high"], df["low"], df["close"],
                        length=p["adx_period"])
    adx_col    = f"ADX_{p['adx_period']}"
    df["adx"]  = adx_df[adx_col] if adx_col in adx_df.columns else None

    # ── RSI ──────────────────────────────────────────────────
    df["rsi"]   = ta.rsi(df["close"], length=p["rsi_period"])

    # ── ATR + ATR Ratio ──────────────────────────────────────
    df["atr"]      = ta.atr(df["high"], df["low"], df["close"],
                            length=p["atr_period"])
    df["atr_ma"]   = df["atr"].rolling(20).mean()
    df["atr_ratio"]= df["atr"] / df["atr_ma"]

    # ── Volume MA ────────────────────────────────────────────
    df["vol_ma"]   = df["volume"].rolling(p["vol_ma_period"]).mean()

    # ── MACD ─────────────────────────────────────────────────
    macd_df        = ta.macd(df["close"], fast=12, slow=26, signal=9)
    df["macd_h"]   = macd_df["MACDh_12_26_9"] \
                     if "MACDh_12_26_9" in macd_df.columns else 0

    # ── Swing High / Low (rolling 11-bar window) ─────────────
    df["swing_hi"] = df["high"].rolling(11, center=True).max()
    df["swing_lo"] = df["low"].rolling(11, center=True).min()

    df.dropna(inplace=True)
    return df


# ================================================================
# FUNGSI: EVALUASI SINYAL UNTUK SATU SAHAM
# ================================================================

def evaluate_signal(ticker: str, params: dict) -> dict | None:
    """
    Menjalankan seluruh logika sistem untuk satu saham.

    Mengevaluasi:
    1. Market Regime (Bullish/Sideways/Bearish)
    2. Setup A — Pullback ke EMA zona
    3. Setup B — Structural Breakout
    4. Validasi Risk (max 3% per trade)
    5. Kalkulasi SL, TP1, TP2

    Returns:
        dict berisi semua data sinyal, atau None jika tidak ada sinyal
    """
    # Ambil data
    df = fetch_ohlcv(ticker, params)
    if df is None:
        return None

    # Hitung indikator
    df = add_indicators(df, params)
    if len(df) < 5:
        return None

    p        = params
    row      = df.iloc[-1]       # Candle terbaru
    row_prev = df.iloc[-2]       # Candle sebelumnya

    # ── Ekstrak nilai indikator ───────────────────────────────
    close      = float(row["close"])
    open_p     = float(row["open"])
    high_p     = float(row["high"])
    low_p      = float(row["low"])
    ema21      = float(row["ema21"])
    ema89      = float(row["ema89"])
    ema200     = float(row["ema200"])
    adx        = float(row["adx"])
    rsi        = float(row["rsi"])
    atr        = float(row["atr"])
    atr_ratio  = float(row["atr_ratio"])
    volume     = float(row["volume"])
    vol_ma     = float(row["vol_ma"])
    macd_h     = float(row["macd_h"])
    macd_h_p   = float(row_prev["macd_h"])
    swing_hi   = float(row["swing_hi"])
    swing_lo   = float(row["swing_lo"])

    # ── 1. Market Regime ─────────────────────────────────────
    bull     = (close > ema200) and (ema21 > ema89) and \
               (adx >= p["adx_thresh"]) and (close > ema21)
    sideways = not bull

    # ── 2. Volatility Regime Filter ──────────────────────────
    vol_regime_ok = p["atr_ratio_min"] <= atr_ratio <= p["atr_ratio_max"]

    # ── 3. Pullback Zone (antara EMA21 dan EMA89) ─────────────
    pb_top   = ema21
    pb_bot   = ema89 * 0.98
    in_pb    = (low_p <= pb_top) and \
               (close >= pb_bot) and \
               (close > ema200)

    # ── 4. Candlestick Confirmation ──────────────────────────
    body       = abs(close - open_p)
    rng        = high_p - low_p
    if rng > 0:
        is_bull_c = close > open_p and body >= 0.55 * rng
        is_hammer = (close > open_p) and \
                    ((open_p - low_p) >= 1.8 * body) and \
                    (body >= 0.25 * rng)
        is_engulf = is_bull_c and \
                    close > float(row_prev["open"]) and \
                    open_p < float(row_prev["close"]) and \
                    float(row_prev["close"]) < float(row_prev["open"])
    else:
        is_bull_c = is_hammer = is_engulf = False

    candle_ok = is_bull_c or is_hammer or is_engulf

    # ── 5. Setup A: Pullback ──────────────────────────────────
    rsi_ok     = p["rsi_lo"] <= rsi <= p["rsi_hi"]
    vol_pb_ok  = volume >= p["vol_pb_mult"] * vol_ma

    setup_a = (bull and in_pb and rsi_ok and
               candle_ok and vol_pb_ok and
               vol_regime_ok and not sideways)

    # ── 6. Setup B: Breakout ──────────────────────────────────
    bo_ok      = close > swing_hi * 1.005
    macd_bull  = macd_h > 0 and macd_h > macd_h_p
    atr_ok     = atr >= 0.8 * float(row["atr_ma"])
    vol_bo_ok  = volume >= p["vol_bo_mult"] * vol_ma

    setup_b = (bull and bo_ok and macd_bull and
               atr_ok and vol_bo_ok and
               vol_regime_ok and not sideways)

    # ── Tidak ada sinyal → skip ───────────────────────────────
    if not setup_a and not setup_b:
        return None

    # ── 7. Stop Loss & Take Profit ────────────────────────────
    sl_struct  = swing_lo - (0.5 * atr)
    sl_atr     = close - (p["sl_mult"] * atr)
    sl_use     = max(sl_struct, sl_atr)
    risk_pct   = (close - sl_use) / close if close > 0 else 999

    # Validasi risk: harus antara 0.2% dan 3%
    if not (0.002 < risk_pct <= 0.03):
        return None

    risk_amt = close - sl_use
    tp1      = close + (p["tp1_rr"] * risk_amt)
    tp2      = close + (p["tp2_rr"] * risk_amt)

    # ── 8. Bangun Output Dictionary ──────────────────────────
    ticker_clean = ticker.replace(".JK", "")

    # Tentukan setup mana yang aktif (prioritaskan Breakout)
    if setup_b:
        signal_type = "BREAKOUT"
        setup_name  = "B — Breakout"
        signal_icon = "🔵"
    else:
        signal_type = "PULLBACK"
        setup_name  = "A — Pullback"
        signal_icon = "🟢"

    # Tentukan EMA Stack
    ema_stack_ok = (ema21 > ema89 > ema200)

    return {
        # Identitas
        "Ticker"      : ticker_clean,
        "Signal"      : f"{signal_icon} {signal_type}",
        "Setup"       : setup_name,

        # Harga
        "Close"       : round(close, 0),
        "Stop Loss"   : round(sl_use, 0),
        "TP1 (50%)"   : round(tp1, 0),
        "TP2 (30%)"   : round(tp2, 0),

        # Indikator
        "ADX"         : round(adx, 1),
        "RSI"         : round(rsi, 1),
        "ATR Ratio"   : round(atr_ratio, 2),
        "Vol / MA"    : round(volume / vol_ma, 2),
        "EMA Stack"   : "✅ Aligned" if ema_stack_ok else "⚠️ Partial",

        # Risk metrics
        "Risk %"      : round(risk_pct * 100, 2),
        "RR TP1"      : f"1 : {p['tp1_rr']}",
        "RR TP2"      : f"1 : {p['tp2_rr']}",

        # Meta
        "TV Link"     : f"https://www.tradingview.com/chart/?symbol=IDX:{ticker_clean}",
        "Scan Time"   : datetime.now().strftime("%H:%M:%S"),

        # Flag internal (untuk filter sidebar)
        "_signal_type": signal_type,
        "_setup_ok"   : True,
    }


# ================================================================
# FUNGSI UTAMA: SCAN SELURUH UNIVERSE IDX
# ================================================================

def run_screener(
    universe          : list  = None,
    params            : dict  = None,
    progress_callback         = None,
) -> pd.DataFrame:
    """
    Memindai seluruh daftar saham dalam universe.

    Args:
        universe          : List ticker (default: IDX_UNIVERSE)
        params            : Parameter sistem (default: DEFAULT_PARAMS)
        progress_callback : Fungsi callback (current, total, ticker)

    Returns:
        DataFrame berisi semua saham dengan sinyal valid,
        diurutkan: Breakout dulu → Pullback, dalam grup by ADX desc
    """
    if universe is None:
        universe = IDX_UNIVERSE
    if params is None:
        params = DEFAULT_PARAMS.copy()

    results = []
    total   = len(universe)

    for i, ticker in enumerate(universe):
        # Panggil callback progress jika ada
        if progress_callback:
            progress_callback(i + 1, total, ticker)

        # Evaluasi sinyal
        result = evaluate_signal(ticker, params)
        if result:
            results.append(result)

    # Jika tidak ada hasil
    if not results:
        return pd.DataFrame()

    # Buat DataFrame dan sortir
    df_out = pd.DataFrame(results)
    df_out["_sort_key"] = df_out["_signal_type"].apply(
        lambda x: 0 if x == "BREAKOUT" else 1
    )
    df_out = df_out.sort_values(
        ["_sort_key", "ADX"],
        ascending=[True, False]
    )

    # Hapus kolom internal sebelum return
    df_out.drop(
        columns=["_sort_key", "_signal_type", "_setup_ok"],
        inplace=True
    )
    df_out.reset_index(drop=True, inplace=True)

    return df_out

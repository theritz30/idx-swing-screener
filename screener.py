# ================================================================
# IDX SWING SCREENER — ENGINE UTAMA
# File: screener.py
# Library: "ta" (bukan pandas-ta) — lebih stabil di Streamlit Cloud
# ================================================================

import pandas as pd
import numpy as np
import yfinance as yf
import ta
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ================================================================
# UNIVERSE SAHAM IDX
# ================================================================

IDX_UNIVERSE = [
    # Perbankan
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BRIS.JK",
    "BJBR.JK", "BNGA.JK",
    # Telekomunikasi
    "TLKM.JK", "EXCL.JK", "ISAT.JK",
    # Konsumer
    "UNVR.JK", "ICBP.JK", "INDF.JK", "MYOR.JK",
    "ACES.JK", "LPPF.JK", "AMRT.JK", "SIDO.JK",
    # Properti
    "BSDE.JK", "CTRA.JK", "PWON.JK", "SMRA.JK",
    # Konstruksi
    "WIKA.JK", "WSKT.JK", "ADHI.JK",
    # Energi & Tambang
    "ADRO.JK", "PTBA.JK", "INCO.JK", "ANTM.JK",
    "MDKA.JK", "HRUM.JK", "ITMG.JK",
    "MEDC.JK", "PGAS.JK",
    # Infrastruktur
    "JSMR.JK", "TOWR.JK", "TBIG.JK",
    # Otomotif & Industri
    "ASII.JK", "AUTO.JK", "SMSM.JK",
    # Healthcare
    "KLBF.JK", "MIKA.JK", "HEAL.JK",
    # Media
    "SCMA.JK", "EMTK.JK",
    # Semen
    "SMGR.JK", "INTP.JK",
    # Agribusiness
    "AALI.JK", "SIMP.JK", "LSIP.JK",
    # Lainnya
    "GOTO.JK", "BUKA.JK",
]

# ================================================================
# PARAMETER DEFAULT
# ================================================================

DEFAULT_PARAMS = {
    "ema_short"     : 21,
    "ema_mid"       : 89,
    "ema_long"      : 200,
    "adx_period"    : 14,
    "adx_thresh"    : 18.0,
    "rsi_period"    : 14,
    "rsi_lo"        : 38.0,
    "rsi_hi"        : 55.0,
    "atr_period"    : 14,
    "sl_mult"       : 2.0,
    "tp1_rr"        : 1.5,
    "tp2_rr"        : 2.5,
    "vol_ma_period" : 20,
    "vol_pb_mult"   : 1.2,
    "vol_bo_mult"   : 1.5,
    "atr_ratio_min" : 0.7,
    "atr_ratio_max" : 2.0,
    "lookback_days" : 420,
}


# ================================================================
# FUNGSI: AMBIL DATA DARI YAHOO FINANCE
# ================================================================

def fetch_ohlcv(ticker: str, params: dict):
    try:
        end_date   = datetime.today()
        start_date = end_date - timedelta(days=params["lookback_days"])

        raw = yf.download(
            tickers           = ticker,
            start             = start_date.strftime("%Y-%m-%d"),
            end               = end_date.strftime("%Y-%m-%d"),
            interval          = "1d",
            progress          = False,
            auto_adjust       = True,
            multi_level_index = False,
        )

        if raw is None or len(raw) < 250:
            return None

        raw.columns = [str(c).lower().strip() for c in raw.columns]
        raw.dropna(inplace=True)
        return raw

    except Exception:
        return None


# ================================================================
# FUNGSI: HITUNG INDIKATOR (menggunakan library "ta")
# ================================================================

def add_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    p = params

    close  = df["close"]
    high   = df["high"]
    low    = df["low"]
    volume = df["volume"]

    # ── EMA ──────────────────────────────────────────────────
    df["ema21"]  = ta.trend.ema_indicator(close, window=p["ema_short"])
    df["ema89"]  = ta.trend.ema_indicator(close, window=p["ema_mid"])
    df["ema200"] = ta.trend.ema_indicator(close, window=p["ema_long"])

    # ── ADX ──────────────────────────────────────────────────
    adx_ind  = ta.trend.ADXIndicator(high, low, close, window=p["adx_period"])
    df["adx"] = adx_ind.adx()

    # ── RSI ──────────────────────────────────────────────────
    df["rsi"] = ta.momentum.RSIIndicator(close, window=p["rsi_period"]).rsi()

    # ── ATR ──────────────────────────────────────────────────
    df["atr"]       = ta.volatility.AverageTrueRange(
                          high, low, close, window=p["atr_period"]
                      ).average_true_range()
    df["atr_ma"]    = df["atr"].rolling(20).mean()
    df["atr_ratio"] = df["atr"] / df["atr_ma"]

    # ── Volume MA ────────────────────────────────────────────
    df["vol_ma"] = volume.rolling(p["vol_ma_period"]).mean()

    # ── MACD ─────────────────────────────────────────────────
    macd_ind     = ta.trend.MACD(close, window_fast=12, window_slow=26, window_sign=9)
    df["macd_h"] = macd_ind.macd_diff()

    # ── Swing High / Low ─────────────────────────────────────
    df["swing_hi"] = high.rolling(11, center=True).max()
    df["swing_lo"] = low.rolling(11, center=True).min()

    df.dropna(inplace=True)
    return df


# ================================================================
# FUNGSI: EVALUASI SINYAL SATU SAHAM
# ================================================================

def evaluate_signal(ticker: str, params: dict):
    df = fetch_ohlcv(ticker, params)
    if df is None:
        return None

    df = add_indicators(df, params)
    if len(df) < 5:
        return None

    p        = params
    row      = df.iloc[-1]
    row_prev = df.iloc[-2]

    close     = float(row["close"])
    open_p    = float(row["open"])
    high_p    = float(row["high"])
    low_p     = float(row["low"])
    ema21     = float(row["ema21"])
    ema89     = float(row["ema89"])
    ema200    = float(row["ema200"])
    adx       = float(row["adx"])
    rsi       = float(row["rsi"])
    atr       = float(row["atr"])
    atr_ratio = float(row["atr_ratio"])
    volume    = float(row["volume"])
    vol_ma    = float(row["vol_ma"])
    macd_h    = float(row["macd_h"])
    macd_h_p  = float(row_prev["macd_h"])
    swing_hi  = float(row["swing_hi"])
    swing_lo  = float(row["swing_lo"])

    # ── 1. Market Regime ─────────────────────────────────────
    bull = (close > ema200) and (ema21 > ema89) and \
           (adx >= p["adx_thresh"]) and (close > ema21)

    if not bull:
        return None

    # ── 2. Volatility Filter ──────────────────────────────────
    vol_regime_ok = p["atr_ratio_min"] <= atr_ratio <= p["atr_ratio_max"]
    if not vol_regime_ok:
        return None

    # ── 3. Pullback Zone ──────────────────────────────────────
    pb_top = ema21
    pb_bot = ema89 * 0.98
    in_pb  = (low_p <= pb_top) and (close >= pb_bot) and (close > ema200)

    # ── 4. Candlestick ────────────────────────────────────────
    body  = abs(close - open_p)
    rng   = high_p - low_p
    if rng > 0:
        is_bull_c = close > open_p and body >= 0.55 * rng
        is_hammer = (close > open_p) and \
                    ((open_p - low_p) >= 1.8 * body) and \
                    (body >= 0.25 * rng)
    else:
        is_bull_c = is_hammer = False
    candle_ok = is_bull_c or is_hammer

    # ── 5. Setup A: Pullback ──────────────────────────────────
    rsi_ok    = p["rsi_lo"] <= rsi <= p["rsi_hi"]
    vol_pb_ok = volume >= p["vol_pb_mult"] * vol_ma
    setup_a   = in_pb and rsi_ok and candle_ok and vol_pb_ok

    # ── 6. Setup B: Breakout ──────────────────────────────────
    bo_ok     = close > swing_hi * 1.005
    macd_bull = macd_h > 0 and macd_h > macd_h_p
    atr_ok    = atr >= 0.8 * float(row["atr_ma"])
    vol_bo_ok = volume >= p["vol_bo_mult"] * vol_ma
    setup_b   = bo_ok and macd_bull and atr_ok and vol_bo_ok

    if not setup_a and not setup_b:
        return None

    # ── 7. SL / TP ────────────────────────────────────────────
    sl_struct = swing_lo - (0.5 * atr)
    sl_atr    = close - (p["sl_mult"] * atr)
    sl_use    = max(sl_struct, sl_atr)
    risk_pct  = (close - sl_use) / close if close > 0 else 999

    if not (0.002 < risk_pct <= 0.03):
        return None

    risk_amt = close - sl_use
    tp1      = close + (p["tp1_rr"] * risk_amt)
    tp2      = close + (p["tp2_rr"] * risk_amt)

    ticker_clean    = ticker.replace(".JK", "")
    ema_stack_ok    = (ema21 > ema89 > ema200)

    if setup_b:
        signal_type = "BREAKOUT"
        setup_name  = "B — Breakout"
        signal_icon = "🔵"
    else:
        signal_type = "PULLBACK"
        setup_name  = "A — Pullback"
        signal_icon = "🟢"

    return {
        "Ticker"      : ticker_clean,
        "Signal"      : f"{signal_icon} {signal_type}",
        "Setup"       : setup_name,
        "Close"       : round(close, 0),
        "Stop Loss"   : round(sl_use, 0),
        "TP1 (50%)"   : round(tp1, 0),
        "TP2 (30%)"   : round(tp2, 0),
        "ADX"         : round(adx, 1),
        "RSI"         : round(rsi, 1),
        "ATR Ratio"   : round(atr_ratio, 2),
        "Vol / MA"    : round(volume / vol_ma, 2),
        "EMA Stack"   : "✅ Aligned" if ema_stack_ok else "⚠️ Partial",
        "Risk %"      : round(risk_pct * 100, 2),
        "RR TP1"      : f"1 : {p['tp1_rr']}",
        "RR TP2"      : f"1 : {p['tp2_rr']}",
        "TV Link"     : f"https://www.tradingview.com/chart/?symbol=IDX:{ticker_clean}",
        "Scan Time"   : datetime.now().strftime("%H:%M:%S"),
        "_signal_type": signal_type,
    }


# ================================================================
# FUNGSI UTAMA: SCAN SELURUH UNIVERSE
# ================================================================

def run_screener(universe=None, params=None, progress_callback=None):
    if universe is None:
        universe = IDX_UNIVERSE
    if params is None:
        params = DEFAULT_PARAMS.copy()

    results = []
    total   = len(universe)

    for i, ticker in enumerate(universe):
        if progress_callback:
            progress_callback(i + 1, total, ticker)
        result = evaluate_signal(ticker, params)
        if result:
            results.append(result)

    if not results:
        return pd.DataFrame()

    df_out = pd.DataFrame(results)
    df_out["_sort"] = df_out["_signal_type"].apply(
        lambda x: 0 if x == "BREAKOUT" else 1
    )
    df_out = df_out.sort_values(["_sort", "ADX"], ascending=[True, False])
    df_out.drop(columns=["_sort", "_signal_type"], inplace=True)
    df_out.reset_index(drop=True, inplace=True)
    return df_out

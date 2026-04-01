# app/services/stock_service.py
import asyncio
from pandas_datareader import data as pdr
from datetime import datetime, timedelta
from app.services.base_service import BaseService
from app.models.stock import Stock
import pandas as pd
import numpy as np
import math
import logging
from typing import Any
from app.repositories.stock_repository import StockRepository

try:
    import yfinance as yf
except Exception:  # pragma: no cover - optional dependency fallback
    yf = None

try:
    import pandas_ta as ta
except Exception:  # pragma: no cover - optional fallback for constrained envs
    ta = None

logger = logging.getLogger(__name__)

class StockService(BaseService):
    def __init__(self, repository: StockRepository):
        self.repository = repository

    @staticmethod
    def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()

        cleaned = df.copy()

        # yfinance may return MultiIndex columns like ("Open", "MSFT").
        if isinstance(cleaned.columns, pd.MultiIndex):
            cleaned.columns = [str(col[0]) for col in cleaned.columns]

        # Normalize lowercase provider columns.
        rename_map = {
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
        cleaned = cleaned.rename(columns=rename_map)

        expected = ["Open", "High", "Low", "Close", "Volume"]
        missing = [col for col in expected if col not in cleaned.columns]
        if missing:
            return pd.DataFrame()

        cleaned = cleaned.dropna(subset=expected)
        if cleaned.empty:
            return pd.DataFrame()

        cleaned = cleaned.sort_index(ascending=True)
        return cleaned

    def _fetch_market_data_sync(self, symbol: str, start_date: datetime) -> pd.DataFrame:
        upper = symbol.upper()
        stooq_candidates = [upper]
        if "." not in upper:
            stooq_candidates.insert(0, f"{upper}.US")

        errors: list[str] = []

        # Provider 1: pandas-datareader + Stooq (try with and without market suffix)
        for candidate in stooq_candidates:
            try:
                df = pdr.get_data_stooq(candidate, start=start_date)
                normalized = self._normalize_ohlcv(df)
                if not normalized.empty:
                    return normalized
            except Exception as e:  # pragma: no cover - external provider failures
                errors.append(f"stooq[{candidate}]: {e}")

        # Provider 2: yfinance fallback when Stooq blocks or returns no data
        if yf is not None:
            yf_symbol = upper.split(".")[0]
            try:
                df = yf.download(yf_symbol, start=start_date.date(), progress=False, auto_adjust=False)
                normalized = self._normalize_ohlcv(df)
                if not normalized.empty:
                    return normalized
            except Exception as e:  # pragma: no cover - external provider failures
                errors.append(f"yfinance[{yf_symbol}]: {e}")

        logger.error("All market data providers failed for %s: %s", symbol, " | ".join(errors) or "no data")
        return pd.DataFrame()

    async def _fetch_market_data(self, symbol: str, start_date: datetime) -> pd.DataFrame:
        return await asyncio.to_thread(self._fetch_market_data_sync, symbol, start_date)
    
    async def fetch_and_update_stock(self, symbol: str):
        start_date = datetime.now() - timedelta(days=10)
        df = await self._fetch_market_data(symbol, start_date)
        
        if df.empty:
            raise ValueError(f"Stock data not found for {symbol}")
        
        latest_data = df.iloc[-1]
        current_price = float(latest_data['Close'])
        
        data = {
            "symbol": symbol.upper(),
            "company_name": symbol.upper(),
            "price": current_price,
            "currency": "USD"
        }

        # Update DB using the Async Repository
        stock = await self.repository.get_by_symbol(symbol)
        
        if stock:
            return await self.repository.update(stock, data)
        else:
            stock = Stock(**data)
            return await self.repository.create(stock)

    async def get_history(self, symbol: str, days: int = 100):
        """
        Fetches OHLCV data from Stooq (Live Data).
        Returns a list of dictionaries suitable for the Frontend Chart.
        """
        start_date = datetime.now() - timedelta(days=days)
        
        df = await self._fetch_market_data(symbol, start_date)
        if df.empty:
            raise ValueError(f"No historical data for {symbol}")
        
        history = []
        for date, row in df.iterrows():
            history.append({
                "time": date.strftime('%Y-%m-%d'),
                "open": row['Open'],
                "high": row['High'],
                "low": row['Low'],
                "close": row['Close'],
                "volume": int(row['Volume'])
            })
            
        return history

    @staticmethod
    def _safe_number(value: Any, digits: int = 4) -> float | None:
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(numeric) or math.isinf(numeric):
            return None
        return round(numeric, digits)

    @staticmethod
    def _parabolic_sar(high: pd.Series, low: pd.Series, step: float = 0.02, max_step: float = 0.2) -> pd.Series:
        sar = pd.Series(index=high.index, dtype=float)
        if len(high) < 2:
            return sar

        trend_up = True
        af = step
        ep = high.iloc[0]
        sar.iloc[0] = low.iloc[0]

        for i in range(1, len(high)):
            prev_sar = sar.iloc[i - 1]
            next_sar = prev_sar + af * (ep - prev_sar)

            if trend_up:
                next_sar = min(next_sar, low.iloc[i - 1])
                if i > 1:
                    next_sar = min(next_sar, low.iloc[i - 2])
                if low.iloc[i] < next_sar:
                    trend_up = False
                    next_sar = ep
                    ep = low.iloc[i]
                    af = step
                else:
                    if high.iloc[i] > ep:
                        ep = high.iloc[i]
                        af = min(af + step, max_step)
            else:
                next_sar = max(next_sar, high.iloc[i - 1])
                if i > 1:
                    next_sar = max(next_sar, high.iloc[i - 2])
                if high.iloc[i] > next_sar:
                    trend_up = True
                    next_sar = ep
                    ep = high.iloc[i]
                    af = step
                else:
                    if low.iloc[i] < ep:
                        ep = low.iloc[i]
                        af = min(af + step, max_step)

            sar.iloc[i] = next_sar

        return sar

    async def get_indicator_suite(self, symbol: str, days: int = 365) -> dict[str, Any]:
        history = await self.get_history(symbol, days=max(days, 320))
        if not history or len(history) < 60:
            raise ValueError(f"Not enough historical data for indicator suite: {symbol}")

        df = pd.DataFrame(history)
        df["time"] = pd.to_datetime(df["time"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna().reset_index(drop=True)

        if len(df) < 60:
            raise ValueError(f"Insufficient clean data for indicators: {symbol}")

        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # Trend indicators (pandas-ta preferred, pandas fallback)
        if ta is not None:
            sma20 = ta.sma(close, length=20)
            sma50 = ta.sma(close, length=50)
            sma200 = ta.sma(close, length=200)
            ema12 = ta.ema(close, length=12)
            ema20 = ta.ema(close, length=20)
            ema26 = ta.ema(close, length=26)
            macd_df = ta.macd(close, fast=12, slow=26, signal=9)
            if macd_df is not None and not macd_df.empty:
                macd = macd_df.get("MACD_12_26_9")
                macd_signal = macd_df.get("MACDs_12_26_9")
            else:
                macd = ema12 - ema26
                macd_signal = macd.ewm(span=9, adjust=False).mean()
            rsi14 = ta.rsi(close, length=14)
        else:
            sma20 = close.rolling(20).mean()
            sma50 = close.rolling(50).mean()
            sma200 = close.rolling(200).mean()
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema20 = close.ewm(span=20, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            macd_signal = macd.ewm(span=9, adjust=False).mean()
            delta = close.diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, np.nan)
            rs = gain / loss
            rsi14 = 100 - (100 / (1 + rs))
        macd_hist = macd - macd_signal

        sar = self._parabolic_sar(high, low)

        up_move = high.diff()
        down_move = -low.diff()
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        tr = pd.concat(
            [
                high - low,
                (high - close.shift(1)).abs(),
                (low - close.shift(1)).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr14 = tr.ewm(alpha=1 / 14, adjust=False).mean()

        plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1 / 14, adjust=False).mean() / atr14
        minus_di = 100 * pd.Series(minus_dm).ewm(alpha=1 / 14, adjust=False).mean() / atr14
        dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
        adx14 = dx.ewm(alpha=1 / 14, adjust=False).mean()

        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        chikou = close.shift(-26)

        # Momentum indicators

        low14 = low.rolling(14).min()
        high14 = high.rolling(14).max()
        stoch_k = ((close - low14) / (high14 - low14).replace(0, np.nan)) * 100
        stoch_d = stoch_k.rolling(3).mean()

        williams_r = ((high14 - close) / (high14 - low14).replace(0, np.nan)) * -100

        typical_price = (high + low + close) / 3
        tp_sma20 = typical_price.rolling(20).mean()
        mad20 = typical_price.rolling(20).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
        cci20 = (typical_price - tp_sma20) / (0.015 * mad20.replace(0, np.nan))

        roc12 = close.pct_change(12) * 100

        raw_money_flow = typical_price * volume
        pos_flow = raw_money_flow.where(typical_price > typical_price.shift(1), 0.0)
        neg_flow = raw_money_flow.where(typical_price < typical_price.shift(1), 0.0)
        mfi_ratio = pos_flow.rolling(14).sum() / neg_flow.rolling(14).sum().replace(0, np.nan)
        mfi14 = 100 - (100 / (1 + mfi_ratio))

        # Volatility indicators
        std20 = close.rolling(20).std()
        bb_upper = sma20 + (2 * std20)
        bb_lower = sma20 - (2 * std20)
        bb_bandwidth = ((bb_upper - bb_lower) / sma20.replace(0, np.nan)) * 100

        keltner_upper = ema20 + (2 * atr14)
        keltner_lower = ema20 - (2 * atr14)

        donchian_upper = high.rolling(20).max()
        donchian_lower = low.rolling(20).min()

        log_returns = np.log(close / close.shift(1))
        hist_vol_21 = log_returns.rolling(21).std() * np.sqrt(252) * 100

        # Volume indicators
        obv = (np.sign(close.diff()).fillna(0) * volume).cumsum()
        vwap = (typical_price * volume).cumsum() / volume.cumsum().replace(0, np.nan)

        adl = (((close - low) - (high - close)) / (high - low).replace(0, np.nan)) * volume
        cmf21 = adl.rolling(21).sum() / volume.rolling(21).sum().replace(0, np.nan)
        vol_roc = volume.pct_change(12) * 100

        volume_bins = pd.cut(close, bins=8)
        volume_profile = (
            df.assign(volume_bin=volume_bins)
            .groupby("volume_bin", observed=False)["volume"]
            .sum()
            .dropna()
        )

        # Market structure
        prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
        prev_high, prev_low, prev_close = prev["high"], prev["low"], prev["close"]
        range_hl = prev_high - prev_low

        pp = (prev_high + prev_low + prev_close) / 3
        pivot_classic = {
            "pp": self._safe_number(pp),
            "r1": self._safe_number((2 * pp) - prev_low),
            "s1": self._safe_number((2 * pp) - prev_high),
            "r2": self._safe_number(pp + range_hl),
            "s2": self._safe_number(pp - range_hl),
        }

        pivot_fib = {
            "pp": self._safe_number(pp),
            "r1": self._safe_number(pp + (0.382 * range_hl)),
            "r2": self._safe_number(pp + (0.618 * range_hl)),
            "r3": self._safe_number(pp + (1.0 * range_hl)),
            "s1": self._safe_number(pp - (0.382 * range_hl)),
            "s2": self._safe_number(pp - (0.618 * range_hl)),
            "s3": self._safe_number(pp - (1.0 * range_hl)),
        }

        pivot_camarilla = {
            "r1": self._safe_number(prev_close + (range_hl * 1.1 / 12)),
            "r2": self._safe_number(prev_close + (range_hl * 1.1 / 6)),
            "r3": self._safe_number(prev_close + (range_hl * 1.1 / 4)),
            "r4": self._safe_number(prev_close + (range_hl * 1.1 / 2)),
            "s1": self._safe_number(prev_close - (range_hl * 1.1 / 12)),
            "s2": self._safe_number(prev_close - (range_hl * 1.1 / 6)),
            "s3": self._safe_number(prev_close - (range_hl * 1.1 / 4)),
            "s4": self._safe_number(prev_close - (range_hl * 1.1 / 2)),
        }

        woodie_pp = (prev_high + prev_low + (2 * prev_close)) / 4
        pivot_woodie = {
            "pp": self._safe_number(woodie_pp),
            "r1": self._safe_number((2 * woodie_pp) - prev_low),
            "s1": self._safe_number((2 * woodie_pp) - prev_high),
            "r2": self._safe_number(woodie_pp + range_hl),
            "s2": self._safe_number(woodie_pp - range_hl),
        }

        swing_high = high.tail(120).max()
        swing_low = low.tail(120).min()
        fib_range = swing_high - swing_low
        fib_retracement = {
            "0.0": self._safe_number(swing_high),
            "23.6": self._safe_number(swing_high - 0.236 * fib_range),
            "38.2": self._safe_number(swing_high - 0.382 * fib_range),
            "50.0": self._safe_number(swing_high - 0.5 * fib_range),
            "61.8": self._safe_number(swing_high - 0.618 * fib_range),
            "78.6": self._safe_number(swing_high - 0.786 * fib_range),
            "100.0": self._safe_number(swing_low),
        }

        pivot_points = {
            "classic": pivot_classic,
            "fibonacci": pivot_fib,
            "camarilla": pivot_camarilla,
            "woodie": pivot_woodie,
        }

        # Advanced analytics
        returns = close.pct_change().dropna()
        sharpe_ratio = None
        sortino_ratio = None
        max_drawdown = None
        if not returns.empty:
            daily_mean = returns.mean()
            daily_std = returns.std()
            downside_std = returns[returns < 0].std()
            if daily_std and daily_std > 0:
                sharpe_ratio = (daily_mean / daily_std) * math.sqrt(252)
            if downside_std and downside_std > 0:
                sortino_ratio = (daily_mean / downside_std) * math.sqrt(252)

            cumulative = (1 + returns).cumprod()
            peak = cumulative.cummax()
            dd = (cumulative - peak) / peak
            max_drawdown = dd.min()

        # Heuristic market regime: proxy for roadmap HMM state output
        latest_close = close.iloc[-1]
        latest_ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
        latest_vol = hist_vol_21.iloc[-1] if not hist_vol_21.empty else np.nan
        market_regime = "BULL"
        if latest_close < latest_ema50:
            market_regime = "BEAR"
        if pd.notna(latest_vol) and latest_vol > 35:
            market_regime = f"{market_regime}_HIGH_VOL"

        # Elliott wave heuristic: count alternating local pivots in recent window
        recent = close.tail(90).reset_index(drop=True)
        pivot_indices = []
        for i in range(2, len(recent) - 2):
            is_peak = recent.iloc[i] > recent.iloc[i - 2 : i].max() and recent.iloc[i] > recent.iloc[i + 1 : i + 3].max()
            is_trough = recent.iloc[i] < recent.iloc[i - 2 : i].min() and recent.iloc[i] < recent.iloc[i + 1 : i + 3].min()
            if is_peak or is_trough:
                pivot_indices.append(i)
        elliott_wave_phase = "UNDEFINED"
        if len(pivot_indices) >= 8:
            elliott_wave_phase = "IMPULSE_LIKELY"
        elif len(pivot_indices) >= 5:
            elliott_wave_phase = "CORRECTIVE_LIKELY"

        # Correlation matrix + beta vs SPY
        peers = ["SPY", "QQQ", "DIA", "IWM"]
        peer_symbols = [symbol.upper()] + [p for p in peers if p != symbol.upper()]
        peer_histories = await asyncio.gather(
            *[self.get_history(sym, days=130) for sym in peer_symbols],
            return_exceptions=True,
        )

        returns_frame = pd.DataFrame()
        for sym, hist_result in zip(peer_symbols, peer_histories):
            if isinstance(hist_result, Exception) or not hist_result:
                continue
            peer_df = pd.DataFrame(hist_result)
            peer_df["time"] = pd.to_datetime(peer_df["time"])
            peer_df = peer_df.sort_values("time")
            series = pd.to_numeric(peer_df["close"], errors="coerce")
            peer_returns = series.pct_change()
            peer_returns.index = peer_df["time"]
            peer_returns.name = sym

            if returns_frame.empty:
                returns_frame = peer_returns.to_frame()
            else:
                returns_frame = returns_frame.join(peer_returns, how="outer")

        if not returns_frame.empty:
            returns_frame = returns_frame.loc[:, ~returns_frame.columns.duplicated()]
            returns_frame = returns_frame.dropna(how="all")
        corr_matrix = returns_frame.corr().round(4) if not returns_frame.empty else pd.DataFrame()

        beta_vs_spy = None
        if symbol.upper() in returns_frame.columns and "SPY" in returns_frame.columns:
            temp = returns_frame[[symbol.upper(), "SPY"]].dropna()
            if len(temp) > 10 and temp["SPY"].var() > 0:
                beta_vs_spy = temp[symbol.upper()].cov(temp["SPY"]) / temp["SPY"].var()

        result = {
            "symbol": symbol.upper(),
            "as_of": df["time"].iloc[-1].strftime("%Y-%m-%d"),
            "timeframe_days": days,
            "trend": {
                "close": self._safe_number(latest_close),
                "sma_20": self._safe_number(sma20.iloc[-1]),
                "sma_50": self._safe_number(sma50.iloc[-1]),
                "sma_200": self._safe_number(sma200.iloc[-1]),
                "ema_12": self._safe_number(ema12.iloc[-1]),
                "ema_26": self._safe_number(ema26.iloc[-1]),
                "macd": self._safe_number(macd.iloc[-1]),
                "macd_signal": self._safe_number(macd_signal.iloc[-1]),
                "macd_histogram": self._safe_number(macd_hist.iloc[-1]),
                "parabolic_sar": self._safe_number(sar.iloc[-1]),
                "adx_14": self._safe_number(adx14.iloc[-1]),
                "+di_14": self._safe_number(plus_di.iloc[-1]),
                "-di_14": self._safe_number(minus_di.iloc[-1]),
                "ichimoku": {
                    "tenkan": self._safe_number(tenkan.iloc[-1]),
                    "kijun": self._safe_number(kijun.iloc[-1]),
                    "senkou_a": self._safe_number(senkou_a.dropna().iloc[-1] if not senkou_a.dropna().empty else None),
                    "senkou_b": self._safe_number(senkou_b.dropna().iloc[-1] if not senkou_b.dropna().empty else None),
                    "chikou": self._safe_number(chikou.dropna().iloc[-1] if not chikou.dropna().empty else None),
                },
            },
            "momentum": {
                "rsi_14": self._safe_number(rsi14.iloc[-1]),
                "stochastic_k_14": self._safe_number(stoch_k.iloc[-1]),
                "stochastic_d_3": self._safe_number(stoch_d.iloc[-1]),
                "williams_r_14": self._safe_number(williams_r.iloc[-1]),
                "cci_20": self._safe_number(cci20.iloc[-1]),
                "roc_12": self._safe_number(roc12.iloc[-1]),
                "mfi_14": self._safe_number(mfi14.iloc[-1]),
            },
            "volatility": {
                "bollinger_upper": self._safe_number(bb_upper.iloc[-1]),
                "bollinger_middle": self._safe_number(sma20.iloc[-1]),
                "bollinger_lower": self._safe_number(bb_lower.iloc[-1]),
                "bollinger_bandwidth": self._safe_number(bb_bandwidth.iloc[-1]),
                "atr_14": self._safe_number(atr14.iloc[-1]),
                "keltner_upper": self._safe_number(keltner_upper.iloc[-1]),
                "keltner_middle": self._safe_number(ema20.iloc[-1]),
                "keltner_lower": self._safe_number(keltner_lower.iloc[-1]),
                "donchian_upper_20": self._safe_number(donchian_upper.iloc[-1]),
                "donchian_lower_20": self._safe_number(donchian_lower.iloc[-1]),
                "historical_volatility_21d": self._safe_number(hist_vol_21.iloc[-1]),
            },
            "volume": {
                "obv": self._safe_number(obv.iloc[-1]),
                "vwap": self._safe_number(vwap.iloc[-1]),
                "chaikin_money_flow_21": self._safe_number(cmf21.iloc[-1]),
                "volume_roc_12": self._safe_number(vol_roc.iloc[-1]),
                "volume_profile": {str(k): self._safe_number(v) for k, v in volume_profile.to_dict().items()},
            },
            "market_structure": {
                "pivot_points": pivot_points,
                "fibonacci_retracement": fib_retracement,
                "elliott_wave_heuristic": {
                    "pivot_count_90": len(pivot_indices),
                    "phase": elliott_wave_phase,
                },
            },
            "advanced": {
                "market_regime": market_regime,
                "correlation_matrix_30d": corr_matrix.to_dict() if not corr_matrix.empty else {},
                "beta_vs_spy": self._safe_number(beta_vs_spy),
                "sharpe_ratio": self._safe_number(sharpe_ratio),
                "sortino_ratio": self._safe_number(sortino_ratio),
                "max_drawdown": self._safe_number(max_drawdown),
            },
        }

        return result

    async def get_technical_analysis(self, symbol: str):
        """
        Calculates RSI, MACD, and SMA using pure Pandas.
        """
        try:
            suite = await self.get_indicator_suite(symbol, days=180)
            momentum_data = suite.get("momentum", {})
            trend_data = suite.get("trend", {})
            close_price = trend_data.get("close") or 0

            rsi_val = momentum_data.get("rsi_14") or 50
            macd_val = trend_data.get("macd") or 0
            signal_val = trend_data.get("macd_signal") or 0
            sma_val = trend_data.get("sma_50") or close_price

            rsi_status = "NEUTRAL"
            if rsi_val > 70:
                rsi_status = "OVERBOUGHT"
            elif rsi_val < 30:
                rsi_status = "OVERSOLD"

            trend = "BULLISH" if close_price > sma_val else "BEARISH"
            momentum = "POSITIVE" if macd_val > signal_val else "NEGATIVE"

            return {
                "symbol": symbol,
                "price": round(close_price, 2) if close_price else 0,
                "rsi": round(rsi_val, 2),
                "rsi_signal": rsi_status,
                "trend": trend,
                "momentum": momentum,
                "narrative": (
                    f"The stock {symbol} is trading at ${round(close_price, 2)}. "
                    f"Trend is {trend}. RSI is {round(rsi_val, 1)} ({rsi_status})."
                )
            }
        except Exception as e:
            logger.error(f"Technical Analysis Failed: {e}")
            return None
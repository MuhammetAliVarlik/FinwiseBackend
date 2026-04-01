from __future__ import annotations

from typing import Final

CANONICAL_LABELS: Final[set[str]] = {"BULLISH", "BEARISH", "NEUTRAL"}
UNKNOWN_LABEL: Final[str] = "UNKNOWN"

# Canonical directional labels to stable symbolic output tokens.
SIGNAL_TO_TOKEN: Final[dict[str, str]] = {
    "BULLISH": "P_SURGE_V_HIGH",
    "BEARISH": "P_CRASH_V_HIGH",
    "NEUTRAL": "P_STABLE_V_MID",
}

# Explicit aliases accepted from legacy/model outputs.
ALIAS_TO_LABEL: Final[dict[str, str]] = {
    "BULL": "BULLISH",
    "BULLISH": "BULLISH",
    "BUY": "BULLISH",
    "BEAR": "BEARISH",
    "BEARISH": "BEARISH",
    "SELL": "BEARISH",
    "NEUTRAL": "NEUTRAL",
    "HOLD": "NEUTRAL",
    # Token-style aliases from older runs
    "P_SURGE": "BULLISH",
    "P_HIGH": "BULLISH",
    "P_CRASH": "BEARISH",
    "P_LOW": "BEARISH",
    "P_STABLE": "NEUTRAL",
    "P_MID": "NEUTRAL",
}


def _label_from_price_bin(price_bin: int, n_quantiles: int) -> str:
    """Map quantile price bin into canonical direction label."""
    if n_quantiles < 2:
        return UNKNOWN_LABEL

    bearish_max = max(0, (n_quantiles // 3) - 1)
    bullish_min = n_quantiles - (n_quantiles // 3)

    if price_bin <= bearish_max:
        return "BEARISH"
    if price_bin >= bullish_min:
        return "BULLISH"
    return "NEUTRAL"


def normalize_direction_label(value: str | None) -> str:
    """Normalize directional labels and known aliases into canonical labels.
    
    Handles:
    - Simple aliases: BULL, BEARISH, HOLD, etc.
    - Price-side tokens (P_CRASH, P_SURGE, P_STABLE, etc.)
    - Composite tokens with volume descriptors: P_CRASH_V_HIGH, P_SURGE_V_MID, etc.
    
    Price-side tokens take precedence over volume descriptors to ensure correct mapping.
    """
    if not value:
        return UNKNOWN_LABEL

    raw = str(value).strip().upper()
    
    # Exact alias match (handles BUY, SELL, HOLD, etc. and single-word price tokens)
    if raw in ALIAS_TO_LABEL:
        return ALIAS_TO_LABEL[raw]

    # Check for price-side token prefixes with priority: bearish > neutral > bullish
    # This ensures P_CRASH_V_HIGH maps to BEARISH (not BULLISH from V_HIGH)
    if "P_CRASH" in raw or "P_LOW" in raw:
        return "BEARISH"
    if "P_STABLE" in raw or "P_MID" in raw:
        return "NEUTRAL"
    if "P_SURGE" in raw or "P_HIGH" in raw:
        return "BULLISH"

    # Fallback: Check for non-prefixed directional keywords (backward compat)
    if "SURGE" in raw or "CRASH" in raw:
        return "BEARISH" if "CRASH" in raw else "BULLISH"
    if "HIGH" in raw or "LOW" in raw:
        return "BEARISH" if "LOW" in raw else "BULLISH"
    if "STABLE" in raw or "MID" in raw:
        return "NEUTRAL"

    return UNKNOWN_LABEL


def normalize_prediction_token(value: str | None, n_quantiles: int = 10) -> str:
    """Normalize symbolic prediction tokens into canonical labels.

    Supports tokens like `P_7_V_3` and directional aliases.
    """
    if not value:
        return UNKNOWN_LABEL

    raw = str(value).strip().upper()

    # Quantile-token style: P_<n>_V_<n>
    if raw.startswith("P_"):
        parts = raw.split("_")
        if len(parts) >= 2:
            try:
                price_bin = int(parts[1])
                return _label_from_price_bin(price_bin, n_quantiles)
            except ValueError:
                pass

    return normalize_direction_label(raw)


def signal_to_token(label: str | None) -> str:
    """Return stable token for canonical directional label."""
    normalized = normalize_direction_label(label)
    return SIGNAL_TO_TOKEN.get(normalized, SIGNAL_TO_TOKEN["NEUTRAL"])

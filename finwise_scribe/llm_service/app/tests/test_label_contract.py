from app.core.label_contract import (
    UNKNOWN_LABEL,
    normalize_direction_label,
    normalize_prediction_token,
    signal_to_token,
)
from app.ml.symbolizer import FinwiseSymbolizer


def test_direction_alias_normalization():
    assert normalize_direction_label("bull") == "BULLISH"
    assert normalize_direction_label("SELL") == "BEARISH"
    assert normalize_direction_label("hold") == "NEUTRAL"


def test_prediction_token_normalization_quantiles():
    assert normalize_prediction_token("P_9_V_1", n_quantiles=10) == "BULLISH"
    assert normalize_prediction_token("P_0_V_9", n_quantiles=10) == "BEARISH"
    assert normalize_prediction_token("P_4_V_2", n_quantiles=10) == "NEUTRAL"


def test_unknown_label_behavior():
    assert normalize_direction_label("nonsense-value") == UNKNOWN_LABEL
    assert normalize_prediction_token("garbage_token") == UNKNOWN_LABEL


def test_signal_to_token_contract():
    assert signal_to_token("BULLISH") == "P_SURGE_V_HIGH"
    assert signal_to_token("BEARISH") == "P_CRASH_V_HIGH"
    assert signal_to_token("NEUTRAL") == "P_STABLE_V_MID"


def test_symbolizer_uses_same_label_contract():
    symbolizer = FinwiseSymbolizer(n_quantiles=10)
    assert symbolizer.classify_token("P_9_V_2") == "BULLISH"
    assert symbolizer.classify_token("P_1_V_8") == "BEARISH"


def test_composite_token_normalization():
    """Test normalization of stable symbolic output tokens with volume descriptors.
    
    These tokens are logged in MLflow by engine.py and used for legacy evaluation fallbacks.
    Price-side direction must take precedence over volume descriptors.
    """
    # BULLISH tokens (P_SURGE, P_HIGH) with any volume descriptor
    assert normalize_prediction_token("P_SURGE_V_HIGH") == "BULLISH"
    assert normalize_prediction_token("P_SURGE_V_MID") == "BULLISH"
    assert normalize_prediction_token("P_SURGE_V_LOW") == "BULLISH"
    assert normalize_prediction_token("P_HIGH_V_HIGH") == "BULLISH"
    assert normalize_prediction_token("P_HIGH_V_MID") == "BULLISH"
    assert normalize_prediction_token("P_HIGH_V_LOW") == "BULLISH"

    # BEARISH tokens (P_CRASH, P_LOW) with any volume descriptor
    # CRITICAL: P_CRASH_V_HIGH must map to BEARISH, not BULLISH (common legacy pattern)
    assert normalize_prediction_token("P_CRASH_V_HIGH") == "BEARISH"
    assert normalize_prediction_token("P_CRASH_V_MID") == "BEARISH"
    assert normalize_prediction_token("P_CRASH_V_LOW") == "BEARISH"
    assert normalize_prediction_token("P_LOW_V_HIGH") == "BEARISH"
    assert normalize_prediction_token("P_LOW_V_MID") == "BEARISH"
    assert normalize_prediction_token("P_LOW_V_LOW") == "BEARISH"

    # NEUTRAL tokens (P_STABLE, P_MID) with any volume descriptor
    assert normalize_prediction_token("P_STABLE_V_HIGH") == "NEUTRAL"
    assert normalize_prediction_token("P_STABLE_V_MID") == "NEUTRAL"
    assert normalize_prediction_token("P_STABLE_V_LOW") == "NEUTRAL"
    assert normalize_prediction_token("P_MID_V_HIGH") == "NEUTRAL"
    assert normalize_prediction_token("P_MID_V_MID") == "NEUTRAL"
    assert normalize_prediction_token("P_MID_V_LOW") == "NEUTRAL"


def test_direction_label_composite_tokens():
    """Test normalize_direction_label with composite tokens for fallback evaluation."""
    # Test legacy/fallback paths that call normalize_direction_label directly
    assert normalize_direction_label("P_SURGE_V_HIGH") == "BULLISH"
    assert normalize_direction_label("P_CRASH_V_HIGH") == "BEARISH"
    assert normalize_direction_label("P_STABLE_V_MID") == "NEUTRAL"
    assert normalize_direction_label("P_HIGH_V_MID") == "BULLISH"
    assert normalize_direction_label("P_LOW_V_HIGH") == "BEARISH"  # P_LOW takes precedence over V_HIGH

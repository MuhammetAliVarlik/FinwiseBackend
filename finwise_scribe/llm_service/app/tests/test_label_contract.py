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

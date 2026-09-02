import pytest

from ullm.parsing import parse_prediction


def test_parse_prediction_normalizes_rounding():
    out = parse_prediction('{"label":"Unknown","probabilities":{"True":0.1,"False":0.1,"Unknown":0.79},"reason_short":"x"}')
    assert out["label"] == "Unknown"
    assert abs(sum(out["probabilities"].values()) - 1.0) < 1e-9
    assert abs(out["probability_sum_raw"] - 0.99) < 1e-9
    assert out["normalization_delta"] > 0
    assert out["argmax_consistent"] is True


def test_parse_prediction_flags_label_argmax_inconsistency():
    out = parse_prediction('{"label":"Unknown","probabilities":{"True":0.8,"False":0.1,"Unknown":0.1},"reason_short":"x"}')
    assert out["argmax_consistent"] is False


def test_parse_prediction_rejects_nonfinite_or_negative_values():
    with pytest.raises(ValueError):
        parse_prediction('{"label":"True","probabilities":{"True":1.1,"False":-0.1,"Unknown":0.0},"reason_short":"x"}')

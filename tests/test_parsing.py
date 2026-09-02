from ullm.parsing import parse_prediction


def test_parse_prediction_normalizes_rounding():
    out = parse_prediction('{"label":"Unknown","probabilities":{"True":0.1,"False":0.1,"Unknown":0.79},"reason_short":"x"}')
    assert out["label"] == "Unknown"
    assert abs(sum(out["probabilities"].values()) - 1.0) < 1e-9

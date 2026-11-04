import pytest

from bot.config import ROOT, load_config, load_strategy_spec
from bot.strategies import make_strategy


def test_all_strategy_files_load():
    for p in (ROOT / "strategies").glob("*.yaml"):
        spec = load_strategy_spec(p)
        make_strategy(spec.type, spec.name, spec.params)


def test_config_loads():
    cfg = load_config()
    assert cfg.shadow_strategies


def test_unknown_param_rejected():
    with pytest.raises(ValueError):
        make_strategy("htf_trend", "x", {"entry_smaa": 50})


def test_unknown_risk_key_rejected(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text("name: x\ntype: htf_trend\nrisk:\n  stop: 0.1\n")
    with pytest.raises(ValueError):
        load_strategy_spec(p)

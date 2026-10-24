import pytest

from midterms.config import DEFAULT_PATH, ModelConfig, load_config


def test_default_config_loads_with_expected_types():
    cfg = load_config()
    assert isinstance(cfg, ModelConfig)
    assert isinstance(cfg.simulation.n_draws, int)
    assert isinstance(cfg.polls.population_priority, tuple)
    assert isinstance(cfg.polls.include_internal, bool)
    assert isinstance(cfg.national.df, float)
    assert cfg.national.distribution == "student_t"


def test_missing_key_is_rejected(tmp_path):
    text = DEFAULT_PATH.read_text().replace("seed = 20261103", "")
    path = tmp_path / "model.toml"
    path.write_text(text)
    with pytest.raises(KeyError, match="seed"):
        load_config(path)


def test_unknown_key_is_rejected(tmp_path):
    text = DEFAULT_PATH.read_text() + "\n[extra]\nfoo = 1\n"
    path = tmp_path / "model.toml"
    path.write_text(text)
    with pytest.raises(KeyError, match="extra"):
        load_config(path)


def test_wrong_type_is_rejected(tmp_path):
    text = DEFAULT_PATH.read_text().replace("n_draws = 20000", 'n_draws = "lots"')
    path = tmp_path / "model.toml"
    path.write_text(text)
    with pytest.raises(TypeError, match="n_draws"):
        load_config(path)


def write_variant(tmp_path, old, new):
    path = tmp_path / "model.toml"
    path.write_text(DEFAULT_PATH.read_text().replace(old, new))
    return path


def test_int_is_widened_to_float(tmp_path):
    path = write_variant(tmp_path, "df = 5.0", "df = 5")
    cfg = load_config(path)
    assert cfg.national.df == 5.0
    assert isinstance(cfg.national.df, float)


def test_bool_is_rejected_for_int_field(tmp_path):
    path = write_variant(tmp_path, "n_draws = 20000", "n_draws = true")
    with pytest.raises(TypeError, match="n_draws"):
        load_config(path)


def test_bool_is_rejected_for_float_field(tmp_path):
    path = write_variant(tmp_path, "df = 5.0", "df = true")
    with pytest.raises(TypeError, match="df"):
        load_config(path)


def test_non_string_list_is_rejected(tmp_path):
    path = write_variant(
        tmp_path,
        'population_priority = ["lv", "rv", "v", "a"]',
        "population_priority = [1, 2]",
    )
    with pytest.raises(TypeError, match="population_priority"):
        load_config(path)


def test_missing_section_is_rejected(tmp_path):
    text = DEFAULT_PATH.read_text()
    start = text.index("[race_noise]")
    path = tmp_path / "model.toml"
    path.write_text(text[:start])
    with pytest.raises(KeyError, match="race_noise"):
        load_config(path)


def test_section_that_is_not_a_table_is_rejected(tmp_path):
    text = DEFAULT_PATH.read_text()
    start = text.index("[race_noise]")
    path = tmp_path / "model.toml"
    path.write_text("race_noise = 5\n" + text[:start])
    with pytest.raises(TypeError, match="race_noise"):
        load_config(path)

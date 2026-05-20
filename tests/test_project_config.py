from pathlib import Path

import yaml


def test_project_yaml_has_required_top_level_sections():
    cfg_path = Path(__file__).resolve().parents[1] / "config" / "project.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    assert "deployment" in cfg
    assert "gateway" in cfg
    assert "ngrok" in cfg
    assert "inference" in cfg
    assert "vision" in cfg
    assert "audio" in cfg
    assert "stt" in cfg
    assert "tts" in cfg


def test_project_yaml_core_field_types_are_valid():
    cfg_path = Path(__file__).resolve().parents[1] / "config" / "project.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    assert isinstance(cfg["gateway"]["port"], int)
    assert isinstance(cfg["ngrok"]["enabled"], bool)
    assert isinstance(cfg["ngrok"]["use_ephemeral_tcp"], bool)
    assert isinstance(cfg["gateway"]["transport"], str)
    assert isinstance(cfg["audio"]["sample_rate_hz"], int)
    assert isinstance(cfg["vision"]["source"], str)
    assert isinstance(cfg["audio"]["chunk_bytes"], int)
    assert isinstance(cfg["stt"]["enabled"], bool)
    assert isinstance(cfg["stt"]["backend"], str)
    assert isinstance(cfg["tts"]["enabled"], bool)
    assert isinstance(cfg["tts"]["voice"], str)

import importlib


def test_config_state_file_respects_env_override(monkeypatch, tmp_path):
    custom_state_file = str(tmp_path / "custom_state.json")
    monkeypatch.setenv("STATE_FILE", custom_state_file)

    import src.config as config_module

    reloaded = importlib.reload(config_module)

    assert reloaded.STATE_FILE == custom_state_file


def test_config_pcurl_to_mobile_defaults_to_true_matching_settings(monkeypatch):
    monkeypatch.delenv("PCURL_TO_MOBILE", raising=False)

    import src.config as config_module
    from src.infrastructure.config.settings import NotificationSettings

    reloaded = importlib.reload(config_module)

    assert reloaded.PCURL_TO_MOBILE is True
    assert reloaded.PCURL_TO_MOBILE == NotificationSettings().pcurl_to_mobile


def test_config_ai_max_output_tokens_respects_env_override(monkeypatch):
    monkeypatch.setenv("AI_MAX_OUTPUT_TOKENS", "8000")

    import src.config as config_module
    from src.infrastructure.config.settings import AISettings

    reloaded = importlib.reload(config_module)

    assert reloaded.get_ai_max_output_tokens() == 8000
    assert AISettings().max_output_tokens == 8000


def test_config_ai_max_output_tokens_defaults_and_clamps(monkeypatch):
    monkeypatch.delenv("AI_MAX_OUTPUT_TOKENS", raising=False)

    import src.config as config_module

    reloaded = importlib.reload(config_module)

    assert reloaded.get_ai_max_output_tokens() == 4000

    monkeypatch.setenv("AI_MAX_OUTPUT_TOKENS", "999999999")
    assert reloaded.get_ai_max_output_tokens() == 1_000_000

    monkeypatch.setenv("AI_MAX_OUTPUT_TOKENS", "-5")
    assert reloaded.get_ai_max_output_tokens() == 1

    monkeypatch.setenv("AI_MAX_OUTPUT_TOKENS", "garbage")
    assert reloaded.get_ai_max_output_tokens() == 4000

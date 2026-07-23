from pathlib import Path
import importlib.util
import sys


def load_module():
    script = Path(__file__).resolve().parents[1] / "scripts/retry_frozen_claim_sources.py"
    sys.path.insert(0, str(script.parent))
    spec = importlib.util.spec_from_file_location("retry_frozen_claim_sources", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_retry_preserves_original_attempt_and_exact_url() -> None:
    text = (Path(__file__).resolve().parents[1] / "scripts/retry_frozen_claim_sources.py").read_text()
    assert '"profile": "original-cached"' in text
    assert '"profile": "curl-browser-compatible"' in text
    assert "source_url" in text
    assert "status == 200" in text
    assert '"accessed_at_utc"' in text
    assert '"redirect_chain"' in text


def test_redirect_chain_parser_preserves_each_hop() -> None:
    module = load_module()
    headers = (
        "HTTP/1.1 301 Moved Permanently\r\nLocation: /canonical\r\n\r\n"
        "HTTP/2 302\r\nLocation: https://official.test/final\r\n\r\n"
        "HTTP/2 200\r\nContent-Type: text/html\r\n\r\n"
    )
    assert module.parse_redirect_chain(headers, "https://official.test/start") == [
        {
            "status": 301,
            "from_url": "https://official.test/start",
            "to_url": "https://official.test/canonical",
        },
        {
            "status": 302,
            "from_url": "https://official.test/canonical",
            "to_url": "https://official.test/final",
        },
    ]

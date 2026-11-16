# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import zlib
from pathlib import Path
from typing import Any

import pytest

from protocolith.cli import main
from protocolith.core import InputError, Store, build_atlas, init
from protocolith.core import atlas as atlas_module
from protocolith.core.atlas import (
    AtlasResult,
    build_atlas_result,
    confine,
    english_catalog,
    load_languages,
    write_atlas,
)
from protocolith.core.errors import EnvError

DATA_RE = re.compile(rb'<script type="application/json" id="atlas-data">(.*?)</script>', re.S)
ASSETS = Path(atlas_module.__file__).parent / "atlas_assets"


def card(n: int = 1, **changes: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        "evidence_id": f"PLITH-X-2026-01-{n:06d}",
        "protocol_id": "X",
        "result_status": "PASSED_UNDER_PROTOCOL",
        "domain": "demo",
        "reproduction_level": "not independently reproduced",
        "claim_boundary": "Only the stated gate.",
        "created_at": "2026-01-05",
        "official_source_name": "Demo",
        "official_source_url": "https://example.org/x",
        "unknown_future_field": {"a": [1, 2]},
    }
    out.update(changes)
    return out


def put(folder: Path, name: str, value: Any) -> Path:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")
    return path


def data_of(page: bytes) -> dict[str, Any]:
    found = DATA_RE.search(page)
    assert found
    loaded: dict[str, Any] = json.loads(found.group(1))
    return loaded


def block_of(data: dict[str, Any], index: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = json.loads(zlib.decompress(base64.b64decode(data["blocks"][index])))
    return out


@pytest.fixture
def cards(tmp_path: Path) -> Path:
    folder = tmp_path / "cards"
    for n in range(1, 4):
        put(folder, f"c{n}.json", card(n, result_status="BLOCKED_SOURCE" if n == 3 else "PASSED_UNDER_PROTOCOL"))
    return folder


def test_build_from_cards_round_trips(cards: Path) -> None:
    page = build_atlas(cards=[cards])
    data = data_of(page)
    assert data["total"] == data["shown"] == 3 and data["issues"] == {"count": 0, "items": []}
    assert data["statuses"] == {"BLOCKED_SOURCE": 1, "PASSED_UNDER_PROTOCOL": 2}
    assert data["integrity"] == [{"count": 3, "kind": "cards"}]
    assert [row[0] for row in data["rows"]] == [
        "PLITH-X-2026-01-000001",
        "PLITH-X-2026-01-000002",
        "PLITH-X-2026-01-000003",
    ]
    row = data["rows"][0]
    assert row[1:7] == [
        "X",
        "PASSED_UNDER_PROTOCOL",
        "demo",
        "not independently reproduced",
        "2026-01-05",
        "Only the stated gate.",
    ]
    assert len(row[7]) == 64 and "https://example.org/x" in row[8]
    assert block_of(data, 0)[0]["unknown_future_field"] == {"a": [1, 2]}
    assert page.startswith(b"<!doctype html>") and b"<title>Protocolith atlas</title>" in page


def test_output_is_deterministic(cards: Path, recorded: Store) -> None:
    first = build_atlas(cards=[cards], store=recorded)
    assert first == build_atlas(cards=[cards], store=recorded)
    assert first == build_atlas(cards=[str(cards)], store=str(recorded.path))


def test_page_has_no_network_references(cards: Path) -> None:
    text = build_atlas(cards=[cards]).decode()
    assert not re.search(r"(src|href)\s*=\s*[\"']?(https?:)?//", text)
    assert "@import" not in text and "url(" not in text
    assert "default-src 'none'" in text
    assert text.count("</script") == 2


def test_hostile_content_is_embedded_safely(tmp_path: Path) -> None:
    folder = tmp_path / "h"
    nasty = "</script><script>alert(1)</script><img src=x onerror=alert(1)> &    \x00\x01\x1b {{DATA}} {{T:noscript}}"
    put(folder, "a.json", card(1, evidence_id=nasty, claim_boundary=nasty * 3, domain="déjà 中文 \U0001f600"))
    put(folder, "b.json", card(2, claim_boundary="x" * 300_000, known_limitations=["y" * 1000] * 150))
    put(folder, "c.json", card(3, claim_boundary="\ud800 lone surrogate"))
    page = build_atlas(cards=[folder], title="<b>T</b> </title><script>")
    assert page.count(b"</script") == 2 and page.count(b"<script") == 2
    assert b"<img" not in page and b"<b>T</b>" not in page
    inner = DATA_RE.search(page)
    assert inner
    for bad in (b"<", b">", b"&", " ".encode(), " ".encode(), b"\x00"):
        assert bad not in inner.group(1)
    data = data_of(page)
    assert data["title"] == "<b>T</b> </title><script>"
    ids = {row[0] for row in data["rows"]}
    assert nasty in ids and "{{DATA}}" in nasty
    big = next(row for row in data["rows"] if row[0].endswith("000002"))
    assert len(big[6]) < 2200 and "clipped" in big[6]
    extra = block_of(data, 0)[[row[0] for row in data["rows"]].index(big[0])]
    assert len(extra["known_limitations"]) == 101 and extra["known_limitations"][-1].startswith("[clipped")
    assert page.count(b"<noscript>") == 1


def test_clip_bounds_depth_and_keys() -> None:
    deep: Any = "end"
    for _ in range(20):
        deep = [deep]
    assert "nested too deeply" in json.dumps(atlas_module._clip(deep))
    assert atlas_module._clip({"k" * 500: 1}) == {"k" * 200: 1}
    assert atlas_module._clip([1, None, True, 2.5]) == [1, None, True, 2.5]


def test_malformed_files_are_counted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    folder = tmp_path / "m"
    put(folder, "good.json", card(1, ratio=0.5))
    put(folder, "sub/deeper/good2.JSON", card(2))
    put(folder, "bad.json", "{not json")
    put(folder, "list.json", "[1,2]")
    put(folder, "noid.json", {"result_status": "BLOCKED_SOURCE"})
    put(folder, "nostatus.json", {"evidence_id": "A"})
    put(folder, "emptyid.json", {"evidence_id": "", "result_status": "BLOCKED_SOURCE"})
    put(folder, "nan.json", '{"evidence_id": "N", "result_status": "X", "v": NaN}')
    put(folder, "inf.json", '{"evidence_id": "I", "result_status": "X", "v": 1e999}')
    put(folder, "deep.json", "[" * 200_000)
    (folder / "latin1.json").write_bytes(b'{"evidence_id": "\xe9", "result_status": "X"}')
    (folder / "dangling.json").symlink_to(folder / "missing-target")
    (folder / "readme.txt").write_text("not json")
    big = put(folder, "big.json", card(3))
    monkeypatch.setattr(atlas_module, "MAX_FILE_BYTES", big.stat().st_size - 1)
    result = build_atlas_result(cards=[folder])
    assert result.total == 0 and result.skipped == 13 and result.ok
    monkeypatch.setattr(atlas_module, "MAX_FILE_BYTES", 10_000_000)
    result = build_atlas_result(cards=[folder])
    assert (result.total, result.skipped) == (3, 10)
    issues = data_of(result.html)["issues"]
    assert issues["count"] == 10 and {i["path"] for i in issues["items"]} >= {"bad.json", "dangling.json", "nan.json"}
    reasons = {i["path"]: i["reason"] for i in issues["items"]}
    assert reasons["dangling.json"] == "unreadable" and reasons["bad.json"] == "not valid UTF-8 JSON"


def test_issue_list_is_capped(tmp_path: Path) -> None:
    folder = tmp_path / "many"
    for n in range(atlas_module.MAX_ISSUES + 5):
        put(folder, f"b{n:03d}.json", "{")
    issues = data_of(build_atlas(cards=[folder]))["issues"]
    assert issues["count"] == atlas_module.MAX_ISSUES + 5 and len(issues["items"]) == atlas_module.MAX_ISSUES


def test_unknown_status_and_odd_types_are_kept(tmp_path: Path) -> None:
    folder = tmp_path / "u"
    put(
        folder,
        "a.json",
        card(
            1,
            result_status="SOMETHING_NEW",
            domain=5,
            claim_boundary=None,
            created_at=7,
            last_verified_date="2026-02-03",
        ),
    )
    put(
        folder,
        "b.json",
        card(2, created_at="nonsense", access_date="x", official_source_name=None, official_source_url=None),
    )
    data = data_of(build_atlas(cards=[folder]))
    assert data["statuses"] == {"PASSED_UNDER_PROTOCOL": 1, "SOMETHING_NEW": 1}
    by_id = {row[0]: row for row in data["rows"]}
    odd = by_id["PLITH-X-2026-01-000001"]
    assert odd[2] == "SOMETHING_NEW" and odd[3] is None and odd[5] == "2026-02-03" and odd[6] is None
    assert block_of(data, 0)[data["rows"].index(odd)]["domain"] == 5
    assert by_id["PLITH-X-2026-01-000002"][5] == "" and by_id["PLITH-X-2026-01-000002"][8] == ""


def test_duplicates_max_rows_and_order(tmp_path: Path) -> None:
    folder = tmp_path / "d"
    put(folder, "a.json", card(1, created_at="2026-03-01"))
    put(folder, "b.json", card(2, created_at="2026-05-01"))
    put(folder, "c.json", card(3, created_at="2026-05-01"))
    put(folder, "d.json", card(3, created_at="2026-05-01", domain="other"))
    result = build_atlas_result(cards=[folder], max_rows=2)
    assert result.total == 3 and result.shown == 2 and any("already used" in w for w in result.warnings)
    data = data_of(result.html)
    assert [row[0][-1] for row in data["rows"]] == ["2", "3"] and data["total"] == 3 and data["shown"] == 2
    assert sum(data["statuses"].values()) == 3 and len(data["blocks"]) == 1
    assert data["rows"][1][3] == "demo"  # the first file with that id wins


def test_blocks_split(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(atlas_module, "BLOCK_ROWS", 2)
    folder = tmp_path / "b"
    for n in range(5):
        put(folder, f"c{n}.json", card(n))
    data = data_of(build_atlas(cards=[folder]))
    assert len(data["blocks"]) == 3 and data["block"] == 2 and len(block_of(data, 2)) == 1


def test_from_ledger(recorded: Store) -> None:
    result = build_atlas_result(store=recorded)
    data = data_of(result.html)
    assert result.ok and result.ledger and result.ledger["ok"] and result.total == 1
    group = data["integrity"][0]
    assert group["kind"] == "ledger" and group["ok"] and group["count"] == 2 and group["head_seq"] == 1
    row = data["rows"][0]
    assert (
        row[0].startswith("PLITH-DEMO_D001-2026-11-15") and row[1] == "DEMO_D001" and row[2] == "PASSED_UNDER_PROTOCOL"
    )
    assert row[7] == json.loads(recorded.ledger_path.read_text().splitlines()[1])["hash"]
    assert block_of(data, 0)[0]["ledger_record_seq"] == 1
    assert isinstance(result.to_dict()["bytes"], int) and isinstance(result, AtlasResult)


def test_empty_ledger(store: Store) -> None:
    init(store)
    result = build_atlas_result(store=store)
    assert result.ok and result.total == 0
    assert data_of(result.html)["integrity"][0]["head_seq"] is None


def test_missing_ledger_is_an_environment_error(store: Store) -> None:
    with pytest.raises(EnvError) as info:
        build_atlas(store=store)
    assert info.value.code == "NO_LEDGER"


def test_tampered_ledger_still_builds_with_failure(recorded: Store) -> None:
    lines = recorded.ledger_path.read_text().splitlines()
    lines[1] = lines[1].replace("run-1", "run-X")
    recorded.ledger_path.write_text("\n".join(lines) + "\n")
    result = build_atlas_result(store=recorded)
    group = data_of(result.html)["integrity"][0]
    assert not result.ok and group["ok"] is False and group["problem_count"] >= 1
    assert group["problems"][0]["code"] and b"LEDGER FAILED VERIFICATION" in result.html


def test_problem_list_is_capped(recorded: Store) -> None:
    lines = recorded.ledger_path.read_text().splitlines()
    junk = [lines[0], *[f"garbage {n}" for n in range(40)]]
    recorded.ledger_path.write_text("\n".join(junk) + "\n")
    group = data_of(build_atlas(store=recorded))["integrity"][0]
    assert group["problem_count"] > atlas_module.MAX_PROBLEMS and len(group["problems"]) == atlas_module.MAX_PROBLEMS


def test_ledger_record_whose_card_cannot_be_built(recorded: Store, monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*_: Any) -> Any:
        raise InputError("CARD_INVALID", "no")

    monkeypatch.setattr(atlas_module, "build_card", refuse)
    data = data_of(build_atlas(store=recorded))
    assert data["rows"][0][0] == "LEDGER-RECORD-000001" and data["rows"][0][1] == "DEMO_D001"
    assert data["rows"][0][2] == "PASSED_UNDER_PROTOCOL"


def test_store_and_cards_together(recorded: Store, cards: Path) -> None:
    data = data_of(build_atlas(store=recorded, cards=[cards]))
    assert [g["kind"] for g in data["integrity"]] == ["ledger", "cards"] and data["total"] == 4


def test_missing_card_directory(tmp_path: Path) -> None:
    with pytest.raises(InputError) as info:
        build_atlas(cards=[tmp_path / "nope"])
    assert info.value.code == "BAD_PATH"


def test_auto_detect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recorded: Store) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(InputError) as info:
        build_atlas()
    assert info.value.code == "NO_SOURCE"
    put(tmp_path, "docs/evidence_cards/c.json", card(1))
    assert data_of(build_atlas())["integrity"][0]["kind"] == "cards"
    shutil.copytree(recorded.path, tmp_path / ".protocolith")
    assert data_of(build_atlas())["integrity"][0]["kind"] == "ledger"
    monkeypatch.setenv("PROTOCOLITH_STORE", str(tmp_path / "elsewhere"))
    assert data_of(build_atlas())["integrity"][0]["kind"] == "cards"


def test_option_validation(cards: Path) -> None:
    for bad in (0, -1, "3", True, 2.0):
        with pytest.raises(InputError):
            build_atlas(cards=[cards], max_rows=bad)
    for bad in ("", "  ", None, 5):
        with pytest.raises(InputError):
            build_atlas(cards=[cards], title=bad)
    with pytest.raises(InputError) as info:
        build_atlas(cards=[cards], default_lang="xx")
    assert info.value.code == "BAD_LANG"
    assert b"<title>A &amp; B</title>" in build_atlas(cards=[cards], title="A & B\x00\n")
    assert data_of(build_atlas(cards=[cards], title="t" * 500))["title"] == "t" * 200


def lang_dir(tmp_path: Path) -> Path:
    folder = tmp_path / "i18n"
    put(
        folder,
        "de.json",
        {"_name": "Deutsch\x07", "filter_reset": "Filter zuruecksetzen", "bogus_key": "x", "copied": 5, "copy_id": ""},
    )
    put(folder, "fr-CA.json", {"filter_all": "Tous"})
    put(folder, "bad.json", "{oops")
    put(folder, "lst.json", "[]")
    put(folder, "en.json", {"filter_all": "ALL"})
    put(folder, "Bad Code.json", {"filter_all": "x"})
    put(folder, "notes.txt", "ignored")
    (folder / "dir.json").mkdir()
    return folder


def test_i18n_fallback_and_warnings(tmp_path: Path, cards: Path) -> None:
    folder = lang_dir(tmp_path)
    result = build_atlas_result(cards=[cards], i18n_dir=folder, default_lang="de")
    langs = data_of(result.html)["i18n"]
    assert set(langs["langs"]) == {"en", "de", "fr-CA"} and langs["default"] == "de"
    german, english = langs["langs"]["de"], english_catalog()
    assert german["_name"] == "Deutsch " and german["filter_reset"] == "Filter zuruecksetzen"
    assert german["copy_id"] == english["copy_id"] and german["copied"] == english["copied"]
    assert langs["langs"]["fr-CA"]["_name"] == "fr-CA" and langs["langs"]["fr-CA"]["filter_all"] == "Tous"
    assert langs["langs"]["en"] == english and b'<html lang="de">' in result.html
    text = "\n".join(result.warnings)
    for expected in ("unknown key 'bogus_key'", "must be a string", "bad.json", "lst.json", "en.json", "Bad Code.json"):
        assert expected in text
    assert "dir.json" not in text and "notes.txt" not in text


def test_i18n_directory_must_exist(tmp_path: Path, cards: Path) -> None:
    with pytest.raises(InputError) as info:
        build_atlas(cards=[cards], i18n_dir=tmp_path / "none")
    assert info.value.code == "BAD_PATH"
    languages, warnings = load_languages(None)
    assert list(languages) == ["en"] and warnings == []


def test_catalog_matches_the_page_templates() -> None:
    html = (ASSETS / "atlas.html").read_text()
    js = (ASSETS / "atlas.js").read_text()
    used = set(re.findall(r'\bt\("(\w+)"', js)) | set(re.findall(r'data-i18n="(\w+)"', html))
    used |= set(re.findall(r"\{\{T:(\w+)\}\}", html)) | set(re.findall(r'"(col_\w+)"', js))
    for attrs in re.findall(r'data-i18n-attr="([^"]+)"', html):
        used |= {pair.split(":")[1] for pair in attrs.split(",")}
    used |= {"detail_loading", "detail_unavailable", "copied", "copy_failed"}
    catalog = set(english_catalog()) - {"_name"}
    assert used == catalog
    assert all(isinstance(v, str) and v for v in english_catalog().values())


def test_assets_are_plain_ascii_and_safe() -> None:
    for name in ("atlas.html", "atlas.css", "atlas.js"):
        text = (ASSETS / name).read_text()
        assert text.isascii(), name
    js = (ASSETS / "atlas.js").read_text()
    assert "innerHTML" not in js and "outerHTML" not in js and "insertAdjacentHTML" not in js
    assert "eval(" not in js and "fetch(" not in js and "XMLHttpRequest" not in js and "</script" not in js.lower()
    assert english_catalog()["_name"] == "English" and all(c.isascii() for c in "".join(english_catalog().values()))


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_page_script_is_valid_javascript(tmp_path: Path) -> None:
    path = tmp_path / "atlas.js"
    path.write_text((ASSETS / "atlas.js").read_text())
    done = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr


def test_write_atlas_targets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert write_atlas(b"x", "a/b/page.html") == Path("a/b/page.html")
    assert write_atlas(b"x", "p.HTM") == Path("p.HTM")
    assert write_atlas(b"y", tmp_path / "existing") == tmp_path / "existing" / "protocolith-atlas.html"
    (tmp_path / "dirwithdot.html").mkdir()
    assert write_atlas(b"z", "dirwithdot.html") == Path("dirwithdot.html/protocolith-atlas.html")
    assert write_atlas(b"w", "out/") == Path("out/protocolith-atlas.html")
    assert (
        write_atlas(b"v") == Path("protocolith-atlas.html")
        and (tmp_path / "protocolith-atlas.html").read_bytes() == b"v"
    )
    (tmp_path / "file").write_text("x")
    with pytest.raises(EnvError):
        write_atlas(b"x", "file/inner.html")


def test_confine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert confine("a/b.html") == tmp_path.resolve() / "a" / "b.html"
    assert confine("x", tmp_path / "base") == (tmp_path / "base").resolve() / "x"
    for bad in ("../x", "/etc/passwd", "", None, 3):
        with pytest.raises(InputError):
            confine(bad)
    with pytest.raises(EnvError):
        confine("a\x00b")


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_cli_cards(capsys: pytest.CaptureFixture[str], tmp_path: Path, cards: Path) -> None:
    out = tmp_path / "o" / "a.html"
    code, text, err = run(capsys, "atlas", "--cards", str(cards), "--out", str(out), "--title", "Mine")
    assert code == 0 and text.startswith(f"wrote {out} bytes=") and "records=3 shown=3 skipped=0" in text and err == ""
    assert data_of(out.read_bytes())["title"] == "Mine"
    code, text, _ = run(capsys, "atlas", "--cards", str(cards), "--out", str(out), "--json", "--max-rows", "1")
    body = json.loads(text)
    assert code == 0 and body["shown"] == 1 and body["cards"] == 3 and body["path"] == str(out)


def test_cli_ledger_and_failure(capsys: pytest.CaptureFixture[str], tmp_path: Path, recorded: Store) -> None:
    out = tmp_path / "led.html"
    code, text, _ = run(capsys, "atlas", "--store", str(recorded.path), "--out", str(out))
    assert code == 0 and "ledger=FAILED" not in text
    lines = recorded.ledger_path.read_text().splitlines()
    lines[1] = lines[1].replace("run-1", "run-X")
    recorded.ledger_path.write_text("\n".join(lines) + "\n")
    code, text, err = run(capsys, "atlas", "--store", str(recorded.path), "--out", str(out))
    assert code == 1 and "ledger=FAILED" in text and "ledger FAILED verification" in err
    assert b"LEDGER FAILED VERIFICATION" in out.read_bytes()


def test_cli_errors_and_warnings(capsys: pytest.CaptureFixture[str], tmp_path: Path, cards: Path) -> None:
    code, _, err = run(capsys, "atlas", "--store", str(tmp_path / "none"), "--out", str(tmp_path / "x.html"))
    assert code == 3 and "NO_LEDGER" in err
    code, _, err = run(capsys, "atlas", "--cards", str(tmp_path / "none"))
    assert code == 2 and "BAD_PATH" in err
    code, out, _ = run(capsys, "atlas", "--cards", str(tmp_path / "none"), "--json")
    assert code == 2 and json.loads(out)["ok"] is False
    folder = lang_dir(tmp_path)
    code, _, err = run(capsys, "atlas", "--cards", str(cards), "--i18n", str(folder), "--out", str(tmp_path / "i.html"))
    assert code == 0 and "warning: de.json: unknown key 'bogus_key' ignored" in err
    code, _, err = run(
        capsys, "atlas", "--cards", str(cards), "--default-lang", "zz", "--out", str(tmp_path / "j.html")
    )
    assert code == 2 and "BAD_LANG" in err


def test_cli_auto_detects_the_local_ledger(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recorded: Store
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PROTOCOLITH_STORE", str(recorded.path))
    code, text, _ = run(capsys, "atlas")
    assert code == 0 and "protocolith-atlas.html" in text and (tmp_path / "protocolith-atlas.html").is_file()


def test_example_translation_is_complete_and_clean() -> None:
    root = Path(__file__).resolve().parents[2]
    languages, warnings = load_languages(root / "examples" / "atlas" / "i18n")
    assert warnings == [] and languages["de"]["_name"] == "Deutsch"
    raw = json.loads((root / "examples" / "atlas" / "i18n" / "de.json").read_text())
    assert set(raw) == set(english_catalog())


def test_template_script_lists_every_key(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import importlib.util

    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "export_atlas_i18n_template", root / "scripts" / "export_atlas_i18n_template.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main([]) == 0
    assert json.loads(capsys.readouterr().out) == dict.fromkeys(english_catalog(), "")
    target = tmp_path / "t.json"
    assert module.main(["--out", str(target)]) == 0
    assert set(json.loads(target.read_text())) == set(english_catalog())

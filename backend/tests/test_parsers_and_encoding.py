"""파서·인코딩 유틸 단위 테스트."""

from app.parsers.strategy_ini import extract_strategy_name
from app.services.encoding import decode_bytes


def test_strategy_name_last_value_wins():
    txt = """
[Strategy]
StrategyName=FIRST
[Other]
StrategyName=LAST
"""
    assert extract_strategy_name(txt) == "LAST"


def test_strategy_name_quoted_value():
    assert extract_strategy_name('StrategyName="With Spaces"') == "With Spaces"
    assert extract_strategy_name("StrategyName='Single Quote'") == "Single Quote"


def test_strategy_name_missing_returns_none():
    assert extract_strategy_name("[A]\nKey=Val") is None
    assert extract_strategy_name("") is None


def test_strategy_name_case_insensitive_key():
    assert extract_strategy_name("STRATEGYNAME=Hello") == "Hello"
    assert extract_strategy_name("strategyname=Lower") == "Lower"


def test_strategy_name_ignores_comments():
    txt = "; StrategyName=COMMENT\n# StrategyName=HASH\nStrategyName=REAL"
    assert extract_strategy_name(txt) == "REAL"


def test_decode_utf8_first():
    r = decode_bytes("한글".encode("utf-8"), "utf-8,cp949,auto")
    assert r.encoding_used == "utf-8"
    assert r.fell_back is False
    assert r.text == "한글"


def test_decode_cp949_fallback():
    r = decode_bytes("한글".encode("cp949"), "utf-8,cp949,auto")
    assert r.encoding_used == "cp949"
    assert r.text == "한글"


def test_decode_force_overrides_priority():
    r = decode_bytes("hi".encode("utf-8"), "cp949,auto", force="utf-8")
    assert r.encoding_used == "utf-8"


def test_decode_broken_falls_back_with_replace():
    r = decode_bytes(b"\xff\xfe\xfd\xfc", "utf-8")
    assert r.fell_back is True
    assert "?" in r.encoding_used or "replace" in r.encoding_used

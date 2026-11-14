from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT


def test_manabloom_harness():
    """Spell text parsing, ranking within damage and healing, wreath colours and seasons, against a stubbed game."""
    lua51 = pytest.importorskip("lupa.lua51")
    run = lua51.LuaRuntime().eval("function(p, d) return assert(loadfile(p))(d) end")
    assert run(str(ROOT / "tests/lua/manabloom_harness.lua"), str(ADDON)) == 94


def test_castbar_harness():
    """The flowering cast bar over a stubbed PlayerCastingBarFrame: fill, flowers, bloom, wilt, lit border, off."""
    lua51 = pytest.importorskip("lupa.lua51")
    run = lua51.LuaRuntime().eval("function(p, d) return assert(loadfile(p))(d) end")
    assert run(str(ROOT / "tests/lua/castbar_harness.lua"), str(ADDON)) == 37

-- Manabloom's cast bar against a stubbed PlayerCastingBarFrame: Blizzard's pieces hidden, the fill fed the bar's
-- values, flowers opening as the fill reaches them, white petals for a heal and violet for damage, a bloom at the
-- right end of a completed cast (the left of a channel), wilting on an interrupt, the season's flowers, the border in the race's
-- colour (with or without Homeland), faint at rest and lit along the fill, secret values, and /manabloom castbar off.
local dir = ...
local ok = 0
local function check(c, msg) assert(c, msg); ok = ok + 1 end
local function near(a, b) return a and math.abs(a - b) < 1e-3 end

-- the game, stubbed
local noop = function() end
local function stub(t) return setmetatable(t, { __index = function() return noop end }) end
local function region(t)
    t = t or {}
    t.alpha, t.shown = t.alpha or 1, t.shown == nil and true or t.shown
    function t:SetAlpha(a) self.alpha = a end
    function t:SetShown(v) self.shown = v and true or false end
    function t:Show() self.shown = true end
    function t:Hide() self.shown = false end
    function t:SetTexture(p) self.tex = p end
    function t:SetVertexColor(r, g, b) self.rgb = { r, g, b } end
    function t:SetColorTexture(r, g, b, a) self.rgb = { r, g, b, a } end
    function t:SetSize(w, h) self.w, self.h = w, h end
    function t:SetPoint(p, rel, rp, x, y) self.at = { p, rel, rp, x, y } end
    function t:SetRotation(r) self.rot = r end
    return stub(t)
end
local secret = {}
function issecretvalue(v) return secret[v] == true end
local frames = {}
function CreateFrame(kind, _, parent)
    local f = region({ kind = kind, parent = parent, scripts = {}, level = 1 })
    function f:CreateTexture() return region({}) end
    function f:SetScript(k, fn) self.scripts[k] = fn end
    function f:RegisterEvent() end
    function f:SetFrameLevel(n) self.level = n end
    function f:GetFrameLevel() return self.level end
    function f:SetMinMaxValues(lo, hi) self.lo, self.hi = lo, hi end
    function f:SetValue(v) self.v = v end
    function f:SetStatusBarColor(r, g, b) self.rgb = { r, g, b } end
    function f:CreateAnimationGroup()
        local g = stub({ plays = 0, scripts = {} })
        function g:CreateAnimation() return stub({}) end
        function g:Play() self.plays = self.plays + 1 end
        function g:SetScript(k, fn) self.scripts[k] = fn end
        return g
    end
    frames[#frames + 1] = f
    return f
end
UIParent = {}
SlashCmdList = {}
function print() end
date = function() return "11" end                       -- November: autumn
C_Timer = { After = noop, NewTicker = noop }
local hooks = {}
function hooksecurefunc(t, name, fn)
    local orig = t[name]
    t[name] = function(...) local r = orig(...); fn(...); return r end
    hooks[name] = true
end
local loaded = {}
C_AddOns = { IsAddOnLoaded = function(n) return loaded[n] == true end }
function UnitRace() return "Night Elf", "NightElf" end
local hostile = false
function UnitCanAttack() return hostile end
function GetActionInfo() end
function GetTime() return 0 end

-- Blizzard's bar: its value and the handlers the hooks follow
local bar = setmetatable(region({ value = 0, lo = 0, hi = 2 }), nil)   -- no stub fallback: casting/channeling read nil when cleared
for _, k in ipairs({ "Border", "Background", "Spark", "DropShadow", "Text", "TextBorder" }) do bar[k] = region({}) end
function bar:GetMinMaxValues() return self.lo, self.hi end
function bar:GetValue() return self.value end
function bar:GetHeight() return 11 end
function bar:GetWidth() return 208 end
function bar:GetFrameLevel() return 5 end
function bar:IsVisible() return true end
function bar:HandleCastStart(event, id)
    self.casting, self.channeling = event ~= "channel" or nil, event == "channel" or nil
    self.spellID, self.value = id, event == "channel" and 2 or 0
end
function bar:FinishSpell() self.casting, self.channeling = nil, nil end
function bar:HandleCastStop() self.casting, self.channeling = nil, nil end
function bar:HandleInterruptOrSpellFailed(_, _, castID)
    if castID == "mine" then self.casting, self.channeling = nil, nil end
end
PlayerCastingBarFrame = bar

local ns = {}
ManabloomDB = {}
assert(loadfile(dir .. "/Castbar.lua"))("Manabloom", ns)
ns.rank = { [8936] = { kind = "heal" }, [5176] = { kind = "damage" } }
ns.Season = function() return "autumn" end
local ev = frames[1]
ev.scripts.OnEvent(ev, "PLAYER_LOGIN")
local o = frames[2]
check(hooks.HandleCastStart and hooks.FinishSpell and hooks.HandleCastStop and hooks.HandleInterruptOrSpellFailed,
    "the four handlers are hooked")
check(bar.Border.alpha == 0 and bar.Background.alpha == 0 and bar.Spark.alpha == 0, "Blizzard's border, background and spark hidden")
check(bar.Text.alpha == 1 and bar.TextBorder.alpha == 1, "the spell name and its box stay")
check(o.parent == bar and o.shown and o.level == 15, "our frame rides on the bar, above it")
check(near(o.edges[1].rgb[1], 240 / 255) and near(o.edges[1].rgb[3], 1), "the night elf's moonflower rim, no Homeland needed")
local lit = { frames[3], frames[4] }
check(near(o.edges[1].alpha, 0.22) and near(o.edges[3].alpha, 0.22) and lit[1].alpha == 0, "at rest the border is faint")
check(near(lit[1].rgb[1], 240 / 255), "the lit edges wear the same colour")

-- a heal: violet? no, white; flowers open as the fill passes them
local fill = frames[5]
bar:HandleCastStart("cast", 8936)
local f1, f5 = o.flowers[1], o.flowers[5]
check(f1.petals.tex:find("petals_autumn$") and f1.centre.tex:find("centre_autumn$"), "autumn's saffron crocus")
check(near(f1.petals.rgb[1], 0.96) and near(f1.petals.rgb[3], 1), "a heal's petals are white")
check(near(fill.rgb[1], 0.12) and near(fill.rgb[2], 0.36), "the fill is dark green")
bar.value = 0.5                                          -- a quarter: past the first flower (1/6), not the second
o.scripts.OnUpdate(o, 1)
check(fill.lo == 0 and fill.hi == 2 and fill.v == 0.5, "the fill takes the bar's own values")
check(lit[1].v == 0.5 and lit[2].hi == 2 and near(lit[1].alpha, 0.95), "top and bottom edges lit as far as the fill")
check(near(o.edges[3].alpha, 0.95) and near(o.edges[4].alpha, 0.22), "the left edge lit, the right still faint")
check(f1.open == 1 and f1.petals.alpha == 1 and f1.bud.alpha == 0, "the first flower is open")
check(o.flowers[2].open == 0 and o.flowers[2].bud.alpha == 1, "the second is still a bud")
o.scripts.OnUpdate(o, 0.1)
check(near(f1.petals.w, 11 * 1.65), "an open flower is 1.65 bar heights across")
bar.value = 2
o.scripts.OnUpdate(o, 0.1)
check(near(f5.open, 0.4), "the last flower opens over a quarter second")
local bloom = frames[7]                -- events, our frame, the two lit edges, the fill, the flowers, the bloom
bar:FinishSpell()
check(bloom.go.plays == 1 and bloom.shown and bloom.at[3] == "RIGHT", "a completed cast blooms at the right end")
check(near(bloom.x.petals.rgb[1], 0.96), "the bloom is the heal's white")
check(near(o.edges[4].alpha, 0.95), "a completed cast lights the right edge too")
bar:HandleCastStop()
check(bloom.go.plays == 1, "the stop after a finish doesn't bloom twice")

-- damage, then an interrupt: violet petals, the fill browns, the flowers close, no bloom
bar:HandleCastStart("cast", 5176)
check(near(f1.petals.rgb[1], 0.72) and near(f1.petals.rgb[3], 0.98), "damage petals are violet")
bar.value = 1; o.scripts.OnUpdate(o, 1)
bar:HandleInterruptOrSpellFailed(false, "UNIT_SPELLCAST_FAILED", "someone else's")
check(near(fill.rgb[1], 0.12), "a failed other spell (still casting) changes nothing")
bar:HandleInterruptOrSpellFailed(false, "UNIT_SPELLCAST_INTERRUPTED", "mine")
check(near(fill.rgb[1], 0.42) and near(fill.rgb[3], 0.28), "interrupted: the fill goes dry-leaf brown")
check(lit[1].alpha == 0 and near(o.edges[3].alpha, 0.22), "and the border goes back to faint")
o.scripts.OnUpdate(o, 1)
check(f1.open == 0, "and the flowers close")
bar:HandleCastStop()
check(bloom.go.plays == 1, "no bloom for an interrupted cast")

-- a channel blooms at the left, where it ends
bar:HandleCastStart("channel", 8936)
check(near(fill.rgb[1], 0.12), "a new cast is green again")
o.scripts.OnUpdate(o, 1)
check(f5.open == 1, "a channel starts full, every flower open")
bar.value = 0.2; o.scripts.OnUpdate(o, 1)
check(f5.open == 0 and f1.open == 0 and o.flowers[1].bud.alpha == 1, "and they close as it drains")
bar:FinishSpell()
check(bloom.go.plays == 2 and bloom.at[3] == "LEFT", "a finished channel blooms at the left")

-- secret values: the fill still follows, the flowers wait as buds, the kind comes from the target
local s = {}
secret[s] = true
hostile = true
bar:HandleCastStart("cast", s)
check(near(f1.petals.rgb[1], 0.72) and ManabloomDB.castbarProbe.secret == 1, "a sealed spell at an enemy: damage, counted")
bar.value = s
o.scripts.OnUpdate(o, 1)
check(fill.v == s and lit[1].v == s and f1.open == 0, "a secret value: the fill and lit edges take it, flowers stay buds")
bar.value = 0; hostile = false
bar:HandleCastStart("cast", 6948)
check(near(f1.petals.rgb[1], 1) and near(f1.petals.rgb[3], 0.55), "a cast that's neither (hearthstone): pale gold")
-- another ID for a ranked spell (a macro, another rank): found by name
C_Spell = { GetSpellName = function(id) return ({ [8936] = "Regrowth", [8938] = "Regrowth", [6948] = "Hearthstone" })[id] end }
bar:HandleCastStart("cast", 8938)
check(near(f1.petals.rgb[1], 0.96) and near(f1.petals.rgb[3], 1), "Regrowth by another ID: matched by name, white")
C_Spell = nil

-- a priest: the class's own ladder in place of the season's flowers, the tint mixed half with white
ns.ClassMotifs = function() return { "priest_1", "priest_2", "priest_3" } end
hostile = true
bar:HandleCastStart("cast", 5176)
check(f1.petals.tex:find("motif_priest_2$") and rawget(f1.centre, "tex") == nil, "a priest's flame along the bar, no flower centre")
check(f1.bud.tex:find("motif_priest_1$"), "and candles waiting ahead of the fill")
check(near(f1.petals.rgb[1], 0.86) and near(f1.petals.rgb[2], 0.75) and near(f1.petals.rgb[3], 0.99),
    "damage tints it violet, mixed half with white")
bar:FinishSpell()
check(bloom.x.petals.tex:find("motif_priest_3$"), "a finished cast ends in a halo")
ns.ClassMotifs = function() return nil end   -- a druid: the season's flowers again
bar:HandleCastStart("cast", 8936)
check(f1.petals.tex:find("petals_autumn$") and f1.bud.tex:find("cast_bud$") and near(f1.petals.rgb[1], 0.96),
    "a druid keeps the season's flowers, the heal's white at full strength")
bar:FinishSpell()
ns.ClassMotifs = nil; hostile = false

-- Homeland loaded changes nothing: the colour is the race's either way
loaded.Homeland = true
ns.Castbar()
check(near(o.edges[1].rgb[1], 240 / 255) and near(o.edges[1].rgb[3], 1), "with Homeland, the same rim")

-- off: Blizzard's bar as it was
ManabloomDB.castbar = false
ns.Castbar()
check(not o.shown and bar.Border.alpha == 1 and bar.Spark.alpha == 1 and o.scripts.OnUpdate == nil, "off: Blizzard's own bar back")
bar:HandleCastStart("cast", 8936)
bar:FinishSpell()
check(bloom.go.plays == 4, "and no blooms while off")  -- two more from the priest and druid casts above
return ok

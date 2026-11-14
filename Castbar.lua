-- Manabloom's cast bar: Blizzard's player cast bar drawn as a flowering stem. A 1 px border, a dark green fill,
-- and five of the season's flowers along the way, each a bud until the fill reaches it, then opening; a cast that
-- completes ends in one full open bloom at the end it finished on (the right for a cast, the left for a channel).
-- The petals are white for a heal and violet for damage (moonlight and the moon's own colour, the balance druid's
-- two halves); a cast that is neither (hearthstone, crafting) wears pale gold. An interrupted cast wilts: the fill
-- goes the dry-leaf brown of a wilted wreath and the flowers close.
--
-- Flowers by season (tools/manabloom_castbar.py): hawthorn blossom in spring, oxeye daisy in summer, saffron crocus
-- in autumn, snowdrop in winter; Innervate makes it spring, as it does the wreaths.
--
-- With Homeland loaded the border takes your race's homeland colour, the same rim as Homeland's coordinates tab, so
-- the cast bar sits with its minimap frame and bar caps.
--
-- How (Forever's CastingBarFrame.lua and .xml, wow-ui-source "forever" branch): PlayerCastingBarFrame, a 208 x 11
-- StatusBar run by CastingBarMixin, is left to do all its own work. This draws over it: its border, background and
-- spark are set invisible (alpha 0, restored by /manabloom castbar off), and Manabloom's own frame, a child of the
-- bar so it shows, hides, moves and fades with it, carries the look. The fill is a StatusBar fed the bar's own
-- min, max and value every frame, so it keeps working when the game hands those over as secret values; the flowers
-- need a number, so with secret values they stay buds. Success and failure come from hooks on the mixin's own
-- handlers: FinishSpell and HandleCastStop (completed), HandleInterruptOrSpellFailed (interrupted or failed).
-- /manabloom castbar on|off.
local _, ns = ...
local DIR = "Interface\\AddOns\\Manabloom\\"

local FLOWERS = 5                                  -- along the bar, evenly, between the ends
local FLOWER, BUD, BLOOM = 1.65, 1.1, 3.2          -- sizes, in bar heights
local OPEN = 0.25                                  -- seconds a flower takes to open or close
local BLOOM_TIME, BLOOM_FADE = 0.9, 0.55           -- the end bloom: how long it lasts, and the fade at its end
local FILL = { 0.12, 0.36, 0.16 }                  -- dark green
local WILTED = { 0.42, 0.36, 0.28 }                -- an interrupted cast: the wreaths' dry-leaf brown
local BACK = { 0.055, 0.063, 0.055, 0.92 }         -- behind the fill
local EDGE = { 0.82, 0.86, 0.80 }                  -- the 1 px border, without Homeland
local TINT = { heal = { 0.96, 0.97, 1.00 }, damage = { 0.72, 0.50, 0.98 }, other = { 1.00, 0.86, 0.55 } }
local HIDE = { "Border", "Background", "Spark", "DropShadow" }   -- Blizzard's pieces that ours replace
-- each race's homeland flower colour (Homeland.lua RACE_COLOUR, from tools/homeland_nouveau.py PALETTE), 0-255
local RACE_COLOUR = {
    NightElf = { 240, 236, 255 }, Human = { 244, 196, 206 }, Dwarf = { 196, 136, 206 }, Gnome = { 124, 172, 240 },
    Orc = { 244, 130, 70 }, Scourge = { 156, 116, 186 }, Tauren = { 244, 212, 96 }, Troll = { 232, 112, 200 },
}

local bar = PlayerCastingBarFrame
local o, bloom                                     -- our frame over the bar, and the end bloom
local cast = { active = false, kind = "other", channel = false }

local function Secret(v) return issecretvalue and issecretvalue(v) or false end
local function On() return ManabloomDB and ManabloomDB.castbar ~= false end
local function Season() return ns.Season and ns.Season() or "spring" end

local function Edge()
    local loaded = C_AddOns and C_AddOns.IsAddOnLoaded and C_AddOns.IsAddOnLoaded("Homeland")
    local c = loaded and RACE_COLOUR[select(2, UnitRace("player")) or ""]
    if c then return c[1] / 255, c[2] / 255, c[3] / 255 end
    return EDGE[1], EDGE[2], EDGE[3]
end

-- what the spell does, for the petals' colour: Manabloom's own ranking if it knows the spell; a spell it can't
-- read (secret in combat) is judged by the target: at an enemy, damage; otherwise a heal
local function Kind(id)
    if Secret(id) then
        local probe = ManabloomDB.castbarProbe or { secret = 0 }
        ManabloomDB.castbarProbe = probe
        probe.secret = probe.secret + 1
        return (UnitCanAttack and UnitCanAttack("player", "target")) and "damage" or "heal"
    end
    local r = ns.rank and ns.rank[id or 0]
    return r and r.kind or "other"
end

---------------------------------------------------------------------------------------------- building it
local function Line(f, a, b, wide)
    local t = f:CreateTexture(nil, "BORDER")
    t:SetPoint(a[1], f, a[1])
    t:SetPoint(b[1], f, b[1])
    local set = wide and "SetHeight" or "SetWidth"
    if PixelUtil and PixelUtil[set] then PixelUtil[set](t, 1, 1) else t[set](t, 1) end
    return t
end

local function Flower(f, layer)
    local x = {}
    x.petals = f:CreateTexture(nil, layer, nil, 2)
    x.centre = f:CreateTexture(nil, layer, nil, 3)
    x.centre:SetPoint("CENTER", x.petals, "CENTER")
    return x
end

local function Look(x, season, kind)
    local t = TINT[kind] or TINT.other
    x.petals:SetTexture(DIR .. "petals_" .. season)
    x.petals:SetVertexColor(t[1], t[2], t[3])
    x.centre:SetTexture(DIR .. "centre_" .. season)
end

local function Build()
    o = CreateFrame("Frame", nil, bar)
    o:SetPoint("TOPLEFT", bar, "TOPLEFT", -2, 2)
    o:SetPoint("BOTTOMRIGHT", bar, "BOTTOMRIGHT", 2, -2)
    o:SetFrameLevel(bar:GetFrameLevel() + 10)
    o.back = o:CreateTexture(nil, "BACKGROUND")
    o.back:SetPoint("TOPLEFT", 1, -1)
    o.back:SetPoint("BOTTOMRIGHT", -1, 1)
    o.back:SetColorTexture(BACK[1], BACK[2], BACK[3], BACK[4])
    o.edges = { Line(o, { "TOPLEFT" }, { "TOPRIGHT" }, true), Line(o, { "BOTTOMLEFT" }, { "BOTTOMRIGHT" }, true),
                Line(o, { "TOPLEFT" }, { "BOTTOMLEFT" }), Line(o, { "TOPRIGHT" }, { "BOTTOMRIGHT" }) }
    o.fill = CreateFrame("StatusBar", nil, o)
    o.fill:SetAllPoints(bar)
    o.fill:SetStatusBarTexture("Interface\\Buttons\\WHITE8x8")
    o.fill:SetFrameLevel(o:GetFrameLevel() + 1)
    o.top = CreateFrame("Frame", nil, o)             -- the flowers, above the fill
    o.top:SetAllPoints(o)
    o.top:SetFrameLevel(o:GetFrameLevel() + 2)
    o.flowers = {}
    for i = 1, FLOWERS do
        local x = Flower(o.top, "ARTWORK")
        x.bud = o.top:CreateTexture(nil, "ARTWORK", nil, 1)
        x.bud:SetTexture(DIR .. "cast_bud")
        x.at = i / (FLOWERS + 1)
        x.open = 0
        o.flowers[i] = x
    end
    bloom = CreateFrame("Frame", nil, UIParent)
    bloom:SetFrameStrata("HIGH")
    bloom:Hide()
    bloom.x = Flower(bloom, "OVERLAY")
    bloom.x.petals:SetAllPoints()
    bloom.go = bloom:CreateAnimationGroup()
    local grow = bloom.go:CreateAnimation("Scale")
    grow:SetScaleFrom(0.45, 0.45)
    grow:SetScaleTo(1.2, 1.2)
    grow:SetDuration(BLOOM_TIME)
    grow:SetSmoothing("OUT")
    local turn = bloom.go:CreateAnimation("Rotation")
    turn:SetDegrees(-25)
    turn:SetDuration(BLOOM_TIME)
    turn:SetSmoothing("OUT")
    local fade = bloom.go:CreateAnimation("Alpha")
    fade:SetFromAlpha(1)
    fade:SetToAlpha(0)
    fade:SetStartDelay(BLOOM_TIME - BLOOM_FADE)
    fade:SetDuration(BLOOM_FADE)
    bloom.go:SetScript("OnFinished", function() bloom:Hide() end)
end

---------------------------------------------------------------------------------------------- each frame
local function Progress()
    local lo, hi = bar:GetMinMaxValues()
    local v = bar:GetValue()
    o.fill:SetMinMaxValues(lo, hi)                   -- secret or not, a StatusBar takes them
    o.fill:SetValue(v)
    if Secret(lo) or Secret(hi) or Secret(v) or not (hi and v) or hi <= (lo or 0) then return nil end
    return (v - (lo or 0)) / (hi - (lo or 0))
end

local function Draw(_, dt)
    local p = Progress()
    local h = bar:GetHeight() or 11
    local w = bar:GetWidth() or 208
    for _, x in ipairs(o.flowers) do
        local want = (p and p >= x.at) and 1 or 0
        if not cast.active and cast.wilted then want = 0 end
        local step = (dt or 0) / OPEN
        x.open = want > x.open and math.min(want, x.open + step) or math.max(want, x.open - step)
        local size = h * FLOWER * (0.5 + 0.5 * x.open)
        x.petals:ClearAllPoints()
        x.petals:SetPoint("CENTER", bar, "LEFT", w * x.at, 0)
        x.petals:SetSize(size, size)
        x.centre:SetSize(size, size)
        if x.petals.SetRotation then x.petals:SetRotation(-0.6 * (1 - x.open)) end
        x.petals:SetAlpha(x.open)
        x.centre:SetAlpha(x.open)
        x.bud:ClearAllPoints()
        x.bud:SetPoint("CENTER", bar, "LEFT", w * x.at, 0)
        x.bud:SetSize(h * BUD, h * BUD)
        x.bud:SetAlpha(1 - x.open)
    end
end

---------------------------------------------------------------------------------------------- the cast
local function Colour(c) o.fill:SetStatusBarColor(c[1], c[2], c[3]) end

local function Start()
    if not (o and On()) then return end
    cast.active, cast.wilted = true, false
    cast.channel = bar.channeling and true or false
    cast.kind = Kind(bar.spellID)
    local season = Season()
    for _, x in ipairs(o.flowers) do Look(x, season, cast.kind); x.open = 0 end
    Colour(FILL)
end

local function Bloom()
    if not (bloom and On() and bar:IsVisible()) then return end
    local size = (bar:GetHeight() or 11) * BLOOM
    bloom:SetSize(size, size)
    bloom.x.centre:SetSize(size, size)
    bloom:ClearAllPoints()
    bloom:SetPoint("CENTER", bar, cast.channel and "LEFT" or "RIGHT", 0, 0)
    Look(bloom.x, Season(), cast.kind)
    bloom.go:Stop()
    bloom:Show()
    bloom.go:Play()
end

local function Done()                                -- the cast completed: one bloom at the end
    if not cast.active then return end
    cast.active = false
    Bloom()
end

local function Wilt()                                -- interrupted or failed: the fill browns, the flowers close
    if not cast.active then return end
    cast.active, cast.wilted = false, true
    Colour(WILTED)
end

local function Stopped(self)
    if not (self.casting or self.channeling or self.reverseChanneling) then Done() end
end

local function Failed(self)
    if not (self.casting or self.channeling or self.reverseChanneling) then Wilt() end
end

---------------------------------------------------------------------------------------------- on and off
function ns.Castbar()
    if not (bar and o) then return end
    local on = On()
    for _, k in ipairs(HIDE) do
        if bar[k] and bar[k].SetAlpha then bar[k]:SetAlpha(on and 0 or 1) end
    end
    o:SetShown(on)
    o:SetScript("OnUpdate", on and Draw or nil)
    local r, g, b = Edge()
    for _, t in ipairs(o.edges) do t:SetColorTexture(r, g, b, 1) end
    if not on and bloom then bloom.go:Stop(); bloom:Hide() end
end

if bar then
    local ev = CreateFrame("Frame")
    ev:RegisterEvent("PLAYER_LOGIN")
    ev:SetScript("OnEvent", function()
        Build()
        hooksecurefunc(bar, "HandleCastStart", Start)
        hooksecurefunc(bar, "FinishSpell", Done)
        hooksecurefunc(bar, "HandleCastStop", Stopped)
        hooksecurefunc(bar, "HandleInterruptOrSpellFailed", Failed)
        Colour(FILL)
        ns.Castbar()
        if bar.casting or bar.channeling then Start() end   -- a /reload mid-cast
    end)
end

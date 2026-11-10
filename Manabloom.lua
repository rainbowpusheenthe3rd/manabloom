-- Manabloom: a seasonal wreath round each action button, coloured by how much the spell does per point of mana.
-- Red is your least efficient spell of its kind, through violet and blue, to white for your most efficient:
-- damage spells are ranked against damage spells, heals against heals. Spells with no number in their text
-- (Mark of the Wild, Thorns, forms) and spells that cost no mana get no wreath.
--
-- What a spell does comes from its own description ("Causes 13 to 16 Nature damage", "Heals ... for 32 over
-- 12 sec"): each "X to Y" counts as its average, plus any single amounts ("an additional 12", "for 32");
-- durations, ranges and percentages are skipped. Its cost is its mana cost (GetSpellPowerCost).
--
-- The wreath follows the season: autumn oak leaves and acorns (Sep-Nov), winter frost (Dec-Feb), spring blossom
-- (Mar-May), summer ivy (Jun-Aug). And it's alive:
--   * below a third of your mana the least efficient wreaths wilt (droop, fade, go brown) and the best glow;
--     drinking brings them back as the mana comes back;
--   * a shared bramble: while you cast, efficient casts (the better half of your scale for that kind) climb a
--     six-step ladder shown on every wreath, north then south: bud, two buds, flower and bud, two flowers,
--     berry and flower, two berries; poor casts step it back; after a few quiet seconds it goes;
--   * Innervate turns every wreath to spring blossom while it lasts;
--   * Moonkin form makes them starlit; cat and bear, where nothing costs mana, curl them shut;
--   * the first time you log in after the season changes, the old wreaths shed and the new ones grow in;
--   * a new rank you've learned but not put on your bars sprouts a little green leaf on the old rank's button.
-- /manabloom for commands.
local ADDON, ns = ...
local DIR = "Interface\\AddOns\\Manabloom\\"
local SEASONS = { "winter", "winter", "spring", "spring", "spring", "summer", "summer", "summer",
                  "autumn", "autumn", "autumn", "winter" }
local BARS = { "ActionButton", "MultiBarBottomLeftButton", "MultiBarBottomRightButton", "MultiBarRightButton",
               "MultiBarLeftButton", "MultiBar5Button", "MultiBar6Button", "MultiBar7Button" }
local SCALE = 1.5  -- the wreath texture is this many buttons across (tools/manabloom_textures.py)
-- red, violet, blue, moonlight white: worst to best
local RAMP = { { 0.92, 0.16, 0.10 }, { 0.62, 0.30, 0.92 }, { 0.30, 0.56, 1.00 }, { 0.94, 0.97, 1.00 } }
-- /manabloom colours season: each season's own range instead, worst to best, getting lighter as it goes
local RAMPS = {
    autumn = { { 0.62, 0.10, 0.06 }, { 0.93, 0.40, 0.08 }, { 1.00, 0.76, 0.22 }, { 1.00, 0.95, 0.78 } },  -- rust, orange, gold, cream
    -- winter's ice darkened 9 Nov 2026: at 0.55/0.82/1.00 its lightness (0.80) sat too close to snow's (0.99)
    winter = { { 0.62, 0.08, 0.20 }, { 0.52, 0.42, 0.80 }, { 0.40, 0.68, 1.00 }, { 0.97, 0.99, 1.00 } },  -- holly berry, frost lilac, deep ice, snow
    spring = { { 0.52, 0.34, 0.24 }, { 0.98, 0.50, 0.70 }, { 0.55, 0.90, 0.42 }, { 1.00, 0.97, 0.96 } },  -- bare earth, blossom, new green, white blossom
    summer = { { 0.80, 0.10, 0.12 }, { 0.98, 0.55, 0.12 }, { 0.40, 0.82, 0.30 }, { 1.00, 0.98, 0.82 } },  -- poppy, sun, leaf, sunlit cream
}
local SKIP_AFTER = { sec = true, seconds = true, min = true, minutes = true, yd = true, yards = true, ["%"] = true,
                     sec_ = true, hr = true, hour = true, hours = true, charges = true, targets = true, times = true }
local WILT_AT = 1 / 3                        -- mana fraction below which the worst wreaths start to wilt
local WILTED = { 0.42, 0.36, 0.28 }          -- dry-leaf brown a fully wilted wreath fades towards
local STARLIT = { 0.86, 0.90, 1.00 }         -- Moonkin's silver
local MOONKIN, CURLED = 31, { [1] = true, [5] = true, [8] = true }  -- GetShapeshiftFormID: cat, bear, dire bear
local INNERVATE = "Innervate"
local SPROUT = { 0.45, 0.95, 0.35 }
-- The bramble's ladder: two motifs per wreath, north and south, in their own natural colours (tools/
-- manabloom_motifs.py), so the stage reads apart from the efficiency colour. Step 0 shows nothing.
local LADDER = { { "bud" }, { "bud", "bud" }, { "flower", "bud" }, { "flower", "flower" },
                 { "berry", "flower" }, { "berry", "berry" } }
local MOTIF = 0.36                                      -- a motif's size, in button widths
-- 9 Nov 2026: the top quarter (0.75) sent a normal Wrath-and-Moonfire fight to seed every time (Wrath Rank 2
-- sits at 0.69 under Rank 1); the better half ripens on good choices and still falls on poor ones.
local IDEAL, REST_AFTER = 0.5, 8                       -- better half climbs; seconds without a cast before it rests
local db

local function Print(msg) print("|cff7fd07fManabloom|r: " .. msg) end

-- what the description says the spell does, and whether that's damage or healing
function ns.Amount(desc)
    if not desc or desc == "" then return end
    local d = desc:gsub("(%d),(%d)", "%1%2")
    if d:find("dead target") or d:find("[Rr]esurrect") then return end  -- Revive, Rebirth: a life, not a heal
    local h = d:gsub("[Hh]ealth", "")  -- Bear Form's "health by 560" is not healing
    local kind = h:find("[Hh]eal") and "heal" or d:find("damage") and "damage"
    if not kind or d:find("attackers") then return end  -- Thorns hurts only those who hit the target
    local total = 0
    d = d:gsub("(%d+%.?%d*) to (%d+%.?%d*)", function(a, b) total = total + (tonumber(a) + tonumber(b)) / 2; return "#" end)
    for n, after in d:gmatch("(%d+%.?%d*)%s*([%%%a]*)") do
        if not SKIP_AFTER[after:lower()] then total = total + tonumber(n) end
    end
    if total > 0 then return total, kind end
end

local function Description(id)
    if C_Spell and C_Spell.GetSpellDescription then return C_Spell.GetSpellDescription(id) end
    return GetSpellDescription and GetSpellDescription(id)
end

local function Mana(id)
    local costs = (C_Spell and C_Spell.GetSpellPowerCost and C_Spell.GetSpellPowerCost(id))
        or (GetSpellPowerCost and GetSpellPowerCost(id))
    for _, c in ipairs(costs or {}) do
        if c.type == 0 or c.name == "MANA" then
            local cost = (c.cost and c.cost > 0 and c.cost) or c.minCost
            return cost and cost > 0 and cost or nil
        end
    end
end

local function SpellName(id)
    if C_Spell and C_Spell.GetSpellName then return C_Spell.GetSpellName(id) end
    return GetSpellInfo and (GetSpellInfo(id))
end

local function Rank(id)
    local sub = (C_Spell and C_Spell.GetSpellSubtext and C_Spell.GetSpellSubtext(id))
        or (GetSpellSubtext and GetSpellSubtext(id))
    return sub and sub:find("^Rank") and sub or nil
end

local function FullName(id)
    local rank = Rank(id)
    return (SpellName(id) or tostring(id)) .. (rank and (" (" .. rank .. ")") or "")
end

local function SpellOf(slot)
    if not slot then return end
    local kind, id = GetActionInfo(slot)
    if kind == "spell" then return id end
    if kind == "macro" and GetMacroSpell then return (GetMacroSpell(id)) end
end

-- Innervate makes it spring whatever the calendar; while the season turns, the old one still shows
local function Season()
    if ns.innervate then return "spring" end
    return ns.turning or db.season or SEASONS[tonumber(date("%m"))]
end

local function Colour(t)
    local ramp = db and db.colours == "season" and RAMPS[Season()] or RAMP
    t = math.max(0, math.min(1, t)) * (#ramp - 1)
    local i = math.min(#ramp - 2, math.floor(t))  -- the top of the scale stays in the last segment
    local f, a, b = t - i, ramp[i + 1], ramp[i + 2]
    return a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, a[3] + (b[3] - a[3]) * f
end

local function Mix(r, g, b, to, f)
    return r + (to[1] - r) * f, g + (to[2] - g) * f, b + (to[3] - b) * f
end

ns.Colour, ns.Season = Colour, Season

-- a small oak leaf in the efficiency colour, for the tooltip line and chat (an inline texture, tinted)
function ns.Leaf(t, size)
    local r, g, b = Colour(t)
    return ("|T%sleaf:%d:%d:0:0:32:32:0:32:0:32:%d:%d:%d|t"):format(DIR, size or 14, size or 14,
        math.floor(r * 255 + 0.5), math.floor(g * 255 + 0.5), math.floor(b * 255 + 0.5))
end

local function Buttons()
    local out = {}
    for _, bar in ipairs(BARS) do
        for i = 1, 12 do
            local b = _G[bar .. i]
            if b then out[#out + 1] = b end
        end
    end
    return out
end

local function Slot(b)
    return b.action or (b.GetAttribute and b:GetAttribute("action"))
end

-- Secret values: the game can hand addons your mana (and in combat, spell IDs and buff names) as "secret" values
-- that may be displayed but not compared or computed with; doing so is an immediate error (9 Nov 2026 on
-- Forever: "attempt to perform arithmetic on a secret number value", and no wreaths at all). Everything that
-- reads them checks first. https://warcraft.wiki.gg/wiki/Secret_Values
local function Secret(v) return issecretvalue and issecretvalue(v) or false end

-- how far into wilting: 0 at a third of your mana or more, 1 at none; nil when your mana is secret. Then
-- there's no wilting: a fade driven by the sealed value through curves was tried (9 Nov 2026) but couldn't be
-- checked in game, and with the bramble it left the wreaths all but invisible in combat.
function ns.Wilt()
    if not (UnitPower and UnitPowerMax) then return 0 end
    local cur, max = UnitPower("player", 0), UnitPowerMax("player", 0)
    if Secret(cur) or Secret(max) then return nil end
    if not max or max <= 0 then return 0 end
    local m = cur / max
    return m < WILT_AT and (WILT_AT - m) / WILT_AT or 0
end

local function Form() return GetShapeshiftFormID and GetShapeshiftFormID() or nil end

-- how each wreath looks now: its efficiency colour, then the season, the form, and the mana
function ns.Style()
    if not db then return end
    local tex = DIR .. Season()
    local wilt, form = ns.Wilt(), Form()
    wilt = wilt or 0
    local curled = CURLED[form]
    for _, b in ipairs(Buttons()) do
        local id = SpellOf(Slot(b))
        local r = ns.rank[id or 0]
        local w, glow = b.manabloom, b.manabloomGlow
        if w and r and not db.off then
            local droop = wilt * (1 - r.t)  -- the worst wilt the most; the best not at all
            local cr, cg, cb = Colour(r.t)
            if form == MOONKIN then cr, cg, cb = Mix(cr, cg, cb, STARLIT, 0.45) end
            cr, cg, cb = Mix(cr, cg, cb, WILTED, 0.7 * droop)
            local size = (b:GetWidth() or 36) * SCALE * (curled and 0.8 or 1) * (1 - 0.08 * droop)
            w:SetSize(size, size)
            w:SetTexture(tex)
            w:SetVertexColor(cr, cg, cb)
            w:ClearAllPoints()
            w:SetPoint("CENTER", b, "CENTER", 0, -3 * droop)  -- a wilting wreath sags
            local O = db.opacity or 1   -- /manabloom opacity: the wreaths' own strength, separate from any bar fade
            w:SetAlpha(O * (curled and 0.35 or 1) * (1 - 0.45 * droop))
            w:Show()
            local shine = curled and 0 or wilt * r.t * 0.5  -- the best glow softly brighter as the mana runs low
            if shine > 0.02 then
                glow:SetSize(size, size)
                glow:SetTexture(tex)
                glow:SetVertexColor(Colour(r.t))
                glow:SetAlpha(O * shine)
                glow:Show()
            else
                glow:Hide()
            end
            -- the shared bramble's stage, north then south, while you're casting
            local step = not curled and ns.bramble and LADDER[ns.bramble]
            local m = (b:GetWidth() or 36) * MOTIF
            for i, t in ipairs({ b.manabloomN, b.manabloomS }) do
                local name = step and step[i]
                if name then
                    t:SetSize(m, m)
                    t:SetTexture(DIR .. "motif_" .. name)
                    t:SetVertexColor(1, 1, 1)  -- their own colours, not the efficiency tint
                    t:SetAlpha(O)
                    t:ClearAllPoints()
                    t:SetPoint("CENTER", b, i == 1 and "TOP" or "BOTTOM", 0, (i == 1 and 1 or -1) * m * 0.15)
                    t:Show()
                else
                    t:Hide()
                end
            end
        elseif w then
            w:Hide(); glow:Hide(); b.manabloomN:Hide(); b.manabloomS:Hide()
        end
        -- a new rank in the spellbook that isn't on the bars yet: a sprout on the old rank's button
        local name = id and SpellName(id)
        local newer = name and db.sprouts and db.sprouts[name]
        if newer and newer ~= id and not db.off then
            if not b.manabloomSprout then
                local s = b:CreateTexture(nil, "OVERLAY", nil, 7)
                s:SetTexture(DIR .. "leaf")
                s:SetSize(14, 14)
                s:SetPoint("TOPRIGHT", b, "TOPRIGHT", 3, 3)
                s:SetVertexColor(SPROUT[1], SPROUT[2], SPROUT[3])
                if s.SetIgnoreParentAlpha then s:SetIgnoreParentAlpha(true) end
                b.manabloomSprout = s
            end
            b.manabloomSprout:SetAlpha(db.opacity or 1)
            b.manabloomSprout:Show()
        elseif b.manabloomSprout then
            b.manabloomSprout:Hide()
        end
    end
    if ns.MinimapLook then ns.MinimapLook() end  -- the minimap leaf follows the colours and on/off
end

ns.rank = {}  -- spellID -> { per mana, kind, t (0 worst .. 1 best), best name }
local pending, styling = false, false

-- every spell on the bars, its amount per mana, ranked within its kind; then each button's wreath
function ns.Refresh()
    pending = false
    if not db then return end
    -- No re-ranking in combat (9 Nov 2026: wreaths vanished mid-fight with no error, most likely a spell's text or
    -- cost briefly missing, which dropped it from the ranking). Keep the last good ranking and restyle; re-rank
    -- when combat ends (PLAYER_REGEN_ENABLED). Before the first ranking there's nothing to keep, so rank anyway.
    if InCombatLockdown and InCombatLockdown() and next(ns.rank) then
        db.combatSkips = (db.combatSkips or 0) + 1
        return ns.Style()
    end
    local eff, best = {}, { damage = {}, heal = {} }
    local buttons = Buttons()
    local onBars = {}
    for _, b in ipairs(buttons) do
        local id = SpellOf(Slot(b))
        if id then onBars[id] = true end
        if id and not eff[id] then
            local amount, kind = ns.Amount(Description(id))
            local mana = Mana(id)
            if amount and mana then
                eff[id] = { amount / mana, kind }
                local k = best[kind]
                k.lo = math.min(k.lo or math.huge, amount / mana)
                if amount / mana > (k.hi or 0) then k.hi, k.name = amount / mana, SpellName(id) end
            end
        end
    end
    local before, after = 0, 0  -- spells that would drop out of the ranking: counted, to confirm the cause above
    for _ in pairs(ns.rank) do before = before + 1 end
    for _ in pairs(eff) do after = after + 1 end
    if after < before then db.rankDrops = (db.rankDrops or 0) + 1 end
    wipe(ns.rank)
    for id, e in pairs(eff) do
        local k = best[e[2]]
        local span = math.log(k.hi) - math.log(k.lo)
        ns.rank[id] = { per = e[1], kind = e[2], t = span > 0 and (math.log(e[1]) - math.log(k.lo)) / span or 1, best = k.name }
    end
    for name, id in pairs(db.sprouts or {}) do  -- the new rank is on the bars now: the sprout has done its job
        if onBars[id] then db.sprouts[name] = nil end
    end
    for _, b in ipairs(buttons) do
        if ns.rank[SpellOf(Slot(b)) or 0] and not b.manabloom then
            b.manabloom = b:CreateTexture(nil, "OVERLAY", nil, 6)
            b.manabloomGlow = b:CreateTexture(nil, "OVERLAY", nil, 7)
            b.manabloomGlow:SetPoint("CENTER")
            if b.manabloomGlow.SetBlendMode then b.manabloomGlow:SetBlendMode("ADD") end
            b.manabloomN = b:CreateTexture(nil, "OVERLAY", nil, 7)
            b.manabloomS = b:CreateTexture(nil, "OVERLAY", nil, 7)
            -- the wreath keeps its own opacity when a bar is faded (Stillwater's quiet bars); wilting still fades it
            for _, t in ipairs({ b.manabloom, b.manabloomGlow, b.manabloomN, b.manabloomS }) do
                if t.SetIgnoreParentAlpha then t:SetIgnoreParentAlpha(true) end
            end
        end
    end
    ns.Style()
end

-- An error while drawing is said once in chat and kept in ManabloomDB.lastError (read after a /reload),
-- rather than failing silently and leaving no wreaths.
local function Safely(fn)
    local ok, err = pcall(fn)
    if not ok then
        pending = false
        if db and db.lastError ~= err then Print("|cffff6666an error stopped the wreaths:|r " .. tostring(err)) end
        if db then db.lastError = err end
    end
end

local function Soon()
    if pending then return end
    pending = true
    C_Timer.After(0.2, function() Safely(ns.Refresh) end)
end

local function StyleSoon()  -- mana ticks come often: restyle at most four times a second
    if styling then return end
    styling = true
    C_Timer.After(0.25, function() styling = false; Safely(ns.Style) end)
end

-- Leaves on the screen, two kinds. Falling: while the mouse is on a wreathed button, one a second (so n leaves
-- take n seconds) down the left and right edges, coloured round the ramp from red to moonlight white over a
-- cycle of CYCLE leaves, then again; off the button, no new ones start and the falling ones fade out.
-- Bursts: a handful flung out of a wreath (a cast, Innervate, the season turning), arcing down and fading.
local CYCLE, EVERY, FALL, BAND, FADE, LIFE = 12, 1.0, 7.0, 0.11, 0.6, 1.0
local sky, leaves, over, nextAt, count, clock = nil, {}, nil, 0, 0, 0

local function Leaf()
    for _, x in ipairs(leaves) do if not x.on then return x end end
    local l = { tex = sky:CreateTexture(nil, "ARTWORK") }
    l.tex:SetTexture(DIR .. "leaf")
    leaves[#leaves + 1] = l
    return l
end

local function Drop()
    local t = (count % CYCLE) / (CYCLE - 1)
    count = count + 1
    local l = Leaf()
    local w = sky:GetWidth()
    local side = count % 2 == 1 and 0 or 1                       -- left, right, left...
    l.kind = "fall"
    l.x = (side == 0 and math.random() * BAND or 1 - math.random() * BAND) * w
    l.age, l.on, l.fading = 0, true, nil
    l.size = 20 + math.random() * 14
    l.spin, l.sway, l.phase = (math.random() - 0.5) * 3, 18 + math.random() * 22, math.random() * 6.28
    l.tex:SetSize(l.size, l.size)
    l.tex:SetVertexColor(Colour(math.min(t, 1)))
    l.tex:Show()
end

local function Fall(_, dt)
    clock = clock + dt
    if over and not over:IsMouseOver() then over = nil end         -- moused off: stop sending more
    if over and clock >= nextAt then Drop(); nextAt = clock + EVERY end
    local h, any = sky:GetHeight(), false
    for _, l in ipairs(leaves) do
        if l.on then
            l.age = l.age + dt
            local x, y, a
            if l.kind == "burst" then
                local p = l.age / LIFE
                x = l.x + l.vx * l.age
                y = l.y + l.vy * l.age - 60 * l.age * l.age            -- flung out, then falling
                a = p < 1 and 0.7 * (1 - p) or 0
            else
                if not over and not l.fading then l.fading = 0 end
                if l.fading then l.fading = l.fading + dt end
                local p = l.age / FALL
                a = p < 1 and 0.85 * math.min(1, l.age / 0.4) * math.min(1, (1 - p) / 0.15) or 0
                if l.fading then a = a * math.max(0, 1 - l.fading / FADE) end
                x = l.x + math.sin(l.age * 1.3 + l.phase) * l.sway
                y = h + 20 - p * (h + 40)
            end
            if a <= 0 then
                l.on = false; l.tex:Hide()
            else
                any = true
                l.tex:ClearAllPoints()
                l.tex:SetPoint("CENTER", sky, "BOTTOMLEFT", x, y)
                if l.tex.SetRotation then l.tex:SetRotation(l.phase + l.age * l.spin) end
                l.tex:SetAlpha(a)
            end
        end
    end
    if not over and not any then sky:SetScript("OnUpdate", nil); sky:Hide() end
end

local function Sky()
    if not sky then
        sky = CreateFrame("Frame", nil, UIParent)
        sky:SetAllPoints(UIParent)
        sky:SetFrameStrata("BACKGROUND")
        if sky.EnableMouse then sky:EnableMouse(false) end
    end
    sky:Show()
    sky:SetScript("OnUpdate", Fall)
end

function ns.Leaves(button)  -- not tied to on/off: that's the wreaths only
    if not button then return end
    Sky()
    if over == button then return end
    if not over then count, nextAt = 0, clock end                 -- a fresh hover starts again at red
    over = button
end
ns.leaves = leaves

-- a handful of leaves flung out of a button's wreath, in its colour: more for a more efficient spell
function ns.Burst(b, t)
    if db.off or not (b and b.GetCenter) then return end
    local cx, cy = b:GetCenter()
    if not cx then return end
    Sky()
    local k = (b.GetEffectiveScale and sky.GetEffectiveScale) and b:GetEffectiveScale() / sky:GetEffectiveScale() or 1
    for _ = 1, 1 + math.floor(3 * t + 0.5) do  -- one leaf for the worst spell, four for the best: small on purpose
        local l = Leaf()
        local ang = math.random() * 2 * math.pi
        local speed = 25 + math.random() * 20
        l.kind, l.on, l.age = "burst", true, 0
        l.x, l.y = cx * k, cy * k
        l.vx, l.vy = math.cos(ang) * speed, math.sin(ang) * speed + 20
        l.spin, l.phase = (math.random() - 0.5) * 6, math.random() * 6.28
        local size = 8 + math.random() * 4
        l.tex:SetSize(size, size)
        l.tex:SetVertexColor(Colour(t))
        l.tex:Show()
    end
end

local function WreathedButtons()
    local out = {}
    for _, b in ipairs(Buttons()) do
        local r = ns.rank[SpellOf(Slot(b)) or 0]
        if r and b.manabloom and (not b.IsVisible or b:IsVisible()) then out[#out + 1] = { b, r } end
    end
    return out
end

function ns.BurstAll()
    for _, e in ipairs(WreathedButtons()) do ns.Burst(e[1], e[2].t) end
end

-- A cast moves the shared bramble: an efficient one (top quarter for its kind) a stage towards berry, any
-- other a stage back towards seed; the first cast from rest starts at bud. A spell the game seals (in combat
-- it may) can't be judged, so it leaves the bramble as it is; castProbe counts how often that happens.
ns.bramble = nil
local lastCast = 0
-- other addons (Stillwater) listen by putting a function in the global ManabloomEvents; each is called with
-- ("bramble", step, top), step 0 when the bramble has gone. Errors in a listener stay in the listener.
function ns.Announce()
    for _, f in ipairs(ManabloomEvents or {}) do pcall(f, "bramble", ns.bramble or 0, #LADDER) end
end
function ns.Cast(spellID)
    local probe = db.castProbe or { seen = 0, secret = 0, secretInCombat = 0 }
    db.castProbe = probe
    probe.seen = probe.seen + 1
    if Secret(spellID) then
        probe.secret = probe.secret + 1
        if InCombatLockdown and InCombatLockdown() then probe.secretInCombat = probe.secretInCombat + 1 end
        return
    end
    local r = ns.rank[spellID or 0]
    if not r or db.off then return end
    local i = ns.bramble or 0
    ns.bramble = r.t >= IDEAL and math.min(#LADDER, i + 1) or math.max(0, i - 1)
    lastCast = GetTime()
    ns.Style()
    ns.Announce()
    C_Timer.After(REST_AFTER, function()
        if GetTime() - lastCast >= REST_AFTER - 0.05 then ns.bramble = nil; ns.Style(); ns.Announce() end
    end)
end

-- the first login after the calendar's season changes: the old wreaths shed, then the new ones grow in
function ns.Turn()
    if not db or db.season then return end
    local now = SEASONS[tonumber(date("%m"))]
    local was = db.lastSeason
    db.lastSeason = now
    if not was or was == now or db.off then return end
    ns.turning = was
    ns.Style()
    C_Timer.After(0.6, function()
        ns.BurstAll()
        Print(("the season turns: %s gives way to %s."):format(was, now))
    end)
    C_Timer.After(1.4, function() ns.turning = nil; ns.Style() end)
end

local function HasBuff(name)
    -- in combat the aura API itself refuses a tainted caller ("Auras cannot be accessed when secret"), 9 Nov 2026
    if InCombatLockdown and InCombatLockdown() then return nil end
    if C_UnitAuras and C_UnitAuras.GetAuraDataByIndex then
        for i = 1, 40 do
            local a = C_UnitAuras.GetAuraDataByIndex("player", i, "HELPFUL")
            if not a then return false end
            if Secret(a.name) then return nil end  -- secret in combat: leave things as they are
            if a.name == name then return true end
        end
        return false
    end
    if UnitBuff then
        for i = 1, 40 do
            local n = UnitBuff("player", i)
            if Secret(n) then return nil end
            if not n then return false end
            if n == name then return true end
        end
    end
    return false
end
ns.innervate = false

-- a spell just learned: if it's a new rank of one on your bars, say how it compares and sprout the old button
function ns.Learned(id)
    local name = id and SpellName(id)
    if not name then return end
    local amount = ns.Amount(Description(id))
    local mana = Mana(id)
    for oldID, r in pairs(ns.rank) do
        if oldID ~= id and SpellName(oldID) == name then
            db.sprouts = db.sprouts or {}
            db.sprouts[name] = id
            local word = r.kind == "heal" and "healing" or "damage"
            if amount and mana then
                local per = amount / mana
                Print(("%s learned: %.2f %s per mana, %s %s's %.2f. Drag it from your spellbook onto your bar.")
                    :format(FullName(id), per, word, per >= r.per and "up from" or "down from", FullName(oldID), r.per))
            else
                Print(FullName(id) .. " learned. Drag it from your spellbook onto your bar.")
            end
            return
        end
    end
end

-- the hover line: what it does per mana, against the best of its kind
local function Tip(tt, slot)
    local id = SpellOf(slot)
    local r = ns.rank[id or 0]
    if not r then return end  -- the tooltip line stays with the wreaths put away
    ns.Leaves(tt.GetOwner and tt:GetOwner())
    local word = r.kind == "heal" and "healing" or "damage"
    tt:AddLine(("%s |cff7fd07fManabloom|r %.2f %s per mana%s"):format(ns.Leaf(r.t), r.per, word,
        r.t >= 1 and (" (your best " .. word .. ")") or (" (best: " .. (r.best or "?") .. ")")), Colour(r.t))
    local newer = db.sprouts and db.sprouts[SpellName(id) or ""]
    if newer and newer ~= id then
        tt:AddLine("A new rank is in your spellbook: " .. FullName(newer), SPROUT[1], SPROUT[2], SPROUT[3])
    end
    tt:Show()
end

local f = CreateFrame("Frame")
f:RegisterEvent("ADDON_LOADED")
local function OnEvent(event, a1, a2, a3)
    if event == "ADDON_LOADED" then
        if a1 ~= ADDON then return end
        ManabloomDB = ManabloomDB or {}
        db = ManabloomDB
        for _, e in ipairs({ "PLAYER_ENTERING_WORLD", "ACTIONBAR_SLOT_CHANGED", "ACTIONBAR_PAGE_CHANGED",
                             "UPDATE_BONUS_ACTIONBAR", "UPDATE_SHAPESHIFT_FORM", "SPELLS_CHANGED",
                             "LEARNED_SPELL_IN_TAB", "SPELL_TEXT_UPDATE", "PLAYER_LEVEL_UP",
                             "UNIT_POWER_UPDATE", "UNIT_AURA", "UNIT_SPELLCAST_SUCCEEDED", "PLAYER_REGEN_ENABLED" }) do
            pcall(f.RegisterEvent, f, e)  -- not every client has every event
        end
        if GameTooltip and GameTooltip.SetAction then hooksecurefunc(GameTooltip, "SetAction", Tip) end
        return
    end
    if event == "UNIT_POWER_UPDATE" then
        if a1 == "player" and a2 == "MANA" then StyleSoon() end
        return
    elseif event == "UNIT_AURA" then
        if a1 == "player" then
            local on = HasBuff(INNERVATE)
            if on ~= nil and on ~= ns.innervate then
                ns.innervate = on
                ns.Style()
                if on then ns.BurstAll() end  -- the wreaths burst into blossom
            end
        end
        return
    elseif event == "UNIT_SPELLCAST_SUCCEEDED" then
        if a1 == "player" then ns.Cast(a3) end
        return
    elseif event == "LEARNED_SPELL_IN_TAB" then
        ns.Learned(a1)
    elseif event == "PLAYER_ENTERING_WORLD" then
        C_Timer.After(1.5, function() Safely(ns.Turn) end)
    end
    Soon()
end
f:SetScript("OnEvent", function(_, event, a1, a2, a3) Safely(function() OnEvent(event, a1, a2, a3) end) end)

-- the spells on the bars, damage then healing, most efficient first
function ns.Ranked()
    local list = {}
    for id, r in pairs(ns.rank) do
        list[#list + 1] = { name = FullName(id), per = r.per, kind = r.kind, t = r.t }
    end
    table.sort(list, function(a, b) if a.kind ~= b.kind then return a.kind < b.kind end return a.per > b.per end)
    return list
end

SLASH_MANABLOOM1 = "/manabloom"
SlashCmdList.MANABLOOM = function(msg)
    local cmd, arg = (msg or ""):lower():match("^(%S*)%s*(%S*)")
    if cmd == "off" or cmd == "on" then
        db.off = cmd == "off"
        Print(db.off and "wreaths put away" or "wreaths back")
    elseif cmd == "colours" or cmd == "colors" then
        db.colours = arg == "season" and "season" or nil
        Print(db.colours and ("colours follow the season (" .. Season() .. "), worst to best")
            or "colours: red to moonlight white, all year")
    elseif cmd == "opacity" and tonumber(arg) then
        db.opacity = math.max(0, math.min(1, tonumber(arg)))
        Print(("wreath opacity %.2f"):format(db.opacity))
    elseif cmd == "season" then
        local ok = { autumn = true, winter = true, spring = true, summer = true }
        db.season = ok[arg] and arg or nil
        Print("season: " .. (db.season or ("following the calendar (" .. Season() .. ")")))
    else
        for _, e in ipairs(ns.Ranked()) do
            local r, g, b = Colour(e.t)
            Print(("%s |cff%02x%02x%02x%s|r: %.2f %s per mana"):format(ns.Leaf(e.t), r * 255, g * 255, b * 255, e.name, e.per,
                e.kind == "heal" and "healing" or "damage"))
        end
        Print("season " .. Season() .. (db.colours and ", seasonal colours" or "") ..
            ". /manabloom season autumn|winter|spring|summer|auto, colours season|classic, opacity <0-1>, off|on")
    end
    Soon()
end

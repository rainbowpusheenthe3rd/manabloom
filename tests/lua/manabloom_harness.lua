-- Manabloom against a stubbed game: the description parser on Classic druid tooltips (Wowhead's classic tooltips,
-- 9 Nov 2026), then a refresh over a stubbed action bar: ranks within damage and within healing, wreath colours,
-- no wreath for Thorns, and the season by month.
local dir = ...
local ok = 0
local function check(c, msg) assert(c, msg); ok = ok + 1 end
local function near(a, b) return a and math.abs(a - b) < 1e-6 end

local SPELLS = {  -- id -> name, description, mana
    [8921] = { "Moonfire", "Burns the enemy for 9 to 12 Arcane damage and then an additional 12 Arcane damage over 9 sec.", 25 },
    [5176] = { "Wrath", "Causes 13 to 16 Nature damage to the target.", 20 },
    [339] = { "Entangling Roots", "Roots the target in place and causes 20 Nature damage over 12 sec.  Damage caused may interrupt the effect.  Only useable outdoors.", 50 },
    [8936] = { "Regrowth", "Heals a friendly target for 93 to 107 and another 98 over 21 sec.", 120 },
    [774] = { "Rejuvenation", "Heals the target for 32 over 12 sec.", 25 },
    [467] = { "Thorns", "Thorns sprout from the friendly target causing 3 Nature damage to attackers when hit.  Lasts 10 min.", 35 },
    [1126] = { "Mark of the Wild", "Increases the friendly target's armor by 25 for 30 min.", 20 },
}
local ACTIONS = { 8921, 5176, 339, 8936, 774, 467, 1126 }

-- the game, stubbed
local timers, tex = {}, {}
now = 0
function GetTime() return now end
C_Timer = { After = function(_, fn) timers[#timers + 1] = fn end }
local function run() local t = timers; timers = {}; for _, fn in ipairs(t) do fn() end end
C_Spell = {
    GetSpellDescription = function(id) return SPELLS[id] and SPELLS[id][2] end,
    GetSpellPowerCost = function(id) return SPELLS[id] and { { type = 0, name = "MANA", cost = SPELLS[id][3] } } end,
    GetSpellName = function(id) return SPELLS[id] and SPELLS[id][1] end,
    GetSpellSubtext = function(id) return id == 5176 and "Rank 1" or nil end,
}
function GetActionInfo(slot) if ACTIONS[slot] then return "spell", ACTIONS[slot] end end
function wipe(t) for k in pairs(t) do t[k] = nil end return t end
local hooks = {}
function hooksecurefunc(_, name, fn) hooks[name] = fn end
function print() end
local month = "11"
date = function() return month end
local frame
local noop = function() end
local function stub(t) return setmetatable(t, { __index = function() return noop end }) end
local sky, mmb
function CreateFrame(kind)
    local f = stub({ events = {}, scripts = {}, shown = false })
    function f:RegisterEvent(e) self.events[e] = true end
    function f:SetScript(k, fn) self.scripts[k] = fn; if k == "OnEvent" then self.fn = fn end end
    function f:GetWidth() return 1000 end
    function f:GetHeight() return 800 end
    function f:Show() self.shown = true end
    function f:Hide() self.shown = false end
    function f:CreateTexture()
        local t = stub({})
        function t:SetVertexColor(r, g, b) self.rgb = { r, g, b } end
        function t:SetPoint(_, _, _, x, y) self.x, self.y = x, y end
        function t:Show() self.shown = true end
        function t:Hide() self.shown = false end
        function t:SetAlpha(a) self.alpha = a end
        return t
    end
    if kind == "Button" then mmb = f elseif not frame then frame = f else sky = f end  -- events, the minimap button, the sky
    return f
end
UIParent = {}
Minimap = stub({})
function Minimap:GetWidth() return 140 end
function Minimap:GetFrameLevel() return 2 end
local tip = {}
GameTooltip = stub({})
function GameTooltip:AddLine(t) tip[#tip + 1] = t end
function GameTooltip:AddDoubleLine(l, r) tip[#tip + 1] = l .. " | " .. r end
SlashCmdList = {}
local glows, sprouts, norths, souths = {}, {}, {}, {}
for i = 1, 12 do
    local b = { action = i, made = 0 }
    function b:GetWidth() return 40 end
    function b:GetCenter() return 100 * i, 50 end
    function b:CreateTexture()
        local t = stub({ shown = false })
        function t:SetPoint(_, _, _, x, y) self.x, self.y = x, y end
        function t:SetSize(w) self.w = w end
        function t:SetTexture(p) self.tex = p end
        function t:SetVertexColor(r, g, bl) self.rgb = { r, g, bl } end
        function t:SetAlpha(a) self.alpha = a end
        function t:Show() self.shown = true end
        function t:Hide() self.shown = false end
        self.made = self.made + 1
        if self.made == 1 then tex[i] = t elseif self.made == 2 then glows[i] = t
        elseif self.made == 3 then norths[i] = t elseif self.made == 4 then souths[i] = t
        else sprouts[i] = t end  -- wreath, glow, north motif, south motif, sprout
        return t
    end
    _G["ActionButton" .. i] = b
end
local mana, form, buffs = 100, nil, {}
function UnitPower() return mana end
function UnitPowerMax() return 100 end
function GetShapeshiftFormID() return form end
function UnitBuff(_, i) return buffs[i] end

local ns = {}
assert(loadfile(dir .. "/Manabloom.lua"))("Manabloom", ns)
assert(loadfile(dir .. "/Minimap.lua"))("Manabloom", ns)

-- the parser
local a, k = ns.Amount(SPELLS[8921][2]); check(near(a, 22.5) and k == "damage", "Moonfire: 10.5 + 12 more over time")
a, k = ns.Amount(SPELLS[8936][2]); check(near(a, 198) and k == "heal", "Regrowth: 100 + 98 over time")
a = ns.Amount(SPELLS[774][2]); check(near(a, 32), "Rejuvenation: 32, not counting the 12 sec")
a = ns.Amount(SPELLS[339][2]); check(near(a, 20), "Roots: 20, not the 12 sec")
check(ns.Amount(SPELLS[467][2]) == nil, "Thorns: only hurts attackers, no wreath")
check(ns.Amount(SPELLS[1126][2]) == nil, "Mark of the Wild: no damage or healing")
check(near(ns.Amount("Heals for 1,200 to 1,400."), 1300), "thousands separators")
check(ns.Amount("Shapeshift into a bear, increasing melee attack power by 120, armor contribution from items by 180%, and health by 560.") == nil,
    "Bear Form: health is not healing")
check(ns.Amount("Returns the spirit to the body, restoring a dead target to life with 400 health and 700 mana.") == nil,
    "Rebirth and Revive: a life, not a heal")

-- a refresh over the bar
frame.fn(nil, "ADDON_LOADED", "Manabloom")
frame.fn(nil, "PLAYER_ENTERING_WORLD"); run()
check(near(ns.rank[8921].per, 0.9) and near(ns.rank[8921].t, 1), "Moonfire is the best damage per mana (0.9)")
check(near(ns.rank[339].t, 0), "Roots the worst (0.4)")
check(ns.rank[5176].t > 0 and ns.rank[5176].t < 1, "Wrath in between")
check(near(ns.rank[8936].t, 1) and near(ns.rank[774].t, 0), "heals ranked apart: Regrowth 1.65 above Rejuvenation 1.28")
check(tex[1].shown and tex[1].rgb[1] > 0.9 and tex[1].rgb[3] > 0.9, "the best wears moonlight white")
check(tex[3].shown and tex[3].rgb[1] > 0.9 and tex[3].rgb[3] < 0.2, "the worst wears red")
check(tex[6] == nil and tex[7] == nil, "Thorns and Mark get no wreath")
check(tex[1].tex:find("autumn$") and tex[1].w == 60, "November is autumn; the wreath is 1.5 buttons wide")
month = "12"; frame.fn(nil, "SPELLS_CHANGED"); run()
check(tex[1].tex:find("winter$"), "December turns it to winter")
SlashCmdList.MANABLOOM("season spring"); run(); check(tex[1].tex:find("spring$"), "/manabloom season spring")
SlashCmdList.MANABLOOM("off"); run(); check(not tex[1].shown, "/manabloom off puts them away")
local offLines = {}
hooks.SetAction({ GetOwner = function() return { IsMouseOver = function() return false end } end,
    AddLine = function(_, t) offLines[#offLines + 1] = t end, Show = function() end }, 1)
check(offLines[1] and offLines[1]:find("Manabloom"), "with the wreaths away, the tooltip line stays")
check(ns.Leaf(1):find("leaf:14:14:0:0:32:32:0:32:0:32:240:247:255|t$") and ns.Leaf(0):find(":235:41:26|t$"), "the leaf wears the colour")
-- the minimap button: its leaf wears the best colour; hover lists the spells; clicks toggle wreaths and colours
SlashCmdList.MANABLOOM("on"); run()
mmb.scripts.OnEnter(mmb)
local all = table.concat(tip, " / ")
check(all:find("Moonfire | 0.90 dmg") and all:find("Regrowth | 1.65 heal") and all:find("Manabloom"), "hover: the spells by mana efficiency")
check(all:find("Wrath %(Rank 1%)"), "ranks named, so two Wraths can be told apart")
month = "11"; SlashCmdList.MANABLOOM("season auto")
mmb.scripts.OnClick(mmb, "LeftButton"); run(); check(ManabloomDB.season == "winter" and not ManabloomDB.off and tex[1].shown,
    "left-click: the next season, never hiding the wreaths")
for _ = 1, 3 do mmb.scripts.OnClick(mmb, "LeftButton") end; check(ManabloomDB.season == nil, "round to summer, then the calendar's")
IsShiftKeyDown = function() return true end
mmb.scripts.OnClick(mmb, "LeftButton"); run(); check(ManabloomDB.off == true and not tex[1].shown, "shift-click puts the wreaths away")
mmb.scripts.OnClick(mmb, "LeftButton"); run(); check(not ManabloomDB.off and tex[1].shown, "and brings them back")
IsShiftKeyDown = nil
mmb.scripts.OnClick(mmb, "RightButton"); check(ManabloomDB.colours == "season", "right-click: the season's colours")
mmb.scripts.OnClick(mmb, "RightButton"); check(ManabloomDB.colours == nil, "and classic again")

-- the spell's own tooltip gets the coloured line, in classic and seasonal colours alike
local function hover(slot)
    local lines = {}
    local tt = { GetOwner = function() return { IsMouseOver = function() return true end } end,
                 AddLine = function(_, t, r, g, b) lines[#lines + 1] = { t, r, g, b } end, Show = function() end }
    hooks.SetAction(tt, slot)
    return lines[1]
end
month = "11"; SlashCmdList.MANABLOOM("season auto"); SlashCmdList.MANABLOOM("colours classic"); run()
local line = hover(2)
check(line and line[1]:find("best: Moonfire") and line[2] and line[2] > 0.3, "classic: Wrath's tooltip says the best is Moonfire, in colour")
SlashCmdList.MANABLOOM("colours season"); run()
line = hover(2)
check(line and line[1]:find("best: Moonfire") and line[2] > 0.9 and line[3] > 0.4 and line[4] < 0.4,
    "seasonal: the same line, in autumn's orange-gold")
SlashCmdList.MANABLOOM("colours classic"); run()

-- each season's own colours, on request
month = "11"; SlashCmdList.MANABLOOM("season auto"); SlashCmdList.MANABLOOM("on"); SlashCmdList.MANABLOOM("colours season"); run()
check(near(tex[1].rgb[1], 1.00) and near(tex[1].rgb[2], 0.95) and near(tex[3].rgb[1], 0.62) and near(tex[3].rgb[2], 0.10),
    "autumn colours: cream for the best, rust for the worst")
month = "1"; SlashCmdList.MANABLOOM("colours season"); run()
check(near(tex[1].rgb[3], 1.00) and near(tex[1].rgb[1], 0.97), "January: snow for the best")
SlashCmdList.MANABLOOM("colours classic"); run()
check(near(tex[1].rgb[1], 0.94) and near(tex[3].rgb[1], 0.92) and near(tex[3].rgb[2], 0.16), "classic: back to red and moonlight white")
month = "11"

-- falling leaves while the mouse is on a wreathed button
SlashCmdList.MANABLOOM("on"); run()
local mouse = true
local btn = { IsMouseOver = function() return mouse end }
ns.Leaves(btn)
local function step(n) for _ = 1, n do if sky.scripts.OnUpdate then sky.scripts.OnUpdate(sky, 0.25) end end end
local function live() local n = 0; for _, l in ipairs(ns.leaves) do if l.on then n = n + 1 end end; return n end
step(1)
check(sky.shown and #ns.leaves == 1 and ns.leaves[1].tex.rgb[1] > 0.9 and ns.leaves[1].tex.rgb[3] < 0.2, "the first leaf falls, red")
step(12)  -- 3.25 s: leaves at 0.25, 1.25, 2.25 and 3.25
check(live() == 4, "one leaf a second: four in the first 3.25 seconds")
local inBand = true
for _, l in ipairs(ns.leaves) do if l.x > 110 and l.x < 890 then inBand = false end end
check(inBand, "they keep to the left and right edges of the screen")
step(4 * 8)  -- to 11.25 s: the twelfth leaf, the last of the cycle, has just fallen
local last; for _, l in ipairs(ns.leaves) do if l.on and l.age < 0.3 then last = l end end
check(last and last.tex.rgb[1] > 0.9 and last.tex.rgb[3] > 0.9, "the twelfth is moonlight white")
step(4); local again; for _, l in ipairs(ns.leaves) do if l.on and l.age < 0.3 then again = l end end
check(again and again.tex.rgb[1] > 0.9 and again.tex.rgb[3] < 0.2, "then red again")
mouse = false; local before = live(); step(1)
check(live() <= before, "moused off: no new leaves")
step(4); check(live() == 0 and not sky.shown, "and the falling ones fade away")

-- alive: wilting with mana (Roots is button 3, the worst damage; Moonfire button 1, the best)
month = "11"; SlashCmdList.MANABLOOM("on"); SlashCmdList.MANABLOOM("colours classic"); SlashCmdList.MANABLOOM("season auto"); run()
mana = 100; ns.Style()
check(tex[3].alpha == 1 and not glows[1].shown, "full mana: no wilting, no glow")
mana = 5; ns.Style()
check(tex[3].alpha < 0.7 and tex[3].y < 0 and tex[1].alpha == 1 and glows[1].shown and glows[1].alpha > 0.3,
    "low mana: the worst wilts and sags, the best glows")
check(tex[3].rgb[1] < 0.8, "and the wilting one goes brown")
mana = 100; ns.Style(); check(tex[3].alpha == 1 and not glows[1].shown, "mana back: it recovers")

-- secret mana (the Forever client, 9 Nov): any arithmetic or comparison on it is an error, as in game
local SECRET = setmetatable({}, { __div = function() error("attempt to perform arithmetic on a secret number value") end,
    __lt = function() error("attempt to compare a secret value") end, __le = function() error("secret") end })
function issecretvalue(v) return v == SECRET end
UnitPower = function() return SECRET end
local ok2, err2 = pcall(ns.Style)
check(ok2, "secret mana: no error (it was 'arithmetic on a secret number value'): " .. tostring(err2))
check(tex[3].shown and tex[3].alpha == 1 and tex[1].alpha == 1, "every wreath stays fully drawn")
check(not glows[1].shown, "and no glow: there's no wilting while mana is secret")
frame.fn(nil, "UNIT_SPELLCAST_SUCCEEDED", "player", "guid", SECRET)
check(ns.bramble == nil and ManabloomDB.castProbe.secret == 1, "a secret spell ID: the bramble is left alone, and counted")
UnitPower = function() return mana end
issecretvalue = nil
mana = 100; ns.Style()

-- forms
form = 31; ns.Style(); check(tex[1].rgb[1] > 0.88 and tex[1].rgb[1] < 0.93, "Moonkin: starlit silver")
form = 5; ns.Style(); check(tex[1].alpha < 0.4 and tex[1].w < 60, "bear: curled shut")
form = nil; ns.Style()

-- Innervate
buffs = { "Innervate" }; frame.fn(nil, "UNIT_AURA", "player")
check(tex[1].tex:find("spring$") and ns.innervate, "Innervate: spring blossom")
buffs = {}; frame.fn(nil, "UNIT_AURA", "player"); check(tex[1].tex:find("autumn$"), "and autumn again when it ends")
step(8)

-- the shared bramble: Moonfire (8921) is the best damage, Roots (339) the worst
local cast = function(id) frame.fn(nil, "UNIT_SPELLCAST_SUCCEEDED", "player", "guid", id) end
local function shows(i)  -- what button i's motifs show, "north/south", "-" for nothing
    local n = norths[i].shown and norths[i].tex:match("motif_([%w_]+)$") or "-"
    local so = souths[i].shown and souths[i].tex:match("motif_([%w_]+)$") or "-"
    return n .. "/" .. so
end
local ladder = { "bud/-", "bud/bud", "flower/bud", "flower/flower", "berry/flower", "berry/berry" }
local climbed = true
for step = 1, 6 do cast(8921); climbed = climbed and shows(1) == ladder[step] and shows(3) == ladder[step] end
check(climbed, "six efficient casts climb the ladder on every wreath: bud, two buds ... two berries")
check(norths[1].rgb[1] == 1 and norths[3].rgb[1] == 1, "the motifs keep their own colours, untinted")
check(tex[1].tex:find("autumn$") and tex[1].shown, "over the season's wreath, which stays")
cast(8921); check(shows(1) == "berry/berry", "and it stays at two berries")
cast(339); check(shows(1) == "berry/flower", "a poor cast steps it back")
for _ = 1, 6 do cast(339) end; check(shows(1) == "-/-" and ns.bramble == 0, "down to nothing, no further")
now = now + 9; run(); check(ns.bramble == nil and shows(1) == "-/-", "quiet for a few seconds: it rests")
-- Wrath (5176) sits between: on these bars it's in the better half, so it ripens (the ideal is the better half)
cast(5176); check(ns.bramble == (ns.rank[5176].t >= 0.5 and 1 or 0), "the middle of the scale follows the better-half rule")
now = now + 9; run()

-- the turn of the season
ManabloomDB.lastSeason = "autumn"; month = "12"; ns.Turn()
check(tex[1].tex:find("autumn$"), "first login in December: the autumn wreaths stay a moment")
run(); check(tex[1].tex:find("winter$") and ManabloomDB.lastSeason == "winter", "then they shed, and winter grows in")
step(8); month = "11"; ManabloomDB.lastSeason = nil; ns.Style()

-- a new rank
SPELLS[5177] = { "Wrath", "Causes 28 to 33 Nature damage to the target.", 35 }
local said = {}
print = function(m) said[#said + 1] = m end
frame.fn(nil, "LEARNED_SPELL_IN_TAB", 5177); run()
check(ManabloomDB.sprouts.Wrath == 5177 and sprouts[2] and sprouts[2].shown, "a new rank of Wrath: a sprout on the old one")
check(said[1] and said[1]:find("up from"), "and it says the new rank is better per mana")
ACTIONS[2] = 5177; frame.fn(nil, "ACTIONBAR_SLOT_CHANGED"); run()
check(ManabloomDB.sprouts.Wrath == nil and not sprouts[2].shown, "on the bar now: the sprout goes")
-- mid-fight the game briefly gives no text for a spell: the wreaths must stay (they vanished at berries, 9 Nov)
SlashCmdList.MANABLOOM("on"); run()
local realDesc = C_Spell.GetSpellDescription
InCombatLockdown = function() return true end
C_Spell.GetSpellDescription = function() return nil end
frame.fn(nil, "ACTIONBAR_SLOT_CHANGED", 1); run()
check(tex[1].shown and tex[3].shown and ns.rank[8921], "in combat, a re-rank with missing spell text keeps every wreath")
check((ManabloomDB.combatSkips or 0) >= 1, "and the skipped re-rank is counted")
C_Spell.GetSpellDescription = realDesc
InCombatLockdown = function() return false end
frame.fn(nil, "PLAYER_REGEN_ENABLED"); run()
check(tex[1].shown and ns.rank[8921], "after combat it re-ranks, wreaths still there")
InCombatLockdown = nil

-- other classes' spell text (Wowhead's classic tooltips, 12 Nov 2026)
local function amt(s) return ns.Amount(s) end
a, k = amt("Draws on the soul of the party member to shield them, absorbing 48 damage.  Lasts 30 sec.  While the shield holds, spellcasting will not be interrupted by damage.  Once shielded, the target cannot be shielded again for 15 sec.")
check(near(a, 48) and k == "heal", "Power Word: Shield: a shield counts as healing, 48")
check(amt("Absorbs 120 physical damage, draining mana instead.  Drains 2 mana per damage absorbed.  Lasts 1 min.") == nil,
    "Mana Shield pays in absorbed mana: no wreath")
check(amt("Summons a Stoneskin Totem with 5 health at the feet of the caster.  The totem protects party members within 20 yards, reducing melee damage taken by 4.  Lasts 2 min.") == nil,
    "Stoneskin Totem only reduces damage taken: no wreath")
a, k = amt("Summons a Searing Totem with 5 health at your feet for 30 sec that repeatedly attacks an enemy within 20 yards for 9 to 11 Fire damage.")
check(near(a, 10) and k == "damage", "Searing Totem: 10, not counting the totem's own 5 health")
a, k = amt("Summons a Healing Stream Totem with 5 health at the feet of the caster for 1 min that heals group members within 20 yards for 6 every 2 seconds.")
check(near(a, 180) and k == "heal", "Healing Stream Totem: 6 every 2 seconds for 1 min is 180")
a, k = amt("Launches Arcane Missiles at the enemy, causing 26 Arcane damage each second for 3 sec.")
check(near(a, 78) and k == "damage", "Arcane Missiles: 26 each second for 3 sec is 78")
a, k = amt("Ignites the area surrounding the caster, causing 87 Fire damage to himself and 87 Fire damage to all nearby enemies every 1 sec.  Lasts 15 sec.")
check(near(a, 1305) and k == "damage", "Hellfire: 87 a second for 15 sec to enemies, not the caster's own")
a, k = amt("Transfers 10 health every second from the target to the caster.  Lasts 5 sec.")
check(near(a, 50) and k == "damage", "Drain Life: 10 a second for 5 sec, as damage")
a, k = amt("Regenerates all nearby group members for 98 every 2 seconds for 10 sec.  Druid must channel to maintain the spell.")
check(near(a, 490) and k == "heal", "Tranquility: 98 every 2 seconds for 10 sec is 490 healing")
check(amt("Converts 30 health into 30 mana.") == nil, "Life Tap: neither damage nor healing")
a, k = amt("Heals the target of 45 damage over 15 sec.")
check(near(a, 45) and k == "heal", "Renew: healing, though it says damage")

-- each class's own ladder on the wreaths
check(ns.Motifs()[1] == "bud", "no class known: the bramble")
for class, first in pairs({ PRIEST = "priest_1", MAGE = "mage_1", WARLOCK = "warlock_1", SHAMAN = "shaman_1",
                            PALADIN = "paladin_1", HUNTER = "hunter_1", DRUID = "bud", WARRIOR = "bud" }) do
    UnitClass = function() return "x", class end
    check(ns.Motifs()[1] == first, class .. "'s ladder starts at " .. first)
end
UnitClass = function() return "Priest", "PRIEST" end
for _ = 1, 3 do cast(8921) end
check(shows(1) == "priest_2/priest_1", "a priest's third step: flame north, candle south")
for _ = 1, 3 do cast(8921) end
check(shows(1) == "priest_3/priest_3", "and the top: two haloes")
now = now + 9; run()
UnitClass = nil
return ok

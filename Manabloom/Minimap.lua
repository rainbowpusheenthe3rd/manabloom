-- A small button on the edge of the minimap, like Shan'do's: half opacity, full when you point at it.
-- The oak leaf on it wears your best spell's colour (this season's, if the colours follow the season).
-- Hover: your spells by mana efficiency, and a few leaves fall. Left-click: the next season (then back to the
-- calendar's). Right-click: classic colours or the season's. Shift-click: wreaths on or off (a stray plain click
-- once hid them all, 9 Nov 2026, so hiding takes a shift). Drag: move it round the edge (kept per character).
local CYCLE = { autumn = "winter", winter = "spring", spring = "summer", summer = "auto" }
local _, ns = ...
local DIR = "Interface\\AddOns\\Manabloom\\"
local REST = 0.5

local b = CreateFrame("Button", "ManabloomMinimapButton", Minimap)
b:SetSize(24, 24)
b:SetFrameStrata("MEDIUM")
b:SetFrameLevel(Minimap:GetFrameLevel() + 8)
b:SetAlpha(REST)
b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
b:RegisterForDrag("LeftButton")
local disc = b:CreateTexture(nil, "BACKGROUND")
disc:SetAllPoints()
disc:SetTexture(DIR .. "disc")
local leaf = b:CreateTexture(nil, "ARTWORK")
leaf:SetPoint("CENTER")
leaf:SetSize(16, 16)
leaf:SetTexture(DIR .. "leaf")

local function Place(angle)
    local r = Minimap:GetWidth() / 2 + 6
    b:ClearAllPoints()
    b:SetPoint("CENTER", Minimap, "CENTER", r * math.cos(math.rad(angle)), r * math.sin(math.rad(angle)))
end

function ns.MinimapLook()
    local db = ManabloomDB or {}
    leaf:SetVertexColor(ns.Colour(1))
    leaf:SetDesaturated(db.off and true or false)
end

b:SetScript("OnEnter", function(self)
    self:SetAlpha(1)
    local db = ManabloomDB or {}
    GameTooltip:SetOwner(self, "ANCHOR_LEFT")
    GameTooltip:AddLine(ns.Leaf(1) .. " |cff7fd07fManabloom|r")
    if db.off then GameTooltip:AddLine("Wreaths put away: shift-click to bring them back", 1, 0.5, 0.3) end
    GameTooltip:AddLine(("%s%s, %s colours"):format(ns.Season(), db.season and "" or " (the calendar's)",
        db.colours and "seasonal" or "classic"), 0.7, 0.7, 0.7)
    for _, e in ipairs(ns.Ranked()) do
        GameTooltip:AddDoubleLine(ns.Leaf(e.t) .. " " .. e.name, ("%.2f %s"):format(e.per, e.kind == "heal" and "heal" or "dmg"),
            1, 1, 1, ns.Colour(e.t))
    end
    GameTooltip:AddLine("Left-click: next season", 1, 1, 1)
    GameTooltip:AddLine("Right-click: classic or seasonal colours", 1, 1, 1)
    GameTooltip:AddLine("Shift-click: wreaths on or off", 1, 1, 1)
    GameTooltip:AddLine("Drag: move this button", 0.7, 0.7, 0.7)
    GameTooltip:Show()
    ns.Leaves(self)
end)
b:SetScript("OnLeave", function(self) self:SetAlpha(REST) GameTooltip:Hide() end)
b:SetScript("OnClick", function(self, button)
    local db = ManabloomDB or {}
    if IsShiftKeyDown and IsShiftKeyDown() then
        SlashCmdList.MANABLOOM(db.off and "on" or "off")
    elseif button == "RightButton" then
        SlashCmdList.MANABLOOM(db.colours and "colours classic" or "colours season")
    else
        SlashCmdList.MANABLOOM("season " .. (CYCLE[ns.Season()] or "auto"))
    end
    ns.MinimapLook()
    if self:IsMouseOver() then self:GetScript("OnEnter")(self) end  -- the tooltip shows the change at once
end)
b:SetScript("OnDragStart", function(self)
    self:SetScript("OnUpdate", function()
        local mx, my = Minimap:GetCenter()
        local cx, cy = GetCursorPosition()
        local s = Minimap:GetEffectiveScale()
        ManabloomDB.map = math.deg(math.atan2(cy / s - my, cx / s - mx))
        Place(ManabloomDB.map)
    end)
end)
b:SetScript("OnDragStop", function(self) self:SetScript("OnUpdate", nil) end)

b:RegisterEvent("PLAYER_LOGIN")
b:SetScript("OnEvent", function() Place((ManabloomDB or {}).map or 235) ns.MinimapLook() end)

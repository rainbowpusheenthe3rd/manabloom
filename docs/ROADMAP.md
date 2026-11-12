# Manabloom roadmap

## 1.0 (public repo up 9 Nov 2026; the GitHub release and CurseForge upload are the author's to do)

The bramble ladder (bud → flower → berry, two motifs per wreath, six steps) in every season.

## 1.1: a ladder of its own for each class (12 Nov 2026)

The flat class ladders chosen on 10 Nov 2026 (tools/manabloom_pivot_draft.py), exported by
tools/manabloom_class_motifs.py. Still to check in game: each class at bar size, especially the hunter's
arrow against its drawn bow and the shaman's dark storm cloud, the weakest steps on the bar-size check sheet.

## Later: a ladder of its own for each season (the author, 9 Nov 2026)

Each season gets something unique and **just as readable** as the bramble ladder: natural colours, distinct in
hue, lightness and shape at bar size (about 23 px a motif), two slots north then south, six steps. Following the
bramble's real year (its flowering May–August and fruit about 55 days after pollination are in Albia's
`content/base/agents/bramble.toml`):

| Season | Ladder |
|---|---|
| Spring | leaf growth: a leaf bud breaks, a leaf unfolds, then a full compound leaf |
| Summer | bud → flower → berry (the 1.0 ladder moves here) |
| Autumn | leaves turn: green → red → brown, then fall |
| Winter | frost instead of plants: a seed crystal → needles → a full ice star |

Check each set at bar size against every efficiency colour before shipping, the way the 1.0 set was.

## Still to check in game

- Combat casts are not sealed: the cast counter saw 275 casts, 0 sealed (9 Nov 2026), so the ladder works in combat.
- Retail: the TOC lists its interface version, but it has only been played on Forever.
- Moonkin: change what is shown (night-opening flowers) rather than recolouring.

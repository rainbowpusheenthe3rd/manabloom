# Changelog

All notable changes to Manabloom are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [1.2.1] - 2026-11-20

### Fixed

- The cast bar no longer shows the first damage cast or two in gold, the colour for other spells. Each spell's kind is now remembered by name, so it stays right even when the game briefly drops the spell from its rank list.

## [1.2.0] - 2026-11-15

### Added

- The cast bar grows your class's own ladder, for every class that casts with mana. The first stage waits ahead of the fill, the second opens as the fill passes, and the third blooms at the end of a finished cast.
  - Priest: candle, flame, halo.
  - Mage: spark, glyph, crystal.
  - Warlock: ember, fel flame, soul shard.
  - Shaman: pebble, wave, storm.
  - Paladin: dim, glowing and radiant seal.
  - Hunter: flint point, fletched arrow, drawn bow.
  - Druid: the season's flowers, as before.
- The heal and damage colours and your race's border are unchanged. The class art keeps its own colours, leaning violet for damage.

## [1.1.0] - 2026-11-15

### Added

- Every mana class grows its own ladder on the wreaths, three stages climbed two at a time like the druid's
  bramble: priest candle to halo, mage spark to crystal, warlock ember to soul shard, shaman pebble to storm,
  paladin dim to radiant seal, hunter flint point to drawn bow.
- A cast bar that flowers: a 1 px border and a dark green fill, five of the season's flowers opening as the fill
  reaches them, and a full bloom at the end of a completed cast. White for heals, violet for damage; an interrupted
  cast wilts. The border wears your race's homeland colour, faint at rest and lit beside the fill as it goes. `/manabloom castbar on|off`, or
  Ctrl-click the minimap button.

### Fixed

- Shields count as healing (Power Word: Shield), not damage.
- Spells that tick "every 2 seconds" or "each second" count over their whole duration (Arcane Missiles,
  Hellfire, Healing Stream Totem, Tranquility, Drain Life, Mend Pet), not just one tick.
- A totem's own health no longer counts as what it does, and Hellfire's damage to the caster is left out.
- Tranquility ("Regenerates") gets a wreath; Drain Life counts as damage.
- Stoneskin Totem ("damage taken") and Mana Shield (paid for in absorbed mana) get no wreath.

## [1.0.0] - 2026-11-09

First release, for World of Warcraft: Forever (interface 16001).

### Added

- A seasonal wreath round each action button, coloured by mana efficiency: lighter for more damage or healing per
  mana. Damage and heals are ranked separately.
- Four seasonal wreaths that follow the calendar: spring vine and blossom, summer oxeye daisies, autumn oak and
  acorns, winter frost. Seasonal or classic colours.
- A bramble on every wreath that ripens from bud to flower to berry on efficient casts and steps back on poor ones.
- A tooltip line on each spell with its damage or healing per mana and your best spell of its kind.
- Leaves falling down the screen's edges while you hover a spell.
- A minimap button: spells ranked by efficiency, season and colour switching, wreaths on or off.
- Form, Innervate and new-rank touches: starlit Moonkin, no wreaths for cat and bear abilities, spring blossom
  during Innervate, and a sprout when a better rank is waiting in your spellbook.

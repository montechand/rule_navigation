# Review: grp_ibsrela_design_pattern_rules_02

doc_ref: `design_pattern_rules[2]`

## Original text

````
### Callout styles (explicit)
- **Rounded rectangle with white outline** (transparent fill) → reserved for key strategic questions (e.g., the "DO YOU WANT TO TRY SOMETHING DIFFERENT?" ask).
- **White banner callout at 80% opacity over background** → for the "IBSRELA WORKS DIFFERENTLY…" claim.
- Scene-paired banner callouts over white backgrounds: **Periwinkle @ 80% opacity** for Office-scene pieces; **Purple @ 60% opacity** for Cafe-scene pieces; **Green @ 40% opacity** for Soccer-scene pieces. These pairings are fixed — do not mix scene and color.
````

## Extracted rules (6)

### rule_ibsrela_callout_rounded_rect_white_outline_reserved
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=exclusivity
- rule_text: The rounded rectangle callout with a white outline and transparent fill is reserved for key strategic questions (e.g., the 'DO YOU WANT TO TRY SOMETHING DIFFERENT?' ask).
- intent: Preserve the distinct visual signal of strategic-question callouts.

### rule_ibsrela_callout_white_banner_80_works_differently
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=exclusivity
- rule_text: The white banner callout at 80% opacity over the background is used for the 'IBSRELA WORKS DIFFERENTLY…' claim.
- intent: Bind the white 80% banner treatment to the differentiation claim.

### rule_ibsrela_callout_periwinkle_80_office_scene
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['callout'] constraint=pairing
- rule_text: For scene-paired banner callouts over white backgrounds, Office-scene pieces use Periwinkle (#7B7BED) at 80% opacity.
- intent: Enforce fixed scene-to-color pairing for Office scenes.

### rule_ibsrela_callout_purple_60_cafe_scene
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['callout'] constraint=pairing
- rule_text: For scene-paired banner callouts over white backgrounds, Cafe-scene pieces use Purple (#92278F) at 60% opacity.
- intent: Enforce fixed scene-to-color pairing for Cafe scenes.

### rule_ibsrela_callout_green_40_soccer_scene
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['callout'] constraint=pairing
- rule_text: For scene-paired banner callouts over white backgrounds, Soccer-scene pieces use Green (#01A47E) at 40% opacity.
- intent: Enforce fixed scene-to-color pairing for Soccer scenes.

### rule_ibsrela_callout_scene_color_no_mixing
- class=color_application scope=campaign hardness=hard_constraint polarity=must_not sections=['callout'] constraint=None
- rule_text: The scene-paired banner callout color pairings (Office→Periwinkle 80%, Cafe→Purple 60%, Soccer→Green 40%) are fixed — do not mix scene and color.
- intent: Prevent cross-pairing of scene imagery and callout color.

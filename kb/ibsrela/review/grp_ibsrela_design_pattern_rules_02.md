# Review: grp_ibsrela_design_pattern_rules_02

doc_ref: `design_pattern_rules[2]`

## Original text

````
### Callout styles (explicit)
- **Rounded rectangle with white outline** (transparent fill) → reserved for key strategic questions (e.g., the "DO YOU WANT TO TRY SOMETHING DIFFERENT?" ask).
- **White banner callout at 80% opacity over background** → for the "IBSRELA WORKS DIFFERENTLY…" claim.
- Scene-paired banner callouts over white backgrounds: **Periwinkle @ 80% opacity** for Office-scene pieces; **Purple @ 60% opacity** for Cafe-scene pieces; **Green @ 40% opacity** for Soccer-scene pieces. These pairings are fixed — do not mix scene and color.
````

## Extracted rules (3)

### rule_ibsrela_key_question_callout_style
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=exclusivity
- rule_text: The rounded-rectangle callout with white outline and transparent fill (callout.key_question.border) is reserved for key strategic questions, e.g. the 'DO YOU WANT TO TRY SOMETHING DIFFERENT?' ask.
- intent: Reserve the white-outline callout device for the single key strategic question.

### rule_ibsrela_white_banner_works_differently_callout
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=exclusivity
- rule_text: The white banner callout at 80% opacity over background (callout.white_banner.opacity) is used for the 'IBSRELA WORKS DIFFERENTLY…' claim.
- intent: Standardize the white-banner treatment for the primary differentiation claim.

### rule_ibsrela_scene_paired_banner_callouts
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['callout'] constraint=pairing
- rule_text: Scene-paired banner callouts over white backgrounds use fixed scene/color/opacity pairings: Periwinkle @ 80% opacity for Office-scene pieces; Purple @ 60% opacity for Cafe-scene pieces; Green @ 40% opacity for Soccer-scene pieces (callout.scene_banner.color / callout.scene_banner.opacity). These pairings are fixed — do not mix scene and color.
- intent: Lock each Flip The Script scene to its designated banner color and opacity.

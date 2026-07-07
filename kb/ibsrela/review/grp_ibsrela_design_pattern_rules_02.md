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

### rule_ibsrela_callout_key_question_white_outline
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=exclusivity
- rule_text: The rounded rectangle with white outline and transparent fill (callout.key_question.border) is reserved for key strategic questions, e.g., the 'DO YOU WANT TO TRY SOMETHING DIFFERENT?' ask.
- intent: Reserve the white-outline callout device for high-level strategic questions.

### rule_ibsrela_callout_white_banner_claim
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=exclusivity
- rule_text: The white banner callout at 80% opacity over the background (callout.white_banner.opacity) is used for the 'IBSRELA WORKS DIFFERENTLY…' claim.
- intent: Assign the 80%-opacity white banner treatment to the works-differently claim.

### rule_ibsrela_callout_scene_paired_banner_colors
- class=color_application scope=campaign hardness=hard_constraint polarity=must_not sections=['callout'] constraint=pairing
- rule_text: Scene-paired banner callouts over white backgrounds use fixed scene-to-color pairings: Periwinkle @ 80% opacity for Office-scene pieces; Purple @ 60% opacity for Cafe-scene pieces; Green @ 40% opacity for Soccer-scene pieces (callout.scene_banner.fill / callout.scene_banner.opacity variants carry the per-scene values). These pairings are fixed — do not mix scene and color.
- intent: Lock each scene to its designated banner-callout color/opacity so scene and color never mix.

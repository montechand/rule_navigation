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

### rule_ibsrela_callout_strategic_question_white_outline
- class=color_application scope=brand hardness=strong_default polarity=must sections=['callout'] constraint=exclusivity
- rule_text: The rounded-rectangle callout with white outline and transparent fill (callout.strategic_question.border) is reserved for key strategic questions, e.g. the 'DO YOU WANT TO TRY SOMETHING DIFFERENT?' ask.
- intent: Reserve a distinct callout treatment for the strategic-question device.

### rule_ibsrela_callout_white_banner_claim
- class=color_application scope=brand hardness=strong_default polarity=should sections=['callout'] constraint=binding
- rule_text: The white banner callout at 80% opacity over the background (callout.white_banner.opacity) is used for the 'IBSRELA WORKS DIFFERENTLY…' claim.
- intent: Pair the semi-transparent white banner treatment with the works-differently claim.

### rule_ibsrela_callout_scene_banner_color_pairings
- class=color_application scope=campaign hardness=hard_constraint polarity=must_not sections=['callout'] constraint=pairing
- rule_text: Scene-paired banner callouts over white backgrounds use fixed scene→color pairings: Periwinkle @ 80% opacity for Office-scene pieces; Purple @ 60% opacity for Cafe-scene pieces; Green @ 40% opacity for Soccer-scene pieces (callout.scene_banner.fill / callout.scene_banner.opacity). These pairings are fixed — do not mix scene and color.
- intent: Lock each scene to its assigned callout color/opacity so scenes and colors are never mixed.

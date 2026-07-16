# Review: grp_lisraya_other_rules_00

doc_ref: `other_rules[0]`

## Original text

````
 ### Accessibility (brand-mandated)
- Body copy **≥16px**; bigger is better.
- Line height **≥150%**; more for light-on-dark text.
- Use a type scale for visual hierarchy.
- Test contrast; never rely on color alone; proof all text for legibility.
- Forms: labels always visible (no placeholder-as-label, no disappearing labels); click/tap targets **≥48px**.
- Animations: quick transitions that don't interrupt flow; avoid excessive motion; provide a way to "pause" effects; design for phone, tablet, and desktop. **[GENERAL email]:** animated GIFs must carry the key message in frame 1 (Outlook shows only the first frame); no autoplaying motion longer than ~5s without a static fallback.
- Media: descriptive **alt text** on all images; transcripts available for any video or audio.
- Reference standard: WCAG (wcag.com).
````

## Extracted rules (5)

### rule_lisraya_body_copy_min_size_and_type_scale
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Body copy must be ≥16px (bigger is better), line height ≥150% (more for light-on-dark text), and a type scale must be used for visual hierarchy.
- intent: Ensure legibility and clear visual hierarchy per brand accessibility mandate.

### rule_lisraya_contrast_and_color_independence
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=None governance=regulatory/requires_qualifier
- rule_text: Test contrast, never rely on color alone to convey meaning, and proof all text for legibility. Reference standard is WCAG (wcag.com).
- intent: Meet WCAG accessibility for contrast and non-color-dependent meaning.

### rule_lisraya_forms_labels_and_tap_targets
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Form labels must always be visible (no placeholder-as-label, no disappearing labels); click/tap targets must be ≥48px.
- intent: Ensure accessible, usable form interactions across devices.

### rule_lisraya_media_alt_text_and_transcripts
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=None governance=regulatory/requires_qualifier
- rule_text: Descriptive alt text must be provided on all images, and transcripts must be available for any video or audio.
- intent: Ensure media is accessible to assistive technologies.

### rule_lisraya_motion_and_animation_constraints
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Use quick transitions that don't interrupt flow; avoid excessive motion; provide a way to pause effects; design for phone, tablet, and desktop. For email, animated GIFs must carry the key message in frame 1 (Outlook shows only the first frame), and no autoplaying motion may run longer than ~5s (motion.gif.max_duration_5s) without a static fallback.
- intent: Prevent motion accessibility issues and email-client GIF limitations.

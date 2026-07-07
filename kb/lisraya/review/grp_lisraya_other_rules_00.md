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

## Extracted rules (6)

### rule_lisraya_min_body_size_and_line_height
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Body copy must be at least 16px (bigger is better) and line height at least 150% (line_height.body.min_150), with more line height for light-on-dark text. Use a type scale to establish visual hierarchy.
- intent: Ensure legibility and readable hierarchy per accessibility mandate.

### rule_lisraya_contrast_not_color_alone
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Test contrast (meeting WCAG AA body 4.5:1 and large text 3:1); never rely on color alone to convey meaning; proof all text for legibility.
- intent: Guarantee perceivable text/color for all users.

### rule_lisraya_forms_visible_labels_touch_targets
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Form labels must always be visible — no placeholder-as-label and no disappearing labels. Click/tap targets must be at least 48px.
- intent: Keep interactive elements usable and labels persistent.

### rule_lisraya_animation_motion_constraints
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Animations must use quick transitions that don't interrupt flow, avoid excessive motion, provide a way to pause effects, and be designed responsively for phone, tablet, and desktop. No autoplaying motion longer than ~5s without a static fallback.
- intent: Prevent motion-based accessibility barriers across devices.

### rule_lisraya_email_animated_gif_first_frame
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: [GENERAL email] Animated GIFs must carry the key message in frame 1, because Outlook shows only the first frame.
- intent: Guarantee message delivery where only the first GIF frame renders.

### rule_lisraya_media_alt_text_and_transcripts
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding governance=regulatory/requires_qualifier
- rule_text: All images must carry descriptive alt text, and transcripts must be available for any video or audio. Reference standard: WCAG (wcag.com).
- intent: Provide text alternatives for non-text media per WCAG.

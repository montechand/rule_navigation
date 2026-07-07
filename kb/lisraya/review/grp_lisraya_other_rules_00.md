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

### rule_lisraya_body_copy_min_size_line_height
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Body copy must be ≥16px (bigger is better) and line height must be ≥150%, with more line height for light-on-dark text. Use a type scale for visual hierarchy.
- intent: Ensure legible, accessible body text.

### rule_lisraya_contrast_and_color_reliance
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Test contrast against WCAG AA minimums; never rely on color alone to convey meaning; proof all text for legibility. Reference standard: WCAG (wcag.com).
- intent: Meet WCAG AA and avoid color-only communication.

### rule_lisraya_form_labels_and_touch_targets
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Form labels must always be visible (no placeholder-as-label, no disappearing labels). Click/tap targets must be ≥48px.
- intent: Ensure usable forms and touch targets.

### rule_lisraya_motion_and_animation
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Use quick transitions that don't interrupt flow; avoid excessive motion; provide a way to 'pause' effects; design for phone, tablet, and desktop. No autoplaying motion longer than ~5s without a static fallback.
- intent: Prevent disruptive or inaccessible motion.

### rule_lisraya_email_animated_gif_first_frame
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: [GENERAL email] Animated GIFs must carry the key message in frame 1 (Outlook shows only the first frame).
- intent: Ensure key message survives email clients that render only the first GIF frame.

### rule_lisraya_image_alt_text_and_transcripts
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: Provide descriptive alt text on all images; transcripts must be available for any video or audio.
- intent: Ensure media is accessible to assistive technology.

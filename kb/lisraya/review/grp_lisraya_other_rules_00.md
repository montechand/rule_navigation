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

## Extracted rules (10)

### rule_lisraya_body_copy_min_16px
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Body copy must be at least 16px; bigger is better.
- intent: Ensure readable body text for accessibility.

### rule_lisraya_line_height_min_150
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Line height must be at least 150%; use more for light-on-dark text.
- intent: Maintain legibility and spacing in text.

### rule_lisraya_use_type_scale_hierarchy
- class=accessibility scope=org_baseline hardness=strong_default polarity=should sections=None constraint=None
- rule_text: Use a type scale for visual hierarchy.
- intent: Establish clear visual hierarchy through consistent type sizing.

### rule_lisraya_contrast_not_color_alone
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: Test contrast; never rely on color alone to convey information; proof all text for legibility.
- intent: Ensure information is perceivable regardless of color perception.

### rule_lisraya_form_labels_always_visible
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Forms: labels must always be visible (no placeholder-as-label, no disappearing labels).
- intent: Keep form fields understandable and accessible.

### rule_lisraya_tap_target_min_48px
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=cardinality
- rule_text: Click/tap targets must be at least 48px.
- intent: Ensure interactive targets are large enough for touch accessibility.

### rule_lisraya_animation_motion_guidance
- class=accessibility scope=org_baseline hardness=strong_default polarity=should sections=None constraint=None
- rule_text: Animations should use quick transitions that don't interrupt flow; avoid excessive motion; provide a way to 'pause' effects; design for phone, tablet, and desktop.
- intent: Prevent motion from harming usability or triggering discomfort.

### rule_lisraya_gif_key_message_frame1
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: [GENERAL email] Animated GIFs must carry the key message in frame 1 (Outlook shows only the first frame); no autoplaying motion longer than ~5s without a static fallback.
- intent: Guarantee the key message survives clients that render only the first GIF frame.

### rule_lisraya_alt_text_and_transcripts
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: Media: descriptive alt text is required on all images; transcripts must be available for any video or audio.
- intent: Ensure non-text media is accessible to assistive technology.

### rule_lisraya_reference_standard_wcag
- class=accessibility scope=org_baseline hardness=strong_default polarity=should sections=None constraint=None
- rule_text: Reference standard for accessibility is WCAG (wcag.com).
- intent: Anchor accessibility decisions to an authoritative standard.

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

## Extracted rules (7)

### rule_lisraya_accessible_body_type_legibility
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Body copy must be at least 16px (bigger is better) with line height at least 150% (more for light-on-dark text). Use a type scale for visual hierarchy and proof all text for legibility.
- intent: Guarantee readable body text for patient audiences.

### rule_lisraya_accessible_contrast_not_color_alone
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Test contrast and never rely on color alone to convey information.
- intent: Ensure information is perceivable regardless of color perception.

### rule_lisraya_accessible_forms_labels_targets
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Forms must keep labels always visible — no placeholder-as-label and no disappearing labels. Click/tap targets must be ≥48px.
- intent: Ensure forms and interactive targets are usable and accessible.

### rule_lisraya_accessible_motion_animation
- class=accessibility scope=brand hardness=strong_default polarity=must sections=None constraint=binding
- rule_text: Use quick transitions that don't interrupt flow; avoid excessive motion; provide a way to 'pause' effects; and design responsively for phone, tablet, and desktop. No autoplaying motion longer than ~5s without a static fallback.
- intent: Prevent motion from harming usability or accessibility.

### rule_lisraya_email_gif_key_message_frame_one
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: [GENERAL email] Animated GIFs must carry the key message in frame 1, because Outlook shows only the first frame.
- intent: Ensure the core message survives email clients that ignore animation.

### rule_lisraya_accessible_media_alt_transcripts
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: All images must carry descriptive alt text, and transcripts must be available for any video or audio.
- intent: Make media content accessible to assistive technology users.

### rule_lisraya_accessibility_reference_standard_wcag
- class=accessibility scope=brand hardness=soft_guidance polarity=should sections=None constraint=None
- rule_text: The reference accessibility standard for all materials is WCAG (wcag.com).
- intent: Anchor accessibility decisions to an authoritative standard.

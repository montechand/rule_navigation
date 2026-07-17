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

### rule_lisraya_accessible_body_type_and_hierarchy
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Body copy must be at least 16px and line height must be at least 150%; use more line height for light-on-dark text. Use a type scale to establish visual hierarchy.
- intent: Maintain readable body copy and a clear accessible text hierarchy.

### rule_lisraya_contrast_legibility_and_noncolor_cues
- class=accessibility scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=None
- rule_text: Test contrast, proof all text for legibility, and never rely on color alone to convey meaning.
- intent: Ensure text remains legible and information is available beyond color perception.

### rule_lisraya_descriptive_media_alternatives
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: All images must have descriptive alt text, and transcripts must be available for any video or audio.
- intent: Provide equivalent access to visual and time-based media content.

### rule_lisraya_email_gif_first_frame_and_fallback
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: For general email, animated GIFs must carry the key message in frame 1 because Outlook shows only the first frame. Do not autoplay motion longer than about 5 seconds without a static fallback.
- intent: Ensure essential email messaging remains available in clients and contexts with limited motion support.

### rule_lisraya_motion_pause_and_responsive_design
- class=accessibility scope=brand hardness=strong_default polarity=should sections=None constraint=None
- rule_text: Use quick transitions that do not interrupt flow, avoid excessive motion, provide a way to pause effects, and design for phone, tablet, and desktop.
- intent: Reduce motion barriers while preserving usable responsive experiences.

### rule_lisraya_visible_form_labels_and_touch_targets
- class=accessibility scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Forms must keep labels always visible: do not use placeholder text as the label and do not allow labels to disappear. Click and tap targets must be at least 48px.
- intent: Make form controls understandable and operable for all users.

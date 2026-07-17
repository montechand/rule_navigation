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

## Extracted rules (4)

### rule_lisraya_accessibility_alternative_text_and_media
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None governance=regulatory/allowed_with_disclosure
- rule_text: All non-decorative media assets must be fully accessible. This requires complete, descriptive alternative (alt) text on all image components, and easily accessible text transcripts for any video or audio components deployed across brand properties.
- intent: Comply with regulatory guidelines and serve visually or hearing impaired audiences.

### rule_lisraya_accessibility_animation_motion
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None governance=regulatory/allowed_with_disclosure
- rule_text: Animations must use quick transitions that do not interrupt flow, avoiding excessive motion, and provide a mechanism to pause effects. When designing email animated GIFs, the key medical or core promotional message must be fully legible in frame 1 to support Outlook clients, and autoplaying motion must not exceed 5 seconds without a static fallback option.
- intent: Ensure readability in email environments that block animation frames, and protect motion-sensitive users.

### rule_lisraya_accessibility_core_standards
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None governance=regulatory/allowed_with_disclosure
- rule_text: All materials must conform to WCAG standards (wcag.com). Body copy must be at least 16px (type_scale.body size = 16px) with a line height of at least 150% (line_height.accessibility.body_min = 150%), increasing for light-on-dark layout conditions. Do not rely on color alone to convey meaning, test contrast, and verify text legibility.
- intent: Ensure basic compliance with baseline medical-marketing accessibility rules.

### rule_lisraya_accessibility_interactive_and_forms
- class=accessibility scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding governance=regulatory/allowed_with_disclosure
- rule_text: Interactive components and forms must maintain labels that are always visible; placeholder-as-label or disappearing labels are strictly forbidden. All click and tap targets must have a minimum dimension of 48px (size.touch_target.minimum = 48px).
- intent: Maintain usable inputs and actionable buttons for motor-impaired and aging populations.

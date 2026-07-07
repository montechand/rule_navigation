# Review: grp_ibsrela_content_pattern_rules_05

doc_ref: `content_pattern_rules[5]`

## Original text

````
### 1.6 Component content specs (explicit)
 
**Top Matter — LOCKED (for reference only):** Supplied pre-built per audience (DTP = logo without BID, patient-friendly safety language; HCP = logo with BID). Contains the logo lockup, mandatory safety message with Medication Guide / full PI (incl. Boxed Warning) links, and View in Browser link. Safety copy is pre-approved. **[INHERITED]** consequences for content sections: (a) **never repeat the IBSRELA logo lockup inside a content section** — it lives in the header (logo may only appear inside approved campaign imagery, untouched); (b) the email's audience is fixed by the supplied header — all content-section copy and imagery must match it.
 
**End Matter — LOCKED (for reference only):** Supplied pre-built; contains the full FDA-reviewed ISI, Ardelyx address/contact, copyright/trademark/job code, and unsubscribe links. **[INHERITED]** consequences for content sections: (a) body copy size and line spacing must match the ISI body settings in the locked footer — fixed at **12 px / 1.4** in this system, see §1.2; (b) references and footnotes used in content sections resolve in/above End Matter, so numbering and symbol order must be coordinated at assembly (§4.5); (c) do not duplicate ISI fragments, indication statements, or legal lines inside content sections.
 
**Email / Primary 1 Column (optional):** Desktop ~600×1138 px; Mobile ~375×788 px. Single-column primary content block: full-width hero image → H1 headline (purple) → bold subheadline → body copy paragraph → teal "Get connected" CTA button. Theme alters background color; can be used with or without decorative wave borders at the top of the section. Editable fields: hero image, H1 headline, subheadline, body copy, CTA label. **Best for: lead message with a strong single visual and one clear call to action.**
 
**Email / Primary 2 Column (optional):** Desktop ~600×1088 px; Mobile ~375×1538 px (columns stack on mobile). Two-column layout — text left, brand/campaign imagery right. Uses brand purple/gradient background with white text and an outlined/contrasting CTA. Editable fields: headline, body copy, CTA label + destination URL, campaign/brand image. Component options: wave shape, image content, button style; default image is a placeholder. **Best for: brand storytelling and campaign moments.**
 
**Email / Secondary (optional, repeatable):** Desktop ~600×458 px; Mobile ~375×1363 px when stacked. Two-column card row for secondary content; each card contains brand image, navy headline, body copy, and a teal CTA button. May collapse to a single column. Editable per card: image, headline, body copy, CTA label + destination URL. Toggles: left column on/off, image-left/image-right, subhead, body copy, button, left/right images. **Best for: multi-topic secondary messaging, supplemental resources, and reference links.**

While generating the section, check what you are generating and see which section you want to choose for your design. 
````

## Extracted rules (6)

### rule_ibsrela_top_matter_locked_no_logo_repeat
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=['top_matter'] constraint=binding
- rule_text: Top Matter is supplied pre-built and LOCKED per audience (DTP = logo without BID, patient-friendly safety language; HCP = logo with BID), containing the logo lockup, mandatory safety message with Medication Guide / full PI (incl. Boxed Warning) links, and View in Browser link; safety copy is pre-approved. Consequence for content sections: never repeat the IBSRELA logo lockup inside a content section — it lives in the header (logo may only appear inside approved campaign imagery, untouched).
- intent: Prevent duplicate logo lockups and preserve the locked, pre-approved header.

### rule_ibsrela_top_matter_audience_fixes_content
- class=assembly scope=brand hardness=hard_constraint polarity=must sections=['top_matter'] constraint=binding
- rule_text: The email's audience is fixed by the supplied header (DTP vs HCP). All content-section copy and imagery must match the audience determined by the supplied Top Matter.
- intent: Keep content aligned to the audience locked by the pre-built header.

### rule_ibsrela_end_matter_locked_isi_footer
- class=assembly scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=binding
- rule_text: End Matter is supplied pre-built and LOCKED, containing the full FDA-reviewed ISI, Ardelyx address/contact, copyright/trademark/job code, and unsubscribe links. Consequences for content sections: (a) body copy size and line spacing must match the locked ISI body settings (fixed at 12 px / 1.4 in this system, see §1.2); (b) references and footnotes used in content sections resolve in/above End Matter, so numbering and symbol order must be coordinated at assembly (§4.5); (c) do not duplicate ISI fragments, indication statements, or legal lines inside content sections.
- intent: Preserve the locked regulatory footer and keep content typography and references consistent with it.

### rule_ibsrela_primary_1_column_component_spec
- class=layout scope=brand hardness=strong_default polarity=should sections=['hero', 'intro', 'cta'] constraint=ordering
- rule_text: Email / Primary 1 Column (optional) is a single-column primary content block (~600×1138 desktop / ~375×788 mobile): full-width hero image → H1 headline (purple) → bold subheadline → body copy paragraph → teal 'Get connected' CTA button. Theme alters background color; may be used with or without decorative wave borders at the top of the section. Editable fields: hero image, H1 headline, subheadline, body copy, CTA label. Best for a lead message with a strong single visual and one clear call to action.
- intent: Define the ordered structure and editable scope of the Primary 1 Column component.

### rule_ibsrela_primary_2_column_component_spec
- class=layout scope=brand hardness=strong_default polarity=should sections=['hero', 'cta'] constraint=None
- rule_text: Email / Primary 2 Column (optional) is a two-column layout (~600×1088 desktop / ~375×1538 mobile, columns stack on mobile): text left, brand/campaign imagery right, on brand purple/gradient background with white text and an outlined/contrasting CTA. Editable fields: headline, body copy, CTA label + destination URL, campaign/brand image. Component options: wave shape, image content, button style; default image is a placeholder. Best for brand storytelling and campaign moments.
- intent: Define the structure, styling and editable scope of the Primary 2 Column component.

### rule_ibsrela_secondary_component_spec
- class=layout scope=brand hardness=strong_default polarity=should sections=['efficacy', 'callout'] constraint=None
- rule_text: Email / Secondary (optional, repeatable) is a two-column card row for secondary content (~600×458 desktop / ~375×1363 mobile when stacked); each card contains brand image, navy headline, body copy, and a teal CTA button, and may collapse to a single column. Editable per card: image, headline, body copy, CTA label + destination URL. Toggles: left column on/off, image-left/image-right, subhead, body copy, button, left/right images. Best for multi-topic secondary messaging, supplemental resources, and reference links.
- intent: Define the repeatable Secondary card-row component and its per-card toggles.

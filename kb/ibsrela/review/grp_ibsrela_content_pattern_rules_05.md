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

## Extracted rules (8)

### rule_ibsrela_top_matter_locked_inheritance
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=['top_matter'] constraint=binding governance=trademark/forbidden
- rule_text: Top Matter is supplied pre-built and LOCKED per audience (DTP = logo without BID + patient-friendly safety language; HCP = logo with BID) and contains the logo lockup, the mandatory safety message with Medication Guide / full PI (incl. Boxed Warning) links, and the View in Browser link; safety copy is pre-approved. Never repeat the IBSRELA logo lockup inside a content section — it lives in the header (the logo may only appear inside approved campaign imagery, untouched).
- intent: Preserve the pre-approved, audience-specific locked header and prevent duplicate logo usage in content.

### rule_ibsrela_content_audience_matches_header
- class=assembly scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: The email's audience is fixed by the supplied header; all content-section copy and imagery must match that audience.
- intent: Keep content consistent with the locked header's audience scope.

### rule_ibsrela_end_matter_locked_inheritance
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=['end_matter'] constraint=None governance=disclosure/forbidden
- rule_text: End Matter is supplied pre-built and LOCKED; it contains the full FDA-reviewed ISI, Ardelyx address/contact, copyright/trademark/job code, and unsubscribe links. Do not duplicate ISI fragments, indication statements, or legal lines inside content sections.
- intent: Keep the FDA-reviewed ISI and legal copy solely in the locked footer.

### rule_ibsrela_content_body_matches_isi_settings
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Content-section body copy size and line spacing must match the ISI body settings in the locked footer — fixed at 12 px / 1.4 in this system (see §1.2).
- intent: Align content typography with the locked footer's ISI body settings.

### rule_ibsrela_references_coordinated_at_assembly
- class=assembly scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=None
- rule_text: References and footnotes used in content sections resolve in/above End Matter, so their numbering and symbol order must be coordinated at assembly (§4.5).
- intent: Ensure footnote/reference numbering resolves correctly against the locked footer.

### rule_ibsrela_primary_1_column_component_spec
- class=layout scope=brand hardness=strong_default polarity=should sections=['hero', 'intro', 'cta'] constraint=ordering
- rule_text: Email / Primary 1 Column (~600×1138 desktop, ~375×788 mobile) is a single-column primary content block ordered full-width hero image → H1 headline (purple) → bold subheadline → body copy paragraph → teal 'Get connected' CTA button. Theme alters background color; may be used with or without decorative wave borders at the top of the section. Editable fields: hero image, H1 headline, subheadline, body copy, CTA label. Best for a lead message with a strong single visual and one clear call to action.
- intent: Define the 1-column primary component structure and editable fields.

### rule_ibsrela_primary_2_column_component_spec
- class=layout scope=brand hardness=strong_default polarity=should sections=['hero', 'cta'] constraint=None
- rule_text: Email / Primary 2 Column (~600×1088 desktop, ~375×1538 mobile with columns stacking) is a two-column layout — text left, brand/campaign imagery right — using brand purple/gradient background with white text and an outlined/contrasting CTA. Editable fields: headline, body copy, CTA label + destination URL, campaign/brand image. Component options: wave shape, image content, button style; default image is a placeholder. Best for brand storytelling and campaign moments.
- intent: Define the 2-column primary component structure, styling and editable fields.

### rule_ibsrela_secondary_component_spec
- class=layout scope=brand hardness=strong_default polarity=should sections=['efficacy', 'affordability', 'cta', 'callout'] constraint=None
- rule_text: Email / Secondary (repeatable; ~600×458 desktop, ~375×1363 mobile when stacked) is a two-column card row for secondary content; each card contains a brand image, navy headline, body copy, and a teal CTA button, and may collapse to a single column. Editable per card: image, headline, body copy, CTA label + destination URL. Toggles: left column on/off, image-left/image-right, subhead, body copy, button, left/right images. Best for multi-topic secondary messaging, supplemental resources, and reference links.
- intent: Define the repeatable secondary card-row component structure and toggles.

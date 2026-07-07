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
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=['top_matter'] constraint=binding
- rule_text: Top Matter is supplied pre-built and locked (per audience: DTP = logo without BID and patient-friendly safety language; HCP = logo with BID). It contains the logo lockup, mandatory safety message with Medication Guide / full PI (incl. Boxed Warning) links, and View in Browser link; safety copy is pre-approved. Inherited consequences for content sections: (a) never repeat the IBSRELA logo lockup inside a content section — it lives in the header (the logo may only appear inside approved campaign imagery, untouched); (b) the email's audience is fixed by the supplied header, so all content-section copy and imagery must match it.
- intent: Preserve the locked, pre-approved header and prevent logo/audience drift in content.

### rule_ibsrela_end_matter_locked_no_duplication
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must_not sections=['end_matter'] constraint=binding
- rule_text: End Matter is supplied pre-built and locked, containing the full FDA-reviewed ISI, Ardelyx address/contact, copyright/trademark/job code, and unsubscribe links. Inherited consequences for content sections: (a) body copy size and line spacing must match the ISI body settings in the locked footer, fixed at 12px / 1.4 in this system (see body_locked / isi.line_height, §1.2); (b) references and footnotes in content sections resolve in/above End Matter, so numbering and symbol order must be coordinated at assembly (§4.5); (c) do not duplicate ISI fragments, indication statements, or legal lines inside content sections.
- intent: Keep the FDA-reviewed footer authoritative and avoid conflicting/duplicated legal content.

### rule_ibsrela_content_body_matches_isi_body_locked
- class=typography scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Body copy size and line spacing in content sections must match the ISI body settings in the locked footer — fixed at 12px / 1.4 in this system (see §1.2).
- intent: Ensure visual consistency between content body and the locked ISI footer.

### rule_ibsrela_primary_1col_component_spec
- class=layout scope=brand hardness=strong_default polarity=should sections=['hero', 'intro'] constraint=ordering
- rule_text: Email / Primary 1 Column (optional): Desktop ~600×1138px; Mobile ~375×788px (see component.primary_1col.dimensions). Single-column primary content block ordered full-width hero image → H1 headline (purple) → bold subheadline → body copy paragraph → teal 'Get connected' CTA button. Theme alters background color; may be used with or without decorative wave borders at the top of the section. Editable fields: hero image, H1 headline, subheadline, body copy, CTA label. Best for a lead message with a strong single visual and one clear call to action.
- intent: Define the fixed structure and editable scope of the 1-column primary template.

### rule_ibsrela_primary_2col_component_spec
- class=layout scope=brand hardness=strong_default polarity=should sections=['hero', 'callout'] constraint=binding
- rule_text: Email / Primary 2 Column (optional): Desktop ~600×1088px; Mobile ~375×1538px (columns stack on mobile). Two-column layout — text left, brand/campaign imagery right — on a brand purple/gradient background with white text and an outlined/contrasting CTA. Editable fields: headline, body copy, CTA label + destination URL, campaign/brand image. Component options: wave shape, image content, button style; default image is a placeholder. Best for brand storytelling and campaign moments.
- intent: Define the 2-column primary template layout, background treatment and editable scope.

### rule_ibsrela_secondary_component_spec
- class=layout scope=brand hardness=strong_default polarity=may sections=['callout'] constraint=binding
- rule_text: Email / Secondary (optional, repeatable): Desktop ~600×458px; Mobile ~375×1363px when stacked. Two-column card row for secondary content; each card contains a brand image, navy headline, body copy, and a teal CTA button. May collapse to a single column. Editable per card: image, headline, body copy, CTA label + destination URL. Toggles: left column on/off, image-left/image-right, subhead, body copy, button, left/right images. Best for multi-topic secondary messaging, supplemental resources, and reference links.
- intent: Define the repeatable secondary card-row template, its dimensions and toggles.

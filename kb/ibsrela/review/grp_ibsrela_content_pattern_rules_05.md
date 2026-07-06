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

### rule_ibsrela_no_logo_duplication_in_content
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=verbatim_content
- rule_text: Never repeat the IBSRELA logo lockup inside a content section — it lives in the locked header (Top Matter). The logo may only appear inside approved campaign imagery, untouched.
- intent: Prevent duplicate/altered logo usage outside the pre-built header.

### rule_ibsrela_content_audience_matches_header
- class=assembly scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: The email's audience is fixed by the supplied Top Matter header (DTP = logo without BID and patient-friendly safety language; HCP = logo with BID). All content-section copy and imagery must match the audience set by the supplied header.
- intent: Keep content aligned with the audience-specific pre-built header.

### rule_ibsrela_content_body_matches_isi_body_settings
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Body copy size and line spacing in content sections must match the ISI body settings in the locked End Matter footer — fixed at 12 px / 1.4 line height in this system (see §1.2).
- intent: Maintain typographic consistency with the locked footer ISI.

### rule_ibsrela_footnote_reference_numbering_coordinated_at_asse
- class=assembly scope=brand hardness=hard_constraint polarity=must sections=['end_matter'] constraint=None
- rule_text: References and footnotes used in content sections resolve in/above End Matter, so their numbering and symbol order must be coordinated at assembly (see §4.5).
- intent: Ensure footnote/reference ordering stays consistent with the locked footer.

### rule_ibsrela_no_isi_indication_legal_duplication_in_content
- class=assembly scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=verbatim_content
- rule_text: Do not duplicate ISI fragments, indication statements, or legal lines inside content sections — these live in the locked End Matter.
- intent: Prevent regulatory content duplication outside the FDA-reviewed footer.

### rule_ibsrela_primary_1_column_structure_order
- class=layout scope=brand hardness=strong_default polarity=should sections=['hero', 'intro', 'cta'] constraint=ordering
- rule_text: Email / Primary 1 Column (optional): single-column primary content block laid out top-to-bottom as full-width hero image → H1 headline (purple) → bold subheadline → body copy paragraph → teal "Get connected" CTA button. Desktop ~600×1138 px; Mobile ~375×788 px. Theme alters background color; may be used with or without decorative wave borders at the top of the section. Editable fields: hero image, H1 headline, subheadline, body copy, CTA label. Best for a lead message with a strong single visual and one clear call to action.
- intent: Define the canonical single-column primary content block structure.

### rule_ibsrela_primary_2_column_layout
- class=layout scope=brand hardness=strong_default polarity=should sections=None constraint=None
- rule_text: Email / Primary 2 Column (optional): two-column layout — text left, brand/campaign imagery right; columns stack on mobile. Uses brand purple/gradient background with white text and an outlined/contrasting CTA. Desktop ~600×1088 px; Mobile ~375×1538 px. Editable fields: headline, body copy, CTA label + destination URL, campaign/brand image. Component options: wave shape, image content, button style; default image is a placeholder. Best for brand storytelling and campaign moments.
- intent: Define the two-column brand-storytelling content block.

### rule_ibsrela_secondary_card_row_structure
- class=layout scope=brand hardness=strong_default polarity=should sections=None constraint=None
- rule_text: Email / Secondary (optional, repeatable): two-column card row for secondary content; each card contains brand image, navy headline, body copy, and a teal CTA button. May collapse to a single column. Desktop ~600×458 px; Mobile ~375×1363 px when stacked. Editable per card: image, headline, body copy, CTA label + destination URL. Toggles: left column on/off, image-left/image-right, subhead, body copy, button, left/right images. Best for multi-topic secondary messaging, supplemental resources, and reference links.
- intent: Define the repeatable secondary card-row content block.

# Review: grp_lisraya_content_pattern_rules_07

doc_ref: `content_pattern_rules[7]`

## Original text

````
### Approved Campaign Messaging (verbatim framework)
- **Headline:** YOU DESERVE MORE. So there's LISRAYA—the first targeted treatment for dermatomyositis.
- **Product benefits:** "LISRAYA is a once-daily FDA-approved pill that blocks the specific inflammatory signals that drive dermatomyositis, so you can:" → bullets: *Increase your muscle strength* / *Improve your skin symptoms* / *Rely less on steroids* / *Do more of the activities you love*.
- **MOA (primary):** "Unlike other treatments for dermatomyositis (DM), which suppress the immune system generally, LISRAYA targets the root cause of the disease."
- **MOA (alt):** "...LISRAYA works by turning off the specific inflammatory switches that are stuck in the 'on' position."
- **Administration:** "LISRAYA is a once-daily pill—you can take it at home or anywhere you like, with no shots or infusions required."
- Doctor-discussion CTA pattern: "Talk to your doctor about LISRAYA, the DM treatment you may be looking for."
- Support program name: **My Compass Support** (patient support: Personalized Communication via PAL — text, phone, email, in person; Authorization Support).
````

## Extracted rules (6)

### rule_lisraya_administration_statement_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: Administration messaging must use the approved verbatim statement: "LISRAYA is a once-daily pill—you can take it at home or anywhere you like, with no shots or infusions required."
- intent: Keep administration/route claims within approved language.

### rule_lisraya_campaign_headline_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: The approved campaign headline must be reproduced verbatim: 'YOU DESERVE MORE. So there's LISRAYA—the first targeted treatment for dermatomyositis.' No paraphrasing or truncation is permitted.
- intent: Lock the MLR-approved campaign headline exactly as cleared.

### rule_lisraya_doctor_discussion_cta_verbatim
- class=cta scope=campaign hardness=hard_constraint polarity=must sections=['cta'] constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: The doctor-discussion CTA follows the approved pattern verbatim: "Talk to your doctor about LISRAYA, the DM treatment you may be looking for."
- intent: Maintain approved doctor-discussion call to action.

### rule_lisraya_moa_messaging_approved_variants
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['efficacy'] constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: Mechanism-of-action messaging uses one of two approved verbatim options: primary — 'Unlike other treatments for dermatomyositis (DM), which suppress the immune system generally, LISRAYA targets the root cause of the disease.'; alternate — '...LISRAYA works by turning off the specific inflammatory switches that are stuck in the "on" position.' Only these two approved phrasings may be used to describe MOA.
- intent: Ensure MOA claims stay within MLR-approved language.

### rule_lisraya_product_benefits_bullets_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['intro'] constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: The product-benefits lead-in ('LISRAYA is a once-daily FDA-approved pill that blocks the specific inflammatory signals that drive dermatomyositis, so you can:') must be followed by exactly the four approved benefit bullets, in this order: 'Increase your muscle strength', 'Improve your skin symptoms', 'Rely less on steroids', 'Do more of the activities you love'.
- intent: Preserve the approved benefits claim set and its order.

### rule_lisraya_support_program_name_and_scope
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['affordability'] constraint=verbatim_content governance=trademark/verbatim_only
- rule_text: The patient support program must always be referred to by its exact name, 'My Compass Support', and its described scope is limited to Personalized Communication via PAL (text, phone, email, in person) and Authorization Support.
- intent: Protect the branded support-program name and keep its scope accurate.

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

### rule_lisraya_campaign_headline_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: The approved campaign headline must be used verbatim: "YOU DESERVE MORE. So there's LISRAYA—the first targeted treatment for dermatomyositis."
- intent: Preserve MLR-approved campaign headline and 'first targeted treatment' claim.

### rule_lisraya_product_benefits_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['efficacy'] constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: Product benefit copy must use the approved framework verbatim: lead-in "LISRAYA is a once-daily FDA-approved pill that blocks the specific inflammatory signals that drive dermatomyositis, so you can:" followed by the four approved bullets — Increase your muscle strength / Improve your skin symptoms / Rely less on steroids / Do more of the activities you love.
- intent: Lock the FDA-approved efficacy claim set and mechanism statement.

### rule_lisraya_moa_messaging_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['intro'] constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: Mechanism-of-action messaging must use the approved wording. Primary: "Unlike other treatments for dermatomyositis (DM), which suppress the immune system generally, LISRAYA targets the root cause of the disease." Alternate: "...LISRAYA works by turning off the specific inflammatory switches that are stuck in the 'on' position."
- intent: Keep MOA claims within MLR-approved language.

### rule_lisraya_administration_messaging_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: Administration messaging must use the approved wording verbatim: "LISRAYA is a once-daily pill—you can take it at home or anywhere you like, with no shots or infusions required."
- intent: Preserve approved administration/route claim.

### rule_lisraya_doctor_discussion_cta_pattern
- class=cta scope=campaign hardness=hard_constraint polarity=must sections=['cta'] constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: The doctor-discussion CTA must follow the approved pattern: "Talk to your doctor about LISRAYA, the DM treatment you may be looking for."
- intent: Standardize the approved doctor-discussion CTA language.

### rule_lisraya_support_program_name_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=verbatim_content governance=trademark/verbatim_only
- rule_text: The patient support program must be named "My Compass Support". Its offerings comprise Personalized Communication via PAL (text, phone, email, in person) and Authorization Support.
- intent: Protect the trademarked support-program name and its described services.

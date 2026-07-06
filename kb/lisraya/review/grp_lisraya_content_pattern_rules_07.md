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

## Extracted rules (7)

### rule_lisraya_campaign_headline_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=verbatim_content
- rule_text: The approved campaign headline must be used verbatim: "YOU DESERVE MORE. So there's LISRAYA—the first targeted treatment for dermatomyositis."
- intent: Preserve MLR-approved campaign headline lockup exactly.

### rule_lisraya_product_benefits_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['efficacy'] constraint=verbatim_content
- rule_text: The product benefits framework must be used verbatim: "LISRAYA is a once-daily FDA-approved pill that blocks the specific inflammatory signals that drive dermatomyositis, so you can:" followed by the bullets: Increase your muscle strength / Improve your skin symptoms / Rely less on steroids / Do more of the activities you love.
- intent: Preserve MLR-approved product benefits claims exactly.

### rule_lisraya_moa_primary_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: The primary MOA statement must be used verbatim: "Unlike other treatments for dermatomyositis (DM), which suppress the immune system generally, LISRAYA targets the root cause of the disease."
- intent: Preserve MLR-approved primary MOA claim exactly.

### rule_lisraya_moa_alt_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: The alternate MOA statement must be used verbatim: "...LISRAYA works by turning off the specific inflammatory switches that are stuck in the 'on' position."
- intent: Preserve MLR-approved alternate MOA claim exactly.

### rule_lisraya_administration_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: The administration statement must be used verbatim: "LISRAYA is a once-daily pill—you can take it at home or anywhere you like, with no shots or infusions required."
- intent: Preserve MLR-approved administration claim exactly.

### rule_lisraya_doctor_discussion_cta_verbatim
- class=cta scope=campaign hardness=hard_constraint polarity=must sections=['cta'] constraint=verbatim_content
- rule_text: The doctor-discussion CTA must follow the approved pattern verbatim: "Talk to your doctor about LISRAYA, the DM treatment you may be looking for."
- intent: Preserve MLR-approved doctor-discussion CTA pattern exactly.

### rule_lisraya_support_program_name_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: The patient support program must be named verbatim as "My Compass Support" (patient support: Personalized Communication via PAL — text, phone, email, in person; Authorization Support).
- intent: Preserve the approved support program name exactly.

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

## Extracted rules (5)

### rule_lisraya_administration_and_convenience_messaging
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['efficacy', 'intro'] constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: Administration convenience statements must use verbatim wording: "LISRAYA is a once-daily pill—you can take it at home or anywhere you like, with no shots or infusions required."
- intent: Maintain accurate compliance guidelines concerning pill delivery claims compared to injections.

### rule_lisraya_campaign_approved_headlines_verbatim
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['hero', 'intro'] constraint=verbatim_content
- rule_text: The full campaign lockup copy must read exactly: "YOU DESERVE MORE. So there's LISRAYA—the first targeted treatment for dermatomyositis."
- intent: Maintain strict medical-legal alignment for primary patient-facing campaign headlines.

### rule_lisraya_doctor_discussion_cta_pattern
- class=cta scope=campaign hardness=hard_constraint polarity=must sections=['cta'] constraint=binding governance=mlr_claim/verbatim_only
- rule_text: CTAs utilize a specific signature shape and treatment.
- intent: Ensure medical discussion CTAs leverage approved regulatory wording.

### rule_lisraya_patient_support_program_naming
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=['patient_story', 'affordability'] constraint=verbatim_content governance=trademark/verbatim_only
- rule_text: The patient support program must always be referred to as "My Compass Support" verbatim.
- intent: Maintain accurate and consistent brand name usage for the patient support program.

### rule_lisraya_product_benefits_messaging
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['efficacy', 'intro'] constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: Product benefits must be introduced by the exact phrasing: "LISRAYA is a once-daily FDA-approved pill that blocks the specific inflammatory signals that drive dermatomyositis, so you can:" followed by approved benefit bullet points.
- intent: Fulfill MLR requirements regarding the approved indication and benefit framing.

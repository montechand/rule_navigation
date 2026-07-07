# Review: grp_ibsrela_content_pattern_rules_06

doc_ref: `content_pattern_rules[6]`

## Original text

````
### DTP voice & tone (patient-facing)
- Address the reader in second person ("you", "your") and frame IBSRELA around getting back to everyday life, not clinical performance.
- Lead with an empathetic acknowledgment of unresolved symptoms (e.g., "If you're still experiencing… you don't have to settle for feeling just okay") before introducing the product benefit.
- Use the phrase **"IBS-C symptoms"** (constipation, belly pain, and/or bloating) — not "your condition" or clinical jargon — and consistently name the three symptoms together when listing benefits.
- Patient-story modules must carry the disclosure "Individual results and experiences may vary. [Name] is an actual patient taking IBSRELA and has been compensated for discussing her experience." immediately under the story copy.
- Efficacy claims must carry the approved qualifier "*Results may vary. Study results seen in 12- and 26-week trials…" and the limitation "These results were observed in the study, but the analysis cannot be used to draw conclusions."
````

## Extracted rules (5)

### rule_ibsrela_dtp_second_person_everyday_life_voice
- class=voice_tone scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Patient-facing DTP copy must address the reader in second person ("you", "your") and frame IBSRELA around getting back to everyday life, not clinical performance.
- intent: Keep DTP tone empathetic, personal, and life-focused rather than clinical.

### rule_ibsrela_dtp_empathetic_lead_before_benefit
- class=voice_tone scope=brand hardness=strong_default polarity=must sections=['intro', 'hero'] constraint=ordering
- rule_text: Lead with an empathetic acknowledgment of unresolved symptoms (e.g., "If you're still experiencing… you don't have to settle for feeling just okay") before introducing the product benefit.
- intent: Meet the reader in their frustration before pitching the product.

### rule_ibsrela_dtp_ibs_c_symptoms_terminology
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: Use the phrase "IBS-C symptoms" (constipation, belly pain, and/or bloating) — not "your condition" or clinical jargon — and consistently name the three symptoms together when listing benefits.
- intent: Enforce approved, plain-language symptom terminology and consistent triad naming.

### rule_ibsrela_patient_story_disclosure
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=['patient_story'] constraint=verbatim_content governance=disclosure/verbatim_only
- rule_text: Patient-story modules must carry the disclosure "Individual results and experiences may vary. [Name] is an actual patient taking IBSRELA and has been compensated for discussing her experience." immediately under the story copy.
- intent: Comply with disclosure obligations for compensated patient testimonials.

### rule_ibsrela_efficacy_claim_required_qualifiers
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=['efficacy'] constraint=verbatim_content governance=mlr_claim/requires_qualifier
- rule_text: Efficacy claims must carry the approved qualifier "*Results may vary. Study results seen in 12- and 26-week trials…" and the limitation "These results were observed in the study, but the analysis cannot be used to draw conclusions."
- intent: Ensure efficacy claims are properly qualified and limited per MLR.

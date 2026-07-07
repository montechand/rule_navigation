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

## Extracted rules (4)

### rule_ibsrela_dtp_second_person_everyday_life_framing
- class=voice_tone scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Address the reader in second person ("you", "your") and frame IBSRELA around getting back to everyday life, not clinical performance. Lead with an empathetic acknowledgment of unresolved symptoms (e.g., "If you're still experiencing… you don't have to settle for feeling just okay") before introducing the product benefit.
- intent: Keep patient-facing voice empathetic, personal, and life-oriented rather than clinical.

### rule_ibsrela_dtp_ibsc_symptoms_phrasing
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: Use the phrase "IBS-C symptoms" (constipation, belly pain, and/or bloating) — not "your condition" or clinical jargon — and consistently name the three symptoms together when listing benefits.
- intent: Enforce approved, non-clinical patient-facing terminology and consistent symptom listing.

### rule_ibsrela_patient_story_disclosure_verbatim
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=['patient_story'] constraint=verbatim_content
- rule_text: Patient-story modules must carry the disclosure "Individual results and experiences may vary. [Name] is an actual patient taking IBSRELA and has been compensated for discussing her experience." immediately under the story copy.
- intent: Ensure required patient-testimonial disclosure appears verbatim adjacent to the story.

### rule_ibsrela_efficacy_claim_qualifier_and_limitation
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=['efficacy'] constraint=verbatim_content
- rule_text: Efficacy claims must carry the approved qualifier "*Results may vary. Study results seen in 12- and 26-week trials…" and the limitation "These results were observed in the study, but the analysis cannot be used to draw conclusions."
- intent: Attach mandatory MLR qualifier and limitation language to any efficacy claim.

# Review: grp_lisraya_content_pattern_rules_04

doc_ref: `content_pattern_rules[4]`

## Original text

````
### Editorial / Style Rules
- **Abbreviation "DM":** After first mention of "dermatomyositis," use "DM" in running copy to avoid repetition. **Do NOT use "DM" in headlines, headings, or subheads** — always the full word there (clarity, accessibility, and SEO on web). First-mention pattern: `dermatomyositis (DM)`.
  - Because sections are assembled later: **[GENERAL] every standalone section must establish `dermatomyositis (DM)` at its own first mention** unless the assembly brief states the abbreviation is established upstream.
- **Inclusive language (patient materials):** say "someone with dermatomyositis" / "people with dermatomyositis" — **not "patients."** ("Patients" is acceptable only in HCP materials.) Use **"care team"** (not "staff") for the network of patients, HCPs, and support systems.
- **Numbers:** spell out zero–nine; numerals for 10+. **Exceptions — always numerals: percentages, ages, ratios.** Percentages use the % sign (e.g., 74%).
- **Data tone:** when citing clinical data, avoid negative or fear-based language; use an empathetic, supportive, trust-building tone without oversimplifying. Example pattern: "Participants in the VALOR study taking LISRAYA had nearly 50% more improvement in their DM symptoms after one year compared to placebo."
- **Punctuation:** Oxford/serial comma always in series of 3+.
````

## Extracted rules (6)

### rule_lisraya_dm_abbreviation_first_mention
- class=copy_editorial scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: After first mention of "dermatomyositis," use "DM" in running copy to avoid repetition; first-mention pattern is `dermatomyositis (DM)`. [GENERAL] Because sections are assembled later, every standalone section must establish `dermatomyositis (DM)` at its own first mention unless the assembly brief states the abbreviation is established upstream.
- intent: Ensure the abbreviation is defined per section so modular assembly never leaves DM undefined.

### rule_lisraya_dm_not_in_headings
- class=copy_editorial scope=org_baseline hardness=hard_constraint polarity=must_not sections=None constraint=verbatim_content
- rule_text: Do NOT use "DM" in headlines, headings, or subheads — always use the full word "dermatomyositis" there (for clarity, accessibility, and SEO on web).
- intent: Preserve clarity, accessibility, and SEO by spelling out the condition in headings.

### rule_lisraya_inclusive_patient_language
- class=copy_editorial scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: In patient materials, say "someone with dermatomyositis" / "people with dermatomyositis" — not "patients" ("patients" is acceptable only in HCP materials). Use "care team" (not "staff") for the network of patients, HCPs, and support systems.
- intent: Maintain inclusive, person-first language in patient-facing copy.

### rule_lisraya_number_style
- class=copy_editorial scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Spell out zero–nine; use numerals for 10+. Exceptions — always numerals: percentages, ages, and ratios. Percentages use the % sign (e.g., 74%).
- intent: Enforce consistent numeral styling across copy.

### rule_lisraya_oxford_comma
- class=copy_editorial scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Use the Oxford/serial comma always in series of 3 or more.
- intent: Consistent punctuation across all copy.

### rule_lisraya_clinical_data_tone
- class=voice_tone scope=org_baseline hardness=strong_default polarity=must sections=['efficacy'] constraint=None
- rule_text: When citing clinical data, avoid negative or fear-based language; use an empathetic, supportive, trust-building tone without oversimplifying. Example pattern: "Participants in the VALOR study taking LISRAYA had nearly 50% more improvement in their DM symptoms after one year compared to placebo."
- intent: Keep data messaging empathetic and trust-building without oversimplifying.

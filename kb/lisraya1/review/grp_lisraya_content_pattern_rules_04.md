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

## Extracted rules (5)

### rule_lisraya_clinical_data_empathetic_tone
- class=voice_tone scope=brand hardness=soft_guidance polarity=should sections=['efficacy'] constraint=None
- rule_text: When citing clinical data, avoid negative or fear-based language; use an empathetic, supportive, trust-building tone without oversimplifying. Example pattern: "Participants in the VALOR study taking LISRAYA had nearly 50% more improvement in their DM symptoms after one year compared to placebo."
- intent: Keep clinical data messaging supportive and trust-building.

### rule_lisraya_dm_abbreviation_first_mention
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: After first mention of "dermatomyositis," use "DM" in running copy to avoid repetition, following the first-mention pattern `dermatomyositis (DM)`. Do NOT use "DM" in headlines, headings, or subheads — always spell out the full word there (clarity, accessibility, SEO). Because sections are assembled later, [GENERAL] every standalone section must establish `dermatomyositis (DM)` at its own first mention unless the assembly brief states the abbreviation is established upstream.
- intent: Ensure clear, accessible, SEO-friendly disease naming while allowing abbreviation in body copy.

### rule_lisraya_number_formatting_convention
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Spell out zero–nine; use numerals for 10+ (number.format.ten_plus_numerals). Exceptions — always numerals: percentages, ages, ratios. Percentages use the % sign (number.percent.sign = %), e.g., 74%.
- intent: Consistent numeral formatting across copy.

### rule_lisraya_oxford_serial_comma
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Use the Oxford/serial comma always in a series of 3 or more items.
- intent: Consistent punctuation style.

### rule_lisraya_person_first_inclusive_language
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: In patient materials, say "someone with dermatomyositis" / "people with dermatomyositis" — not "patients." "Patients" is acceptable only in HCP materials. Use "care team" (not "staff") for the network of patients, HCPs, and support systems.
- intent: Person-first, inclusive language appropriate to audience.

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

### rule_lisraya_clinical_data_supportive_tone
- class=voice_tone scope=brand hardness=strong_default polarity=should sections=['efficacy'] constraint=None
- rule_text: When citing clinical data, avoid negative or fear-based language and use an empathetic, supportive, trust-building tone without oversimplifying.
- intent: Present clinical information with empathy while preserving its meaning.

### rule_lisraya_dm_abbreviation_running_copy
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Use “dermatomyositis (DM)” at first mention, then use “DM” in running copy to avoid repetition. Do not use “DM” in headlines, headings, or subheads; use the full word there.
- intent: Maintain clear, accessible terminology while reducing repetition in body copy.

### rule_lisraya_inclusive_patient_language_and_care_team
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: In patient materials, say “someone with dermatomyositis” or “people with dermatomyositis,” not “patients.” Use “care team,” not “staff,” for the network of patients, HCPs, and support systems. “Patients” is acceptable only in HCP materials.
- intent: Use inclusive, person-first language for patient audiences.

### rule_lisraya_number_and_percentage_style
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: Spell out zero through nine and use numerals for 10 and above. Always use numerals for percentages, ages, and ratios; percentages use the % sign.
- intent: Keep numerical information consistent and easy to scan.

### rule_lisraya_oxford_serial_comma
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Always use the Oxford/serial comma in a series of three or more items.
- intent: Maintain consistent punctuation across brand copy.

### rule_lisraya_standalone_section_dm_first_mention
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: Every standalone section must establish “dermatomyositis (DM)” at its own first mention unless the assembly brief states the abbreviation is established upstream.
- intent: Ensure independently assembled sections remain understandable on their own.

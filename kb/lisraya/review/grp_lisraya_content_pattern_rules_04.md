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

## Extracted rules (7)

### rule_lisraya_dm_abbreviation_usage
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=verbatim_content
- rule_text: After the first mention of 'dermatomyositis,' use 'DM' in running copy to avoid repetition. The first-mention pattern is `dermatomyositis (DM)`.
- intent: Establish the DM abbreviation cleanly on first use to reduce repetition without losing clarity.

### rule_lisraya_dm_forbidden_in_headings
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=verbatim_content
- rule_text: Do NOT use 'DM' in headlines, headings, or subheads — always spell out the full word 'dermatomyositis' there (for clarity, accessibility, and web SEO).
- intent: Preserve clarity, accessibility, and SEO in prominent heading text.

### rule_lisraya_dm_first_mention_per_section
- class=assembly scope=org_baseline hardness=strong_default polarity=must sections=None constraint=verbatim_content
- rule_text: [GENERAL] Because sections are assembled later, every standalone section must establish `dermatomyositis (DM)` at its own first mention, unless the assembly brief states the abbreviation is established upstream.
- intent: Ensure the abbreviation reads correctly regardless of how sections are later assembled.

### rule_lisraya_inclusive_patient_language
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: In patient materials, say 'someone with dermatomyositis' / 'people with dermatomyositis' — not 'patients' ('patients' is acceptable only in HCP materials). Use 'care team' (not 'staff') for the network of patients, HCPs, and support systems.
- intent: Use inclusive, person-first language appropriate for DTC patient audiences.

### rule_lisraya_number_formatting
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Spell out numbers zero–nine; use numerals for 10 and above. Exceptions — always use numerals for percentages, ages, and ratios. Percentages use the % sign (e.g., 74%).
- intent: Consistent, readable number formatting across copy.

### rule_lisraya_data_citation_tone
- class=voice_tone scope=brand hardness=soft_guidance polarity=must sections=['efficacy', 'chart'] constraint=None
- rule_text: When citing clinical data, avoid negative or fear-based language; use an empathetic, supportive, trust-building tone without oversimplifying. Example pattern: 'Participants in the VALOR study taking LISRAYA had nearly 50% more improvement in their DM symptoms after one year compared to placebo.'
- intent: Keep clinical data framing empathetic and trust-building.

### rule_lisraya_oxford_comma
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Always use the Oxford/serial comma in a series of three or more items.
- intent: Consistent punctuation in lists.

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

### rule_lisraya_dm_abbreviation_usage
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=verbatim_content
- rule_text: After the first mention of 'dermatomyositis,' use 'DM' in running copy to avoid repetition, using the first-mention pattern 'dermatomyositis (DM)'. Do NOT use 'DM' in headlines, headings, or subheads — always spell out the full word there (clarity, accessibility, and SEO on web). Because sections are assembled later, [GENERAL] every standalone section must establish 'dermatomyositis (DM)' at its own first mention unless the assembly brief states the abbreviation is established upstream.
- intent: Balance concise running copy with clear, accessible headings across independently assembled sections.

### rule_lisraya_dm_never_in_headings
- class=copy_editorial scope=brand hardness=strong_default polarity=must_not sections=None constraint=verbatim_content
- rule_text: Do NOT use the abbreviation 'DM' in headlines, headings, or subheads — always use the full word 'dermatomyositis' there for clarity, accessibility, and SEO on web.
- intent: Keep headings clear and searchable by never abbreviating the disease name.

### rule_lisraya_inclusive_patient_language
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=verbatim_content
- rule_text: In patient materials, say 'someone with dermatomyositis' / 'people with dermatomyositis' — not 'patients.' ('Patients' is acceptable only in HCP materials.) Use 'care team' (not 'staff') for the network of patients, HCPs, and support systems.
- intent: Use person-first, inclusive language appropriate to patient/DTC audiences.

### rule_lisraya_number_formatting
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Spell out numbers zero–nine; use numerals for 10 and above. Exceptions — always use numerals for percentages, ages, and ratios. Percentages use the % sign (e.g., 74%).
- intent: Consistent numeric style across copy.

### rule_lisraya_clinical_data_tone
- class=voice_tone scope=brand hardness=strong_default polarity=must sections=['efficacy', 'chart'] constraint=verbatim_content
- rule_text: When citing clinical data, avoid negative or fear-based language; use an empathetic, supportive, trust-building tone without oversimplifying. Example pattern: 'Participants in the VALOR study taking LISRAYA had nearly 50% more improvement in their DM symptoms after one year compared to placebo.'
- intent: Present efficacy data in a supportive, trust-building way.

### rule_lisraya_oxford_comma
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Always use the Oxford/serial comma in a series of 3 or more items.
- intent: Consistent punctuation for lists.

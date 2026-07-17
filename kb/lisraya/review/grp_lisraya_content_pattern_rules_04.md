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

### rule_lisraya_rule_lisraya_editorial_abbreviation_dm
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: On the first mention of dermatomyositis within a section, spell it out completely as 'dermatomyositis (DM)'. Thereafter, use the abbreviation 'DM' in running copy. Do NOT use the abbreviation 'DM' in headlines, headings, or subheads; always use the full term there.
- intent: Maintain medical term clarity and search/accessibility compliance while enabling modular section assembly.

### rule_lisraya_rule_lisraya_editorial_numbers_formatting
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=ordering
- rule_text: Spell out whole numbers from zero through nine (zero, one, two... nine), and use numerals for numbers 10 and above. Always use numerals for percentages (using the % sign, e.g., 74%), ages, and ratios.
- intent: Ensure clean, consistent typographical presentation of numerical data across brand copy.

### rule_lisraya_rule_lisraya_editorial_oxford_comma
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=ordering
- rule_text: Always use the Oxford (serial) comma in lists of three or more items.
- intent: Maintain syntactic clarity and consistent punctuation across all written content.

### rule_lisraya_rule_lisraya_patient_inclusive_language
- class=voice_tone scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=exclusivity governance=regulatory/forbidden
- rule_text: In patient-facing materials, do not use the term 'patients'. Instead, use inclusive language such as 'someone with dermatomyositis' or 'people with dermatomyositis'. Additionally, refer to the network of support as the 'care team' rather than 'staff'.
- intent: Ensure patient-centric, empowering, and respectful communication in all DTC materials.

### rule_lisraya_rule_lisraya_voice_and_tone_principles
- class=voice_tone scope=brand hardness=soft_guidance polarity=should sections=None constraint=None
- rule_text: When citing clinical data, maintain an empathetic, supportive, and trust-building tone. Avoid negative, fear-based language, and ensure data is presented clearly without oversimplification.
- intent: Foster reassurance and patient trust through clinical communication.

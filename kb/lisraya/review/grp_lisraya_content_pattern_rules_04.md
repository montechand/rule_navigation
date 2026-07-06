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

## Extracted rules (8)

### rule_lisraya_dm_abbrev_after_first_mention
- class=copy_editorial scope=brand hardness=strong_default polarity=should sections=None constraint=verbatim_content
- rule_text: After the first mention of "dermatomyositis," use "DM" in running copy to avoid repetition. The first-mention pattern is `dermatomyositis (DM)`.
- intent: Reduce repetition while keeping the term clear on first use.

### rule_lisraya_no_dm_abbrev_in_headings
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must_not sections=None constraint=binding
- rule_text: Do NOT use "DM" in headlines, headings, or subheads — always use the full word "dermatomyositis" there (for clarity, accessibility, and SEO on web).
- intent: Preserve clarity, accessibility, and SEO in prominent text.

### rule_lisraya_standalone_section_establishes_dm
- class=assembly scope=org_baseline hardness=hard_constraint polarity=must sections=None constraint=verbatim_content
- rule_text: [GENERAL] Because sections are assembled later, every standalone section must establish `dermatomyositis (DM)` at its own first mention, unless the assembly brief states the abbreviation is established upstream.
- intent: Ensure abbreviation is always introduced regardless of section ordering.

### rule_lisraya_inclusive_language_people_with_dm
- class=copy_editorial scope=brand hardness=hard_constraint polarity=must sections=None constraint=None
- rule_text: In patient materials, say "someone with dermatomyositis" / "people with dermatomyositis" — not "patients." "Patients" is acceptable only in HCP materials.
- intent: Use person-centered, inclusive language for patient audiences.

### rule_lisraya_care_team_not_staff
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Use "care team" (not "staff") for the network of patients, HCPs, and support systems.
- intent: Consistent, inclusive terminology for the support network.

### rule_lisraya_number_style_spell_out_under_ten
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Spell out numbers zero–nine; use numerals for 10 and above. Exceptions — always use numerals for percentages, ages, and ratios. Percentages use the % sign (e.g., 74%).
- intent: Consistent number formatting across copy.

### rule_lisraya_data_tone_empathetic
- class=voice_tone scope=brand hardness=strong_default polarity=must sections=['efficacy'] constraint=None
- rule_text: When citing clinical data, avoid negative or fear-based language; use an empathetic, supportive, trust-building tone without oversimplifying. Example pattern: "Participants in the VALOR study taking LISRAYA had nearly 50% more improvement in their DM symptoms after one year compared to placebo."
- intent: Keep clinical data framing supportive and trust-building.

### rule_lisraya_oxford_comma_always
- class=copy_editorial scope=brand hardness=strong_default polarity=must sections=None constraint=None
- rule_text: Always use the Oxford/serial comma in series of 3 or more items.
- intent: Consistent punctuation across copy.

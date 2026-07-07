# Review: grp_lisraya_content_pattern_rules_05

doc_ref: `content_pattern_rules[5]`

## Original text

````
### Campaign Headline ("YOU DESERVE MORE")
- Set in **Agenda** (digital may use Agenda as live text for this headline only; email fallback: Nunito Sans ExtraBold).
- **ALL CAPS, always.**
- The letters **"D" (in DESERVE) and "M" (in MORE) are set at approximately 40% tint** of the headline color — a nod to the "d" and "m" of dermatomyositis.
- Two approved colorways: brand **Gold/Sunshine** or **Brand Blue** (tinted letters at 40% of the same hue).
- Stack as three lines (YOU / DESERVE / MORE) in hero placements, left-aligned.
- Full lockup copy: "**YOU DESERVE MORE.** So there's LISRAYA—the first targeted treatment for dermatomyositis."
````

## Extracted rules (3)

### rule_lisraya_campaign_headline_typography_you_deserve_more
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: The 'YOU DESERVE MORE' campaign headline is set in Agenda (digital may use Agenda as live text for this headline only; email fallback is Nunito Sans ExtraBold), ALL CAPS always. Two approved colorways only: brand Gold/Sunshine or Brand Blue. In hero placements it is stacked as three lines (YOU / DESERVE / MORE), left-aligned.
- intent: Lock the distinctive campaign headline treatment for consistent recognition.

### rule_lisraya_campaign_headline_tinted_letters
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: In the 'YOU DESERVE MORE' headline the letters 'D' (in DESERVE) and 'M' (in MORE) are set at approximately 40% tint of the headline color (the same hue as the chosen colorway) — a nod to the 'd' and 'm' of dermatomyositis.
- intent: Preserve the intentional dermatomyositis 'd/m' visual cue in the headline.

### rule_lisraya_campaign_headline_full_lockup_copy
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=verbatim_content governance=mlr_claim/verbatim_only
- rule_text: The full campaign lockup copy is verbatim: 'YOU DESERVE MORE. So there's LISRAYA—the first targeted treatment for dermatomyositis.'
- intent: Keep the approved lockup and 'first targeted treatment' claim wording exact.

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

## Extracted rules (2)

### rule_lisraya_campaign_headline_you_deserve_more_type
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: The 'YOU DESERVE MORE' campaign headline is set in Agenda (campaign_headline.font); digital may use Agenda as live text for this headline only, with email fallback Nunito Sans ExtraBold. It is ALL CAPS, always (campaign_headline.case). Two approved colorways only: brand Gold/Sunshine or Brand Blue (campaign_headline.color). The letters 'D' (in DESERVE) and 'M' (in MORE) are set at approximately 40% tint of the headline color / same hue (campaign_headline.dm_letters.tint) — a nod to the 'd' and 'm' of dermatomyositis. In hero placements the headline is stacked as three lines (YOU / DESERVE / MORE), left-aligned (campaign_headline.alignment).
- intent: Ensure the signature campaign headline lockup renders in its locked type, casing, colorway, tinted DM letters, and hero layout.

### rule_lisraya_campaign_headline_you_deserve_more_lockup_copy
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=verbatim_content
- rule_text: The full campaign lockup copy is verbatim: 'YOU DESERVE MORE. So there's LISRAYA—the first targeted treatment for dermatomyositis.'
- intent: Preserve the MLR-approved verbatim campaign lockup copy.

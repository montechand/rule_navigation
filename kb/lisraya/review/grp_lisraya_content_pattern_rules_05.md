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

### rule_lisraya_campaign_headline_you_deserve_more_typography
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: The 'YOU DESERVE MORE' campaign headline is set in Agenda (digital may use Agenda as live text for this headline only; email fallback: Nunito Sans ExtraBold) and is ALL CAPS, always. Two approved colorways: brand Gold/Sunshine or Brand Blue. The letters 'D' (in DESERVE) and 'M' (in MORE) are set at approximately 40% tint of the headline color (same hue) — a nod to the 'd' and 'm' of dermatomyositis. In hero placements the headline stacks as three lines (YOU / DESERVE / MORE), left-aligned.
- intent: Preserve the distinctive, MLR-approved campaign headline lockup and its dermatomyositis letter-tint device.

### rule_lisraya_campaign_headline_lockup_verbatim_copy
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=verbatim_content
- rule_text: The full campaign lockup copy is verbatim: 'YOU DESERVE MORE. So there's LISRAYA—the first targeted treatment for dermatomyositis.'
- intent: Lock the approved full lockup copy exactly as written.

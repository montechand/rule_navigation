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

### rule_lisraya_campaign_headline_typography_lockup
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: The 'YOU DESERVE MORE' campaign headline is set in Agenda (digital may use Agenda as live text for this headline only; email fallback Nunito Sans ExtraBold), ALL CAPS always. It uses one of two approved colorways: Gold/Sunshine or Brand Blue (campaign_headline.color). The letters 'D' (in DESERVE) and 'M' (in MORE) are set at approximately 40% tint of the headline color — a nod to the 'd' and 'm' of dermatomyositis. In hero placements the headline stacks as three lines (YOU / DESERVE / MORE), left-aligned.
- intent: Preserve the signature campaign headline lockup styling and its DM tint nod.

### rule_lisraya_campaign_headline_email_fallback_font
- class=typography scope=campaign hardness=strong_default polarity=must sections=['hero'] constraint=binding
- rule_text: In email, the campaign headline falls back to Nunito Sans ExtraBold (Agenda as live text is reserved for digital surfaces on this headline only).
- intent: Ensure email rendering degrades to the approved web-safe font weight.

### rule_lisraya_campaign_headline_lockup_copy
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=verbatim_content
- rule_text: The full campaign lockup copy is verbatim: 'YOU DESERVE MORE. So there's LISRAYA—the first targeted treatment for dermatomyositis.'
- intent: Lock the MLR-approved campaign lockup wording.

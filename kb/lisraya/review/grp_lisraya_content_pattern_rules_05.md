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

## Extracted rules (6)

### rule_lisraya_campaign_headline_font_agenda
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: The campaign headline 'YOU DESERVE MORE' is set in Agenda. Digital may use Agenda as live text for this headline only; email fallback is Nunito Sans ExtraBold.
- intent: Preserve the distinctive campaign headline typeface across surfaces.

### rule_lisraya_campaign_headline_all_caps_2
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: The campaign headline 'YOU DESERVE MORE' must be set in ALL CAPS, always.
- intent: Maintain the fixed visual treatment of the campaign headline lockup.

### rule_lisraya_campaign_headline_tinted_letters
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: In the campaign headline, the letters 'D' (in DESERVE) and 'M' (in MORE) are set at approximately 40% tint of the headline color — a nod to the 'd' and 'm' of dermatomyositis.
- intent: Encode the branded dermatomyositis reference into the headline styling.

### rule_lisraya_campaign_headline_approved_colorways
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=exclusivity
- rule_text: The campaign headline has two approved colorways only: brand Gold/Sunshine, or Brand Blue. In either case the tinted letters are at 40% of the same hue.
- intent: Restrict the campaign headline to approved colorways.

### rule_lisraya_campaign_headline_hero_stacking
- class=layout scope=campaign hardness=strong_default polarity=must sections=['hero'] constraint=ordering
- rule_text: In hero placements, stack the campaign headline as three lines (YOU / DESERVE / MORE), left-aligned.
- intent: Standardize the hero layout of the campaign headline.

### rule_lisraya_campaign_headline_full_lockup_copy
- class=copy_editorial scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=verbatim_content
- rule_text: The full campaign lockup copy is verbatim: 'YOU DESERVE MORE. So there's LISRAYA—the first targeted treatment for dermatomyositis.'
- intent: Preserve the approved, verbatim campaign lockup copy.

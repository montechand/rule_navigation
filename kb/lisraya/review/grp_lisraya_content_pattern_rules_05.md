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

## Extracted rules (1)

### rule_lisraya_campaign_headline_lockup
- class=typography scope=campaign hardness=hard_constraint polarity=must sections=['hero'] constraint=binding
- rule_text: The campaign headline 'YOU DESERVE MORE' must be set in Agenda font (fallback: 'Nunito Sans', Verdana, Helvetica, Arial, sans-serif) in ALL CAPS, left-aligned, stacked as three lines in hero placements. The letters 'D' (in DESERVE) and 'M' (in MORE) are set at approximately 40% tint (opacity.campaign.headline_char_tint = 0.4) of the headline color, using either Brand Blue (color.primary.brand_blue = #00529b) or Gold/Sunshine (color.primary.gold = #ffc60a) colorways.
- intent: Maintain the conceptual campaign identity and specific brand typographic treatment honoring dermatomyositis.

# Review: grp_lisraya_color_scheme_rules_05

doc_ref: `color_scheme_rules[5]`

## Original text

````
### [IMPORTANT] Gradient Callout CTA Section Rule
 
A full-width banner where a **headline** and a **single button** are overlaid on the branded orange/yellow gradient image, both horizontally centered and stacked.
 
**Layout (explicit):**
 
- **Background** → the gradient PNG, applied as the section background, sized `cover`, `no-repeat`, centered, spanning the full content width (600px). Always set a solid `background-color` of Sunshine `#faa31b` as fallback, since clients like Outlook drop background images.
- **Headline** → Brand Blue `#00529b`, centered, sitting in the **top third**, Nunito Sans weight 800, ~28px, one line.
- **Button** → centered, in the **lower-middle** below the headline. Fill Deep Blue `#003D74`, white label (Nunito Sans 800, 18px), with a Gold `#FFC20E` arrow `›` (24px) after two non-breaking spaces. Size 248 × 64px.
**Background image:** asset is `https://solstice-public-forever.s3.us-east-1.amazonaws.com/design_library/12912e15-c371-4bf0-a5b9-08a7f8c57d20/7772aba5-1ff5-4985-80bf-c15b782111a4/Gradient_callout.png` — do not re-host or recolor. The background may be skipped **only in very, very rare cases** (plain-text/AMP fallback, a client that strips all images, a hard size budget). When skipped, the section still renders on a solid Sunshine `#faa31b` fill and every other rule stays identical.
 
**Button radius (mandatory, never change):** `border-radius: 49.52px 1.76px 40px 1.76px;` — this four-value asymmetric radius is the signature shape and is **always required on every instance**, even when the background is skipped. Never simplify it to a single value, swap the corners, or round the decimals.
 
## MJML
 
```xml
<mj-section
    background-url="https://solstice-public-forever.s3.us-east-1.amazonaws.com/design_library/12912e15-c371-4bf0-a5b9-08a7f8c57d20/7772aba5-1ff5-4985-80bf-c15b782111a4/Gradient_callout.png"
    background-size="cover"
    background-repeat="no-repeat"
    background-position="center center"
    background-color="#faa31b"
    padding="48px 25px 56px 25px">
  <mj-column width="100%">
 
    <mj-text
        align="center"
        color="#00529b"
        font-family="Nunito Sans, Arial, Helvetica, sans-serif"
        font-size="28px"
        font-weight="800"
        line-height="34px"
        padding="0 0 32px 0">
      Talk to your doctor about how LISRAYA can help
    </mj-text>
 
    <mj-text align="center" padding="0">
      <a href="https://www.LISRAYA.com" target="_blank" class="lisraya-cta-btn"
         style="display:inline-block;width:248px;height:64px;background-color:#003D74;color:#ffffff;font-family:'Nunito Sans',Arial,Helvetica,sans-serif;font-size:18px;font-weight:800;line-height:64px;text-align:center;text-decoration:none;border-radius:49.52px 1.76px 40px 1.76px;">
        Visit LISRAYA.com&nbsp;&nbsp;<span style="color:#FFC20E;font-size:24px;">&#10095;</span>
      </a>
    </mj-text>
 
  </mj-column>
</mj-section>
```
 
If the background must be skipped, remove only `background-url`, `background-size`, `background-repeat`, and `background-position` — keep `background-color="#faa31b"` and the headline color, button color, and button radius exactly as above.
````

## Extracted rules (8)

### rule_lisraya_gradient_callout_layout_structure
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['cta', 'callout'] constraint=ordering
- rule_text: The Gradient Callout CTA Section is a full-width banner where a headline and a single button are overlaid on the branded orange/yellow gradient image, both horizontally centered and stacked (headline above, button below).
- intent: Define the canonical layout for the Gradient Callout CTA.

### rule_lisraya_gradient_callout_background_image
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=['cta', 'callout'] constraint=binding
- rule_text: The gradient PNG (ast_lisraya_gradient_callout_bg) must be applied as the section background, sized `cover`, `no-repeat`, centered, spanning the full content width (600px).
- intent: Lock the correct background asset and sizing for the callout.

### rule_lisraya_gradient_callout_bg_fallback_color
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['cta', 'callout'] constraint=binding
- rule_text: Always set a solid `background-color` of Sunshine #faa31b as fallback on the Gradient Callout section, since clients like Outlook drop background images.
- intent: Ensure a branded fallback when the background image is dropped.

### rule_lisraya_gradient_callout_no_rehost_recolor
- class=imagery scope=brand hardness=hard_constraint polarity=must_not sections=['cta', 'callout'] constraint=verbatim_content
- rule_text: The Gradient Callout background image (hosted at the Solstice S3 URL) must not be re-hosted or recolored.
- intent: Protect the integrity of the branded gradient asset.

### rule_lisraya_gradient_callout_headline_style
- class=typography scope=brand hardness=hard_constraint polarity=must sections=['cta', 'callout'] constraint=binding
- rule_text: The headline is Brand Blue #00529b, centered, sitting in the top third, Nunito Sans weight 800, ~28px, one line.
- intent: Lock the headline appearance for the callout.

### rule_lisraya_gradient_callout_button_style
- class=cta scope=brand hardness=hard_constraint polarity=must sections=['cta', 'callout'] constraint=binding
- rule_text: The button is centered in the lower-middle below the headline. Fill Deep Blue #003D74, white label (Nunito Sans 800, 18px), with a Gold #FFC20E arrow `›` (24px) after two non-breaking spaces. Size 248 × 64px.
- intent: Lock the button color, label, arrow, and size for the callout.

### rule_lisraya_gradient_callout_button_radius_locked
- class=cta scope=brand hardness=hard_constraint polarity=must sections=['cta', 'callout'] constraint=binding
- rule_text: The button must use the signature asymmetric radius `border-radius: 49.52px 1.76px 40px 1.76px;` on every instance, even when the background is skipped. Never simplify it to a single value, swap the corners, or round the decimals.
- intent: Preserve the signature asymmetric button shape exactly.

### rule_lisraya_gradient_callout_background_skip_exception
- class=assembly scope=brand hardness=strong_default polarity=may sections=['cta', 'callout'] constraint=None
- rule_text: The background image may be skipped only in very, very rare cases (plain-text/AMP fallback, a client that strips all images, a hard size budget). When skipped, remove only `background-url`, `background-size`, `background-repeat`, and `background-position` — keep `background-color="#faa31b"` and the headline color, button color, and button radius exactly as above; every other rule stays identical.
- intent: Constrain when and how the background may be omitted while preserving all other specs.

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

## Extracted rules (3)

### rule_lisraya_gradient_callout_layout_composition
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['cta', 'callout'] constraint=binding
- rule_text: The Gradient Callout CTA Section is a full-width banner (600px content width) where a single headline and a single button are overlaid on the branded orange/yellow gradient image, both horizontally centered and vertically stacked. The background is the gradient PNG applied as the section background sized cover, no-repeat, centered. The headline (gradient_callout.headline: Brand Blue #00529b, Nunito Sans weight 800, ~28px, one line) sits in the top third; the button (gradient_callout.button: Deep Blue #003D74 fill, white Nunito Sans 800 18px label, Gold #FFC20E arrow '›' at 24px following two non-breaking spaces, 248×64px) sits in the lower-middle below the headline. All values are carried by the bound gradient_callout tokens.
- intent: Lock the composition and element bindings of the signature gradient callout CTA banner.

### rule_lisraya_gradient_callout_background_asset_integrity
- class=imagery scope=brand hardness=hard_constraint polarity=must_not sections=['cta', 'callout'] constraint=binding
- rule_text: The Gradient Callout background asset (Gradient_callout.png) must not be re-hosted or recolored. A solid Sunshine #faa31b background-color must always be set as fallback since clients like Outlook drop background images. The background image may be skipped only in very, very rare cases (plain-text/AMP fallback, a client that strips all images, a hard size budget); when skipped, remove only background-url/size/repeat/position, keep background-color #faa31b, and every other rule (headline color, button color, button radius) stays identical.
- intent: Preserve the integrity of the branded gradient asset and guarantee a graceful, on-brand fallback.

### rule_lisraya_gradient_callout_button_signature_radius
- class=cta scope=brand hardness=hard_constraint polarity=must sections=['cta', 'callout'] constraint=binding
- rule_text: The Gradient Callout button's four-value asymmetric border-radius (49.52px 1.76px 40px 1.76px) is the signature shape and is mandatory on every instance, even when the background is skipped. Never simplify it to a single value, swap the corners, or round the decimals.
- intent: Protect the button's signature asymmetric radius as a brand identifier.

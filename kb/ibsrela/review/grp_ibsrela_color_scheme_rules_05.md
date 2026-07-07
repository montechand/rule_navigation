# Review: grp_ibsrela_color_scheme_rules_05

doc_ref: `color_scheme_rules[5]`

## Original text

````
# CTA Section — Color & Image Rules

The system reduces to two background groups: **light** (White, Silver) and **dark** (Dark Gray, Purple, Dark Blue, Green). Everything flips between these two groups.

## Button rule (explicit)

- On **light** backgrounds — White `#FFFFFF`, Silver `#CFDCE3` → use the **Green filled button** (`#01A47E`) with **white** label text (`#FFFFFF`).
- On **dark** backgrounds — Dark Gray `#567483`, Purple `#92278F`, Dark Blue `#262262`, Green `#01A47E`, Teal `#0F99BC`, or Periwinkle `#7B7BED` → use the **White filled button** (`#FFFFFF`) with **green** label text (`#01A47E`).

One-line version: *light background → green button / white label; dark background → white button / green label.*

## Quick lookup table

| Section background | Heading color | Body color | CTA button fill | CTA label color |
|---|---|---|---|---|
| White `#FFFFFF` | Dark Blue `#262262` | Black `#000000` | Green `#01A47E` | White `#FFFFFF` |
| Silver `#CFDCE3` | Dark Blue `#262262` | Black `#000000` | Green `#01A47E` | White `#FFFFFF` |
| Dark Gray `#567483` | White `#FFFFFF` | White `#FFFFFF` | White `#FFFFFF` | Green `#01A47E` |
| Purple `#92278F` | White `#FFFFFF` | White `#FFFFFF` | White `#FFFFFF` | Green `#01A47E` |
| Dark Blue `#262262` | White `#FFFFFF` | White `#FFFFFF` | White `#FFFFFF` | Green `#01A47E` |
| Green `#01A47E` | White `#FFFFFF` | White `#FFFFFF` | White `#FFFFFF` | Green `#01A47E` |
| Teal `#0F99BC` (LPGA only) | White `#FFFFFF` | White `#FFFFFF` | White `#FFFFFF` | Green `#01A47E` |
| Periwinkle `#7B7BED` | White `#FFFFFF` | White `#FFFFFF` | White `#FFFFFF` | Green `#01A47E` |

---

## CTA right-side image rule
<image_rule>

The CTA section can carry an image on the **right side**. There are **three approved image options**, and these are the ones that will be used in the vast majority of cases. **Each image is locked to a specific CTA section background color** — they are not interchangeable. Pick the image based on the email's content, then set the CTA background to that image's required color.

**When the CTA section should NOT have an image:** if there is already a populated content section directly above the CTA, the CTA runs image-free (text + button only). In that case, skip the right-side image and place the CTA on an approved background from the lookup table.

### The three approved right-side images

| Image | When to use | Required CTA section background |
|---|---|---|
| [`Email_Primary_2_column.png`](https://solstice-public-forever.s3.us-east-1.amazonaws.com/design_library/affda42b-9fe3-4320-8f85-de496892905d/7772aba5-1ff5-4985-80bf-c15b782111a4/Email_Primary_2_column.png) | Default / general CTA | Purple `#92278F` |
| [`Email_Primary_column_golf.png`](https://solstice-public-forever.s3.us-east-1.amazonaws.com/design_library/affda42b-9fe3-4320-8f85-de496892905d/7772aba5-1ff5-4985-80bf-c15b782111a4/Email_Primary_column_golf.png) | **Only** when the email contains LPGA content | Teal `#0F99BC` |
| [`Cake_lockup.png`](https://solstice-public-forever.s3.us-east-1.amazonaws.com/design_library/affda42b-9fe3-4320-8f85-de496892905d/7772aba5-1ff5-4985-80bf-c15b782111a4/Cake_lockup.png) | General CTA (alternate visual) | Periwinkle `#7B7BED` |

### How the rest of the section follows

Because all approved backgrounds (`#92278F`, `#0F99BC`, and `#7B7BED`) are in the **dark** group, the section always uses:

- Heading: White `#FFFFFF`
- Body: White `#FFFFFF`
- CTA button fill: White `#FFFFFF`
- CTA label: Green `#01A47E`

### Notes & guardrails

- **One image per background.** Do not place `Email_Primary_2_column.png` on a teal background, and do not place `Email_Primary_column_golf.png` on a purple (or any non-teal) background.
- **The golf image is LPGA-gated.** If the email has no LPGA content, do not use the golf asset and do not use the `#0F99BC` background.
- **`#0F99BC` is reserved.** Teal is only valid as a CTA section background when paired with the LPGA golf image — it is not a general-purpose background elsewhere in the system.
- **No image when a populated section sits on top of the CTA.** Run the CTA image-free (text + button only) on an approved background from the lookup table.

---

## Sample MJML

### A. CTA with right-side image (default — Purple + `Email_Primary_2_column.png`)

This is the default variant: text + button on the left, approved image on the right, on the image's required background color. Heading/body are white, button is white-filled with a green label per the dark-background rule.

```mjml
<!-- CTA SECTION: image variant (default) -->
<!-- Background MUST match the chosen image: Purple #92278F -> Email_Primary_2_column.png -->
<mj-section background-color="#92278F" padding="40px 24px">
  <!-- LEFT: copy + button -->
  <mj-column width="58%" vertical-align="middle">
    <mj-text
      align="left"
      color="#FFFFFF"
      font-family="Arial, Helvetica, sans-serif"
      font-size="28px"
      font-weight="700"
      line-height="1.25"
      padding="0 0 12px 0">
      Care that meets your team where they are
    </mj-text>

    <mj-text
      align="left"
      color="#FFFFFF"
      font-family="Arial, Helvetica, sans-serif"
      font-size="16px"
      line-height="1.5"
      padding="0 0 24px 0">
      Give members one place to find providers, book visits, and get answers — fast.
    </mj-text>

    <!-- Dark background -> WHITE button fill, GREEN label -->
    <mj-button
      href="https://www.example.com/get-started"
      background-color="#FFFFFF"
      color="#01A47E"
      font-family="Arial, Helvetica, sans-serif"
      font-size="16px"
      font-weight="700"
      border-radius="500px"
      inner-padding="14px 28px"
      align="left"
      padding="0">
      Get started
    </mj-button>
  </mj-column>

  <!-- RIGHT: approved image, locked to this background -->
  <mj-column width="42%" vertical-align="middle">
    <mj-image
      src="https://solstice-public-forever.s3.us-east-1.amazonaws.com/design_library/affda42b-9fe3-4320-8f85-de496892905d/7772aba5-1ff5-4985-80bf-c15b782111a4/Email_Primary_2_column.png"
      alt="Solstice"
      align="center"
      padding="0" />
  </mj-column>
</mj-section>
```

> Swap variants by changing **both** the `background-color` and the image `src` together:
> - LPGA content → `background-color="#0F99BC"` + `Email_Primary_column_golf.png`
> - Alternate general → `background-color="#7B7BED"` + `Cake_lady_lockup.png`

### B. CTA image-free (a populated section sits directly above)

Text + button only, on an approved background from the lookup table. Example shown on a **light** background (Silver), so the button flips to **green-filled with a white label**.

```mjml
<!-- CTA SECTION: image-free variant (use when a populated section is directly above) -->
<!-- Light background (Silver #CFDCE3) -> GREEN button fill, WHITE label -->
<mj-section background-color="#CFDCE3" padding="40px 24px">
  <mj-column width="100%">
    <mj-text
      align="left"
      color="#262262"
      font-family="Arial, Helvetica, sans-serif"
      font-size="26px"
      font-weight="700"
      line-height="1.25"
      padding="0 0 12px 0">
      Ready to see it in action?
    </mj-text>

    <mj-text
      align="left"
      color="#000000"
      font-family="Arial, Helvetica, sans-serif"
      font-size="16px"
      line-height="1.5"
      padding="0 0 24px 0">
      Book a 15-minute walkthrough with our team.
    </mj-text>

    <mj-button
      href="https://www.example.com/demo"
      background-color="#01A47E"
      color="#FFFFFF"
      font-family="Arial, Helvetica, sans-serif"
      font-size="16px"
      font-weight="700"
      border-radius="500px"
      inner-padding="14px 28px"
      align="left"
      padding="0">
      Book a demo
    </mj-button>
  </mj-column>
</mj-section>
```
````

## Extracted rules (4)

### rule_ibsrela_cta_button_fill_label_by_background_group
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=['cta'] constraint=binding
- rule_text: The system reduces to two background groups: light (White, Silver) and dark (Dark Gray, Purple, Dark Blue, Green, Teal, Periwinkle), and CTA styling flips between them. On light backgrounds use the green filled button (#01A47E) with a white label (#FFFFFF); on dark backgrounds use the white filled button (#FFFFFF) with a green label (#01A47E). Heading and body colors follow the same group switching (Dark Blue heading / black body on light; white heading and body on dark). Background-group value switching lives on the bound semantic tokens (cta.button.fill, cta.button.label.color, h1.color, body.color).
- intent: Ensure CTA button and text colors always contrast correctly by flipping as a set with the section's light/dark background group.

### rule_ibsrela_cta_right_image_locked_to_background
- class=imagery scope=brand hardness=hard_constraint polarity=must sections=['cta'] constraint=pairing
- rule_text: The CTA section may carry a right-side image. There are three approved image options, each LOCKED to a specific CTA section background color — they are not interchangeable: Email_Primary_2_column.png (default/general CTA) requires Purple #92278F; Cake_lockup.png (alternate general CTA) requires Periwinkle #7B7BED; Email_Primary_column_golf.png requires Teal #0F99BC. Pick the image based on content, then set the CTA background to that image's required color. Do not place Email_Primary_2_column.png on teal, and do not place the golf image on purple or any non-teal background. Because all three approved backgrounds are in the dark group, the section always uses white heading, white body, white button fill, and green label. Swap variants by changing both the background-color and the image src together.
- intent: Preserve approved, MLR-locked image/background pairings so CTA imagery is never mismatched to its background.

### rule_ibsrela_cta_teal_golf_lpga_gated
- class=color_application scope=campaign hardness=hard_constraint polarity=must sections=['cta'] constraint=exclusivity
- rule_text: The golf image is LPGA-gated: use Email_Primary_column_golf.png and the Teal #0F99BC background only when the email contains LPGA content. If the email has no LPGA content, do not use the golf asset and do not use the #0F99BC background. Teal is reserved exclusively as a CTA section background paired with the LPGA golf image and is not a general-purpose background elsewhere in the system.
- intent: Keep Teal/golf usage restricted to LPGA-content emails only.

### rule_ibsrela_cta_image_free_when_section_above
- class=layout scope=brand hardness=strong_default polarity=must sections=['cta'] constraint=binding
- rule_text: When a populated content section sits directly above the CTA, run the CTA image-free (text + button only): skip the right-side image and place the CTA on an approved background from the lookup table. On a light background (e.g. Silver) the button flips to green fill with a white label per the background-group rule.
- intent: Avoid image redundancy/crowding when the CTA follows an already-populated section.

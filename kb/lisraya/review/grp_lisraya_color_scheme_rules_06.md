# Review: grp_lisraya_color_scheme_rules_06

doc_ref: `color_scheme_rules[6]`

## Original text

````
### [IMPORTANT] Icon Callout Box Rule

A **light-blue accent-shape box** containing a short blue headline, with a **white icon badge that straddles the box's left edge** � the edge runs through the badge's center so it reads as half-on / half-off the box. Used for supporting "proof point" statements (dosing convenience, time-to-effect, etc.).

**Layout (explicit):**

- **Container** ? the callout sits on the page/section background (usually White `#ffffff`). The blue box itself is **inset from the left by half the badge width** so the badge's outer half has room � this is the "box gets a little smaller on the left" step. Everything else stays full content width.
- **Box** ? Light Blue `#E6F0F9` fill, single accent shape. Vertically sized to its text with generous padding; the **left padding must clear the overhanging badge half plus a gap** (? `W/2 + 24px`).
- **Text** ? Brand Blue `#00529b`, Nunito Sans weight 800, ~21px / 28px line-height, left-aligned, **vertically centered** to the box. Never let copy slide under the badge.
- **Icon badge** ? a **White `#ffffff` rounded square** holding the line icon (Brand Blue stroke), **vertically centered** on the box and **horizontally centered on the box's left edge** (the edge is the badge's perpendicular bisector ? 50% over the blue, 50% over the page background).

**Geometry (the part that makes it exact):**

- Let `W` = badge width (use **80px**, icon ?48px inside).
- Inset the blue box from the left by **`W/2` = 40px**, and place the badge so its **center lands exactly on the box's left edge** (badge `left:0` inside a `padding-left:40px` wrapper ? badge center `40px` = box edge). Distance from badge center to box edge must be **`0`**.
- Vertical center via `top:50%` + `margin-top:?40px` (half the badge height).

**Corner radius (mandatory, never change):** box `border-radius: 40px 8px 40px 8px;` in `TL TR BR BL` order � large on **top-left + bottom-right**, near-point on **top-right + bottom-left**, a **5:1 ratio**. The white badge **mirrors the same accent shape at smaller scale**, `border-radius: 20px 4px 20px 4px;` (also 5:1, large TL+BR). Never simplify either to a single uniform radius, swap the corners, or flip the diagonal.

**Drop shadow (mandatory):** the white icon badge **must carry a subtle drop shadow** so it lifts off the blue box � e.g. `box-shadow: 0 4px 10px rgba(1, 30, 69, 0.18);` (Dark Navy at low opacity). This shadow is required on every instance; without it the badge looks flat and pasted-on.

## Palette reference

| Token | HEX | Use here |
|---|---|---|
| Brand Blue | `#00529b` | Headline text + icon stroke |
| Light Blue | `#E6F0F9` | Box fill |
| White | `#ffffff` | Icon badge fill |
| Dark Navy | `#011E45` | Drop-shadow color (low opacity) |

## MJML

```xml
<mj-section background-color="#ffffff" padding="16px 25px">
  <mj-column width="100%" padding="0">
    <mj-text padding="0">
      <!--
        Icon callout. Wrapper has padding-left = W/2 (40px) so the blue box is
        inset and the badge's outer half has room. Badge is absolutely positioned
        with its CENTER on the box's left edge (left:0 + wrapper pad 40px) ->
        perpendicular-bisector 50/50 split, vertically centered.
      -->
      <div style="position:relative; padding-left:40px;">

        <!-- Light Blue accent-shape box (large TL+BR, point TR+BL = 5:1) -->
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:separate;">
          <tr>
            <td style="background-color:#E6F0F9; border-radius:40px 8px 40px 8px; padding:26px 34px 26px 64px;">
              <span style="font-family:'Nunito Sans',Arial,Helvetica,sans-serif; font-size:21px; line-height:28px; font-weight:800; color:#00529b;">
                These improvements occurred as early as four weeks after starting treatment, and they continued getting better through the end of the 52-week study.
              </span>
            </td>
          </tr>
        </table>

        <!-- White icon badge: mirrors accent radii (20/4/20/4), drop shadow, centered on the edge -->
        <div style="position:absolute; left:0; top:50%; margin-top:-40px; width:80px; height:80px; background-color:#ffffff; border-radius:20px 4px 20px 4px; box-shadow:0 4px 10px rgba(1,30,69,0.18); text-align:center; line-height:80px;">
          <img src="ICON_URL" alt="" width="48" height="48" style="vertical-align:middle; border:0;" />
        </div>

      </div>
    </mj-text>
  </mj-column>
</mj-section>
```

## Email fallback caveats (important)

The 50/50 overhang relies on `position:absolute`, which Apple Mail / iOS / most web clients honor but **Outlook (desktop, Word engine) ignores** � there the badge drops to the top-left in normal flow and the box won't be inset. For pixel-perfect fidelity across **all** clients, the brand-safe option is to **pre-composite the white badge (with its shadow, accent radii, and icon) as a transparent PNG** and place it via the same absolute positioning, or bake the entire badge-on-edge treatment into the box's background image while keeping the text live. When that's not feasible, ship the live version above and accept the Outlook degrade (badge flush at the inner-left edge) � every other rule (Light Blue fill, `40px 8px 40px 8px` radius, blue 800 text, drop shadow) stays identical.

## Scaling note

Defaults: badge size `W = 80px`, inner icon `48px`. If your real badge is a different size, keep the relationships � **inset = `W/2`**, **box left-padding = `W/2 + 24px`**, **badge `margin-top` = `?H/2`** � and the bisector stays exact.

````

## Extracted rules (5)

### rule_lisraya_icon_callout_box_structure_style
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: The Icon Callout Box is a light-blue (#E6F0F9) single accent-shape box holding a short Brand Blue (#00529b) headline in Nunito Sans weight 800 at ~21px/28px, left-aligned and vertically centered, with a white (#ffffff) rounded-square icon badge (Brand Blue line-icon stroke) straddling the box's left edge. Used for supporting 'proof point' statements (dosing convenience, time-to-effect, etc.). The box sits on the page/section background (usually White #ffffff), the text is vertically centered, and copy must never slide under the badge.
- intent: Define the branded proof-point callout device with its locked fills, type, and geometry tokens.

### rule_lisraya_icon_callout_badge_edge_geometry
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: Geometry is exact: with badge width W (default 80px, inner icon 48px), inset the blue box from the left by W/2 (=40px) via a padding-left:40px wrapper, and place the badge (left:0) so its center lands exactly on the box's left edge — distance from badge center to box edge must be 0, giving a 50/50 split over the blue box and page background. Vertically center via top:50% + margin-top:-40px (half badge height). The box left-padding must clear the overhanging badge half plus a gap (≈ W/2 + 24px). If the badge is a different size, keep the relationships: inset = W/2, box left-padding = W/2 + 24px, badge margin-top = -H/2, so the bisector stays exact.
- intent: Lock the badge-on-edge bisector geometry so the half-on/half-off treatment is pixel-exact and scales.

### rule_lisraya_icon_callout_accent_radius_never_change
- class=layout scope=brand hardness=hard_constraint polarity=must_not sections=['callout'] constraint=binding
- rule_text: Corner radius is mandatory and must never change: the box is border-radius 40px 8px 40px 8px (TL TR BR BL) — large on top-left + bottom-right, near-point on top-right + bottom-left, a 5:1 ratio. The white badge mirrors the same accent shape at smaller scale, border-radius 20px 4px 20px 4px (also 5:1, large TL+BR). Never simplify either to a single uniform radius, swap the corners, or flip the diagonal.
- intent: Preserve the signature 5:1 asymmetric accent-shape identity on both box and badge.

### rule_lisraya_icon_callout_badge_drop_shadow_required
- class=layout scope=brand hardness=hard_constraint polarity=must sections=['callout'] constraint=binding
- rule_text: The white icon badge must carry a subtle drop shadow so it lifts off the blue box — box-shadow: 0 4px 10px rgba(1,30,69,0.18) (Dark Navy at low opacity). This shadow is required on every instance; without it the badge looks flat and pasted-on.
- intent: Ensure the badge reads as lifted off the box on every instance.

### rule_lisraya_icon_callout_outlook_fallback
- class=assembly scope=brand hardness=soft_guidance polarity=should sections=['callout'] constraint=None
- rule_text: The 50/50 overhang relies on position:absolute, which Apple Mail / iOS / most web clients honor but Outlook (desktop, Word engine) ignores — there the badge drops to the top-left in normal flow and the box won't be inset. For pixel-perfect fidelity across all clients, the brand-safe option is to pre-composite the white badge (with its shadow, accent radii, and icon) as a transparent PNG placed via the same absolute positioning, or bake the entire badge-on-edge treatment into the box's background image while keeping the text live. When that's not feasible, ship the live version and accept the Outlook degrade (badge flush at the inner-left edge); every other rule (Light Blue fill, 40px 8px 40px 8px radius, blue 800 text, drop shadow) stays identical.
- intent: Guide graceful degradation of the absolute-positioned badge in Outlook while preserving all other spec.

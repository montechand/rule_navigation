# Review: grp_lisraya_internal_banner_rules_00

doc_ref: `internal_banner_rules[0]`

## Original text

````

The three approved brand colors in hierarchy order are: (1) 
#00529B Deep Blue (dominant), (2) 
#FAA31B Amber Orange (secondary accent), (3) 
#FFC60A Golden Yellow (tertiary accent).

Agenda, is the primary headline font
and should be used for all headlines and headers.
Nunito Sans should be used for
all body copy in print.

Agenda:


Nunito Sans:
https://fonts.googleapis.com/css2?family=Nunito+Sans:ital,opsz,wght@0,6..12,200..1000;1,6..12,200..1000&display=swap" rel="stylesheet

use this shape and treatment for CTAs:

<svg width="180" height="59" viewBox="0 0 180 59" fill="none" xmlns="http://www.w3.org/2000/svg"> <path d="M0 25C0 11.1929 11.1929 0 25 0H177.5C178.605 0 179.5 0.895431 179.5 2V33.5C179.5 47.3071 168.307 58.5 154.5 58.5H2C0.895433 58.5 0 57.6046 0 56.5V25Z" fill="url(#paint0_linear_75_5202)"/> <defs> <linearGradient id="paint0_linear_75_5202" x1="0" y1="29.25" x2="179.5" y2="29.25" gradientUnits="userSpaceOnUse"> <stop stop-color="`#FFDF55`"/> <stop offset="1" stop-color="`#FAA21B`"/> </linearGradient> </defs> </svg>
````

## Extracted rules (3)

### rule_lisraya_brand_color_hierarchy
- class=color_application scope=brand hardness=hard_constraint polarity=must sections=None constraint=ordering
- rule_text: The three approved brand colors must be used in hierarchy order: (1) #00529B Deep Blue as the dominant color, (2) #FAA31B Amber Orange as the secondary accent, (3) #FFC60A Golden Yellow as the tertiary accent. Palette hierarchy follows primary > secondary > tertiary.
- intent: Preserve brand color dominance and prevent accent overuse.

### rule_lisraya_headline_body_font_assignment
- class=typography scope=brand hardness=hard_constraint polarity=must sections=None constraint=binding
- rule_text: Agenda is the primary headline font and must be used for all headlines and headers. Nunito Sans must be used for all body copy in print. (Per the semantic font tokens, surface variants supply the email stack fallbacks.)
- intent: Enforce consistent brand typeface roles across headlines and body.

### rule_lisraya_cta_signature_svg_shape
- class=cta scope=brand hardness=hard_constraint polarity=must sections=['cta'] constraint=binding
- rule_text: Use the signature CTA SVG shape and treatment for CTAs (viewBox 0 0 180 58.5, rendered 180x59), filled with the CTA gradient (#FFDF55 -> #FAA21B).
- intent: Standardize the branded CTA button silhouette and gradient fill.

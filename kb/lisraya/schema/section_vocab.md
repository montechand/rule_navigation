# Section vocabulary (selector.section_types)

This vocabulary is DYNAMIC: a curated core plus brand-discovered section
devices (extraction proposes `other.<name>`; novel entries are registered
permanently in shared/registries.json).

## Core
hero — lead visual + headline block opening the email body
intro — opening copy establishing context/empathy
efficacy — clinical results, data claims, charts of outcomes
safety — safety info, side effects (content sections; full ISI lives in end_matter)
patient_story — testimonial/lifestyle narrative modules
affordability — pricing/copay/support-program content
cta — call-to-action section (button, optional right-side image)
callout — highlighted panel/box devices inside content
chart — data visualization blocks
top_matter — locked header component (logo, safety links)
end_matter — locked footer component (ISI, legal, unsubscribe)

A blueprint's free-form `section_id` values (e.g. "what_it_means") must be
mapped to the closest vocabulary entries by the querying agent; a section may
match several (e.g. a benefits panel = intro + callout).

Concrete templates/components (content_sub_type) declare which section types
they cover via `covers_section_types` (graph edge `covers_section`) — e.g. a
header template covering [top_matter, hero] bundles the locked header
obligations with the hero design rules.
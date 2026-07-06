# Section vocabulary (selector.section_types)

hero — lead visual + headline block opening the email body
intro — opening copy establishing context/empathy
efficacy — clinical results, data claims, charts of outcomes
safety — safety info, side effects (content sections; full ISI lives in end_matter)
patient_story — testimonial/lifestyle narrative modules
affordability — pricing/copay/support-program content
symptom_trio — the fixed three-symptom icon row (brand-specific device)
cta — call-to-action section (button, optional right-side image)
callout — highlighted panel/box devices inside content
chart — data visualization blocks
top_matter — locked header component (logo, safety links)
end_matter — locked footer component (ISI, legal, unsubscribe)

A blueprint's free-form `section_id` values (e.g. "what_it_means") must be mapped to the
closest vocabulary entries by the querying agent; a section may match several
(e.g. a benefits panel = intro + callout).

# Entity: design_asset

Approved visual asset (photo, icon, logo_lockup, svg_shape, wave, background,
campaign_lockup, cta_image).

- `uri`: storage location (S3 etc). `dims`: pixel dimensions if known.
- `description` / `alt_text`: semantic description and approved accessibility string.
- `contains_token_ids`: tokens the asset embodies and must preserve (palette integrity).
- `required_pairing_token_ids`: tokens that MUST accompany the asset (e.g. golf image ->
  teal background).
- `usage_conditions`: `{requires_content_tags: [], forbidden_content_tags: [],
  max_per_email: int?}`.
- `slot_compatibility`: which slots may carry it: hero, cta_right, icon_row, background, inline.
- `group_id` + `group_order`: ordered set membership (e.g. symptom icon trio).

# Output schema & allowed values (single source of truth for `output.csv`)

14 columns, in this exact order:

| # | column | meaning |
|---|---|---|
| 1 | `user_id` | echo of input |
| 2 | `image_paths` | echo of input (`;`-separated) |
| 3 | `user_claim` | echo of input transcript |
| 4 | `claim_object` | `car` \| `laptop` \| `package` |
| 5 | `evidence_standard_met` | `true` if the image set is sufficient to evaluate the claim, else `false` |
| 6 | `evidence_standard_met_reason` | short reason for the evidence decision |
| 7 | `risk_flags` | `;`-separated risk flags, or `none` |
| 8 | `issue_type` | visible issue type |
| 9 | `object_part` | relevant object part (must match `claim_object`'s list) |
| 10 | `claim_status` | `supported` \| `contradicted` \| `not_enough_information` |
| 11 | `claim_status_justification` | concise image-grounded explanation; cite image IDs when helpful |
| 12 | `supporting_image_ids` | `;`-separated image IDs supporting the decision, or `none` |
| 13 | `valid_image` | `true` if the image set is usable for automated review, else `false` |
| 14 | `severity` | `none` \| `low` \| `medium` \| `high` \| `unknown` |

## Allowed values
- **claim_status:** `supported`, `contradicted`, `not_enough_information`
- **issue_type:** `dent`, `scratch`, `crack`, `glass_shatter`, `broken_part`, `missing_part`,
  `torn_packaging`, `crushed_packaging`, `water_damage`, `stain`, `none`, `unknown`
  - use `none` when the part is visible and no issue is present; `unknown` when it cannot be determined.
- **severity:** `none`, `low`, `medium`, `high`, `unknown`
- **risk_flags:** `none`, `blurry_image`, `cropped_or_obstructed`, `low_light_or_glare`, `wrong_angle`,
  `wrong_object`, `wrong_object_part`, `damage_not_visible`, `claim_mismatch`, `possible_manipulation`,
  `non_original_image`, `text_instruction_present`, `user_history_risk`, `manual_review_required`
- **object_part by claim_object:**
  - `car`: `front_bumper`, `rear_bumper`, `door`, `hood`, `windshield`, `side_mirror`, `headlight`,
    `taillight`, `fender`, `quarter_panel`, `body`, `unknown`
  - `laptop`: `screen`, `keyboard`, `trackpad`, `hinge`, `lid`, `corner`, `port`, `base`, `body`,
    `unknown`
  - `package`: `box`, `package_corner`, `package_side`, `seal`, `label`, `contents`, `item`, `unknown`

## Formatting rules
- Image ID = filename without extension (`images/test/case_001/img_1.jpg` -> `img_1`).
- `risk_flags` and `supporting_image_ids` join multiple values with `;` and no spaces; never mix
  `none` with real values.
- Booleans are lowercase `true` / `false`. Quote every field; one output row per input row, same order.

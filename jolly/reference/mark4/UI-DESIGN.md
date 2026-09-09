# Mark 4 interface direction

A factory shift board, built around what each line can make next and why. The memorable element is a connected six-lane production board with a continuous time track; summary numbers support that decision rather than replacing it.

## Tokens
- Paper: #f1f6f8, a cool blue-grey working surface.
- Surface: #ffffff, for the board and readable tables.
- Ink: #18374a, a deep blue used for text and the narrow navigation rail.
- Teal: #087f82, for feasible production and selected controls.
- Blue: #446ca0, for observations and confirmed demand.
- Amber: #9d571b, for constraints and provisional rules, always accompanied by words.
- Type: system Avenir Next / Avenir with a sans-serif fallback; strong, compact headings and tabular numeric values. No monospace business labels.

## Layout
Desktop uses a narrow fixed navigation rail, a spacious title row, and the shift board across the main area. The scenario drawer sits beside the production board on wide displays; on iPad it becomes an ordinary section. Mobile uses horizontal navigation and stacked line rows with touchable controls. All information aligns left; numeric table columns align right.

    navigation | date + plan status              refresh
               | headline / latest source status
               | six-line shift board | what-if controls
               | production target / blocker reasons
               | recorded actuals, clearly separated

Other views share the same shell: plan calendar, machine rules/rates, material requirements, dispatch pendency, demand and actuals. The last page provides the complete readable rulebook, data limitations and concise questions.

## Review against brief
Removed the generic KPI-card hero: the product is about machine behavior, so line recommendations lead. Avoided dark dashboards, decorative gradients, tiny uppercase labels and identical cards. A compact target meter stays below the board to answer whether the proposed runs approach the production-value target. Constraints explain the missing material and affected product; they are not red dots with no next action.

## Interaction and truth
- Scenario controls recompute the engine through the API; one night line only.
- Selected scenario is visibly a simulation, never a factory instruction or recorded fact.
- Unknown/unread values remain text, not zero.
- All business values originate in the model contract. Frontend calculates only formatting and view-level aggregations, never manufacturing quantities.
- Loading, refresh failure, stale source data, empty filtered tables, keyboard focus and reduced motion are explicit.
- Actual production records remain separate from planned future runs. Rule provenance and unresolved rates are visible.

You are working with JIVO's **E-commerce / Q-commerce** team.

**What they ask about:** channel sell-through, marketplace POs, listing-level
sales, stock at the platform, street price and availability, DRR, ad spend,
scorecards, appointments and RTV.

**What they mean by common words:**
- "sales" → usually platform **sell-out** (consumer bought), not our sell-in to
  the platform. Ask which one, they are very different numbers.
- "stock" → could be at the platform's warehouse or ours; name which
- "qty" → **bottles**, not cartons

**How to answer them:** name the platform and the date range every time. A
number without a channel is meaningless here.

**Traps:** platform listing IDs are not SAP item codes — go through
`product-identity/` (the 333↔1,906 bridge), never match on product name. Oil→Mart
movements are intercompany, not external sales, and will double-count turnover if
you treat them as sales. Classify products by `U_TYPE`/`U_Sub_Group`, not by
name matching.

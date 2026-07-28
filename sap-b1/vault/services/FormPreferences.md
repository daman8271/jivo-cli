---
entity: FormPreferences
domain: administration-setup-3
readable: true
methods: [GET, PATCH, DELETE]
rows_oil: 461588
---
# FormPreferences
Per-user UI form settings (column visibility, width, order per form) saved by the B1 client — hence the huge 461k row count. Live rows in JIVO_OIL_HANADB: 461588.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query FormPreferences --top 5
./sapb1 query FormPreferences --count
./sapb1 query FormPreferences --select "FormID,User,ItemNumber,Column" --top 10
# ALWAYS filter this 461k-row set — e.g. one form's saved layout rows:
./sapb1 query FormPreferences --filter "FormID eq '139'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| FormID | B1 form identifier |
| User | Owning user |
| ItemNumber | Form item/grid identifier |
| Column | Grid column identifier |
| Width | Saved column width |
| VisibleInForm | Shown in normal view |
| VisibleInExpanded | Shown in expanded view |
| EditableInForm | Editable in normal view |
| EditableInExpanded | Editable in expanded view |
| ExpandedIndex | Column order when expanded |
| TabsLayout | Saved tab layout blob |

## Connections
- Domain: [[administration-setup-3]]
- [[Users]] via User — whose client layout each row belongs to

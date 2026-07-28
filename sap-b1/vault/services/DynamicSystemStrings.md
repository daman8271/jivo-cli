---
entity: DynamicSystemStrings
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 8
---
# DynamicSystemStrings
Stores customized UI field labels/strings per form and column so companies can rename screen captions. Live rows in JIVO_OIL_HANADB: 8 (e.g. form 139 "Order No.", form 133 "Document No").

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DynamicSystemStrings --top 5
./sapb1 query DynamicSystemStrings --count
./sapb1 query DynamicSystemStrings --select "FormID,ItemID,ColumnID,ItemString" --top 10
# Relabelled captions on the Sales Order form (FormID is a string):
./sapb1 query DynamicSystemStrings --filter "FormID eq '139'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| FormID | B1 form number (string) |
| ItemID | UI item on the form |
| ColumnID | Column within the item (-1 = whole field) |
| ItemString | The replacement caption text |
| IsBold | Render caption bold? |
| IsItalics | Render caption italic? |

## Connections
- Domain: [[system-other-1]]

---
entity: ShippingTypes
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# ShippingTypes
Shipping/transport method master (courier, road, etc.) referenced by marketing documents; surprisingly empty in this DB. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ShippingTypes --top 5
./sapb1 query ShippingTypes --count
./sapb1 query ShippingTypes --select "Code,Name,Website" --top 10
# Find a transport method by name (if ever populated):
./sapb1 query ShippingTypes --filter "contains(Name,'Road')" --top 10
```
Set is empty here — JIVO documents evidently don't use TransportationCode. Confirm live field names with `./sapb1 fields ShippingTypes` if rows ever appear.

## Key fields
| Field | Meaning |
|---|---|
| Code | Shipping type numeric code (key) |
| Name | Transport method name |
| Website | Carrier website URL |

(No key fields captured in recon — the set is empty; fields above are the standard Service Layer schema.)

## Connections
- Domain: [[administration-setup-3]]
- [[Orders]] via TransportationCode
- [[DeliveryNotes]] via TransportationCode
- [[BusinessPartners]] via ShippingType default on the BP master

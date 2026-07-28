---
entity: CustomerEquipmentCards
domain: business-partners-crm
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# CustomerEquipmentCards
Tracks serialized equipment/service cards per customer (which serial-numbered item a customer owns) for after-sales service management; empty in JIVO_OIL_HANADB so fields are inferred from the SAP B1 schema. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CustomerEquipmentCards --top 5
./sapb1 query CustomerEquipmentCards --count
./sapb1 query CustomerEquipmentCards --select "EquipmentCardNumber,CustomerCode,ItemCode,StatusOfSerialNumber" --top 10
# all equipment cards for one customer:
./sapb1 query CustomerEquipmentCards --filter "CustomerCode eq 'C00001'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| EquipmentCardNumber | Card's internal key |
| InternalSerialNum | SAP-assigned serial number |
| ManufacturerSerialNum | Manufacturer's serial number |
| ItemCode | Serialized item code |
| ItemDescription | Item name |
| CustomerCode | Owning customer code |
| CustomerName | Owning customer name |
| StatusOfSerialNumber | Active / returned / loaned status |
| DeliveryDate | Date delivered to customer |
| InvoiceNum | Originating invoice number |
| ContactEmployeeCode | Customer contact person code |
| TechnicianCode | Assigned service technician |

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartners]] via CustomerCode — the customer who owns the equipment
- [[Items]] via ItemCode — the serialized item on the card
- [[Invoices]] via InvoiceNum — the invoice that delivered the equipment
- [[EmployeesInfo]] via TechnicianCode — the service technician assigned

---
entity: UserLanguages
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 28
---
# UserLanguages
Language master (28 languages) used for user UI language and multi-language descriptions/translations. Live rows in JIVO_OIL_HANADB: 28.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query UserLanguages --top 5
./sapb1 query UserLanguages --count
./sapb1 query UserLanguages --select "Code,LanguageFullName,LanguageShortName" --top 10
# Resolve a language by its short name:
./sapb1 query UserLanguages --filter "LanguageShortName eq 'EN'" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Language numeric code (key) |
| LanguageFullName | Full language name |
| LanguageShortName | Short code (EN, DE…) |
| RelatedSystemLanguage | Mapped B1 system language |

## Connections
- Domain: [[administration-setup-3]]
- [[Users]] via Language (UI language of each user)
- [[BusinessPartners]] via LanguageCode (documents printed in BP's language)

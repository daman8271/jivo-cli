# GST portal logins — verification status

Verified live with gstack browse on 2026-08-21 (17:00–17:25 IST). "OK" = portal accepted username+password, dashboard loaded, `ustatus` returned the GSTIN below. No OTP/2FA was asked on any login.

| # | State | GSTIN | Username | Result | Portal said last login | e-inv |
|---|---|---|---|---|---|---|
| 01 | Haryana | 06AACCJ4223F1Z0 | jivowell729 | OK | 21/08/2026 13:32 | Y |
| 02 | Rajasthan | 08AACCJ4223F1ZW | s08104600868 | OK | 19/08/2026 15:11 | Y |
| 03 | Punjab | 03AACCJ4223F1Z6 | JIVOWELLNESS | **OK** (new password Jivo#1234 from Daman; verified live via the CLI 2026-08-21) | — | Y |
| 04 | Delhi | 07AACCJ4223F1ZY | j07140384127 | OK | 21/08/2026 13:28 | Y |
| 05 | Himachal Pradesh | 02AACCJ4223F1Z8 | akal_barusahib | OK | 20/08/2026 22:07 | Y |
| 06 | Uttar Pradesh | 09AACCJ4223F1ZU | AKAL6081 | OK (2nd try; 1st was my captcha misread) | 19/08/2026 15:16 | Y |
| 07 | Maharashtra (Mumbai) | 27AACCJ4223F2ZV | Jivo_MH27 | OK | 19/08/2026 15:19 | Y |
| 08 | Delhi ISD | 07AACCJ4223F2ZX | Jivowell_ISD | OK | 21/08/2026 13:16 | N (ISD — files GSTR-6, no GSTR-1/3B calendar) |

All 8 regular registrations: GSTR-1 and GSTR-3B **Filed** for Mar-26, Apr-26, May-26, Jun-26, Jul-26 (portal `filingsnapshot`).
Legal name on every login: JIVO WELLNESS PRIVATE LIMITED. All 8 GSTINs pass the check-digit test.

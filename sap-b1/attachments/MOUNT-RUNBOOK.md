# Enable Service-Layer attachments on hanadb (the "door") — needs ROOT once

> **✅ APPLIED & VERIFIED 2026-08-24.** The mount is live on all 3 companies and the API can now
> read AND upload attachments (Oil/Bev `$value`=200, `POST /Attachments2`=201, round-trip OK).
> Full record + open hardening items at the bottom of this file → **[APPLIED 2026-08-24](#-applied-2026-08-24)**.


**Problem:** SAP stores each attachment as a Windows UNC
(`\\10.10.101.52\Attachments_Oil\JIVO_OIL\Attachments`). The Service Layer runs
on Linux (`hanadb`, 138.252.101.222) and cannot resolve that UNC because the
share is **not mounted**. Every attachment read/write via the API returns:

    404  "Fail to get the LINUX mount point for AttachmentsFolderPath"

**Fix:** CIFS-mount the three attachment shares on hanadb. The SL maps the UNC to
the mount by matching the CIFS source in `/proc/mounts`, so no SAP config change
is needed — just the mounts. The SL re-reads mounts per request → **no restart**.

**Blocker today:** this needs root on hanadb. `superadmin` cannot sudo
(SUSE `targetpw` → wants root's password, which we don't hold). Hand this to
whoever has root (IT / the JOY SERVICES migration vendor), or get root's password.

## The commands (run as root on hanadb)

```bash
# credentials file (admin.jivo = full Administrator on .52), root-only
umask 077
cat > /etc/samba/attach.cred <<CRED
username=ADMIN.JIVO
password=Aqr@3609
CRED

# b1service0 (the SL user) is uid=465 gid=464 — mount so it can read+write
for CO in Oil Mart Bev; do
  mkdir -p "/mnt/Attachments_$CO"
  mount -t cifs "//10.10.101.52/Attachments_$CO" "/mnt/Attachments_$CO" \
    -o credentials=/etc/samba/attach.cred,vers=3.0,uid=465,gid=464,file_mode=0770,dir_mode=0770,noserverino
done
mount | grep Attachments      # expect 3 cifs mounts
```

## Verify (no restart needed)

```bash
# from anywhere with the sapb1 CLI: this used to 404, must now return the PDF
sapb1 query Attachments2 --top 1            # find an AbsoluteEntry, e.g. 2
curl -sk -b <session> "https://138.252.101.222:50000/b1s/v1/Attachments2(2)/\$value" -o /tmp/t.pdf
file /tmp/t.pdf                              # expect: PDF document
```

Once this returns a PDF, `POST /Attachments2` (upload) and attaching to a draft
via `AttachmentEntry` also work — fully automatic attach from the CLI.

## Persist across reboot (optional, after verifying)

Add to `/etc/fstab` with `nofail` so a share outage never blocks boot:

```
//10.10.101.52/Attachments_Oil  /mnt/Attachments_Oil  cifs  credentials=/etc/samba/attach.cred,vers=3.0,uid=465,gid=464,file_mode=0770,dir_mode=0770,noserverino,nofail,_netdev  0 0
# (repeat for Mart, Bev)
```

## Until root is available — the root-free path that already works

`sap-b1/attachments/fetch-attachments.sh` pulls any document's attachment PDFs
off `.52` over SMB (no root, no mount). And new PDFs can be **placed** on the
share over SMB; the operator's "Add" in the SAP B1 client then registers them.

---

## ✅ APPLIED 2026-08-24

**Box:** hanadb (SLES 15 SP5, 10.10.101.222 / public 138.252.101.222) — SAP B1 Service Layer :50000 + HANA, LIVE PRODUCTION, 3 company DBs (Oil / Mart / Bev).
**Problem solved:** the 404 "Fail to get the LINUX mount point for AttachmentsFolderPath" on every attachment read/write.

### What was done (as root)
- `superadmin` was granted sudo (`(ALL) NOPASSWD: ALL`) — **to be reverted, see open items.**
- Wrote `/etc/samba/attach.cred` (owner root, mode 0600) with the .52 file-server credential.
- CIFS-mounted all three shares → `/mnt/Attachments_{Oil,Mart,Bev}`
  opts: `credentials=/etc/samba/attach.cred,vers=3.0,uid=465,gid=464,file_mode=0770,dir_mode=0770,noserverino,nofail,_netdev,soft` (uid/gid 465/464 = b1service0, the SL process user).
- Added the three lines to `/etc/fstab` (backup `/etc/fstab.bak.2026-08-24`); `mount -a` parsed clean.

### Verified working
- Oil `GET Attachments2(2)/$value` = 200 (real PDF); Bev = 200.
- Mart mount resolves (its 404s are legacy DB records whose PDFs were never migrated to .52 — data gap, not the mount).
- b1service0 can write all three mounts. Oil `POST /Attachments2` = 201 (AbsoluteEntry 172091); read-back `GET $value` = 200. Test file then deleted; **record 172091 is a known harmless orphan (do not re-investigate its 404).**

### Open items (from the 2026-08-24 Sentinel + Cassius audit)
**MUST-FIX**
1. **Rotate `Aqr@3609`** — cleartext on a public-IP-adjacent box AND already leaked to the public repo (env-vault). Then purge from history/backups.
2. ~~**Shadow-write guard**~~ ✅ **DONE 2026-08-24** — each empty mountpoint set to `root:root 000`, so an absent mount hard-fails instead of silently writing PDFs to hanadb's local disk. Verified: `b1service0` cannot write when unmounted, writes normally when mounted. *(Still SHOULD add a `mountpoint -q` liveness alert.)*
3. **Least-privilege account** — replace full-admin `ADMIN.JIVO` with a scoped `svc_sap_attach` (NTFS Modify on the 3 folders only, not in Administrators); split per-company if practical.
4. **Revert `superadmin NOPASSWD:ALL`** — the mounts run from fstab as root at boot; narrow to `NOPASSWD: /usr/bin/mount -a, /usr/bin/umount /mnt/Attachments_*` if passwordless remount is wanted.

**SHOULD-FIX**
- Real reboot test + SL→mount ordering via systemd `.mount` + `RequiresMountsFor=/mnt/Attachments_*` (`mount -a` on a live shell is NOT proof of reboot survival).
- Switch write mounts `soft`→`hard` (keep `nofail,_netdev`) — `soft` can truncate a PDF mid-write on a blip.
- SMB3 `seal` + require signing on .52 (docs + admin auth currently cross the LAN in cleartext, NTLM-relayable).
- Pin/document b1service0 uid/gid 465/464 — an SL upgrade that re-creates the user with a new uid silently denies all access.
- Exclude `/etc/samba/` + cred files from every backup/rsync/repo scope (the exact way env-vault leaked once already).

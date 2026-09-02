# Message to send to the SAP migration vendor / IT

Hi — need one small thing on the SAP **Linux** server **hanadb (138.252.101.222)**.

The SAP B1 Service Layer there can't open or save attachments — it returns
*"Fail to get the LINUX mount point for AttachmentsFolderPath"* — because the
Windows attachment shares (`\\10.10.101.52\Attachments_Oil / _Mart / _Bev`) are
not CIFS-mounted on the Linux box.

To fix it I need **root-level access on hanadb**. One clarification, because I
think there's a mix-up: the password shared for **`superadmin` is the SSH/login
password, NOT root's**. This box has `sudo` set to `targetpw`, so `superadmin`
is prompted for the **root** password when running admin commands — and we don't
have that. `superadmin` already has full sudo rights (`ALL`); it just can't
authenticate as root.

**Please do any ONE of these (whichever is easiest for you):**
1. **Run the 3 mount commands yourselves** (2 minutes — below), or
2. **Share the root password** for hanadb, or
3. **Give `superadmin` passwordless sudo** (or remove `targetpw`).

**What I do NOT need:** the Windows / HANA / SAP application passwords — we
already have those. Only root (or one of the three options) on the **hanadb
Linux box**. Thanks!

---

## The 3 mount commands (option 1) — run as root on hanadb

```bash
umask 077
cat > /etc/samba/attach.cred <<CRED
username=ADMIN.JIVO
password=<the ADMIN.JIVO password for 10.10.101.52 — your team set this>
CRED

for CO in Oil Mart Bev; do
  mkdir -p "/mnt/Attachments_$CO"
  mount -t cifs "//10.10.101.52/Attachments_$CO" "/mnt/Attachments_$CO" \
    -o credentials=/etc/samba/attach.cred,vers=3.0,uid=465,gid=464,file_mode=0770,dir_mode=0770,noserverino
done
mount | grep Attachments   # expect 3 cifs mounts
```

No SAP restart needed — the Service Layer picks up the mounts on the next request.
(uid=465/gid=464 = the `b1service0` service-layer user, so it can read+write.)

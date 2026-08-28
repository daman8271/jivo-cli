# ARY — read this first

You are in JIVO's **ARY** toolkit. ARY (Akal Rozgar Yojana, a unit of Jivo Wellness Pvt
Ltd) is the **only shop for ~5,000 people** on the closed Baru Sahib campus in Rajgarh,
Himachal Pradesh.

**If someone here is asking about expanding the range, what to stock, or what people
need — read `ARY-TEAM-BRIEF.md` before you query anything.** This database has four
documented traps that produce confident wrong answers, and they have already caught five
findings.

- **`ARY-TEAM-BRIEF.md`** — the job, the traps, the arithmetic, how to run it
- **`assort/vault/00-ARY-Atlas.md`** — everything measured, 28 linked notes
- **`assort/vault/01-foundations/Owner-Brief.md`** — what the owner actually wants. Outranks
  any inference elsewhere
- **`RESUMPTION.md`** — the paused research task. If the user says *"resumption"*, start here

## The one rule that matters most

**In this database the burden of proof sits on "missing", never on "covered."** ARY
probably has it under a different name. Never answer "do we carry X?" from the category
tree — use `ary assort probe <single words>`, and read what actually matched before
quoting any number.

## Read-only, always

The `ary` CLI cannot write: every statement passes a SELECT-only guard inside a
transaction that is always rolled back. **Never run `sapb1` from this folder.** Zero write
calls were made building any of this.

```bash
set -a; . ../connections/ary.env; set +a
./ary doctor
```

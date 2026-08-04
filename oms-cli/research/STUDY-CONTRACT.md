# Phase-3 study contract — read this before writing anything

You are studying one domain of JIVO's OMS API so a **read-only** CLI can be
generated from it. Your output is consumed by a code generator, so it has to be
precise about names, params and types. Everything you need has already been
measured; you are turning evidence into a specification, not re-discovering it.

## Read first

1. `oms-cli/research/API-FACTS-2026-08.md` — what was proven about this API.
   The `branch` section applies to more than `hana`; read it even if your
   domain is elsewhere.
2. Your brief: `oms-cli/research/briefs/brief-<domain>.md`. It carries, per
   endpoint, the shipped command name, the live probe result, and the server's
   own error text.

## Hard rules — these are not style preferences

1. **RULE 0: OMS is read-only. No exceptions, ever, even if asked.** You publish
   GET endpoints. A POST/PUT/PATCH/DELETE is an *exclusion*, and it goes in a
   separate `excluded[]` list — never inside `endpoints[]` with a warning
   attached. Safety that depends on a downstream tool reading a magic string in
   a name field is not safety.

2. **Never send a parameter value you have not observed.** Observed means: in a
   live payload in the evidence, in the server's own error text, or in the app's
   own source. A `GET` on the factory API turned out to be a Django
   `get_or_create` and probing it with invented values created six production
   rows that a human still has to delete. If you cannot source a value, the
   parameter is documented and left unprobed. **Unproven resolves to excluded.**

3. **Do not rename anything.** If the brief shows a `SHIPPED COMMAND`, that is
   the command name. Full stop. MCP `endpoint_id`s are a public contract and
   operators have scripts. Only genuinely new endpoints get new names, and those
   should read like the shipped ones (`hana all-customers`, not `hana getAllCustomers`).

4. **A 403 or a 401 is not proof of death.** Publish it, and mark the response
   shape `UNVERIFIED` with the server's wording as the reason. The credential
   used lacks tracker grants; the endpoints exist.

5. **A 0-row 200 is a data fact, not a scoping fact.** "This user has no
   assigned parties" is a note for the operator. It is not a constraint on the
   command, and it must not become one.

6. **Response type comes from what actually came back**, not from a default. The
   brief prints `top-level JSON` for every 200. A previous OMS spec declared
   `type: object` for all 73 endpoints; the probe shows many are arrays.

## Live calls you may make

You have a token at `/tmp/oms-rescrape/token.txt`. You may issue **GET only**,
and only:

- against a path your brief already shows returning 200 or 400, and
- with parameter values sourced per rule 2, and
- never against a path flagged write-intent or listed under writes in API-FACTS.

Use this shape, and keep the output small:

```bash
T=$(cat /tmp/oms-rescrape/token.txt)
curl -s -H "Authorization: Bearer $T" "https://oms.jivo.in/api/<path>/?<params>" | head -c 600
```

The highest-value live call is a **parameterised** one — fetch a real id from a
list endpoint in your own domain, then call the detail endpoint with it. That is
the only way to learn a detail endpoint's real response shape. Do it where you
can.

If a call creates something, or you suspect it did, **stop and report it**. Do
not try to undo it.

## What to write

Write exactly one file: `oms-cli/research/studies/study-<domain>.md`.

For every endpoint in your brief, in this order:

```markdown
### `<normalised path>`

- **command**: `<resource> <name>`   (shipped name if one exists, else your new one)
- **verdict**: publish | exclude
- **exclusion reason** (only if exclude): write verb | auth mutator | proven dead | unsafe
- **description**: one line, operator language. What business question does this
  answer? Not "returns the list of X" — say what X is at JIVO.
- **params**: for each — name, type, required?, positional?, enum values if the
  server or a payload named them, and where each value came from.
- **response**: `object` | `array`, from the observed probe. Note the key fields
  an operator cares about. Mark `UNVERIFIED` if you only ever saw a 403.
- **evidence**: the status code(s) you are relying on, and any live call you ran.
- **traps**: anything that makes a naive command wrong. Empty if genuinely none.
```

Then finish with:

```markdown
## Domain summary
- what this domain is, in two or three sentences an operator would recognise
- the traps that apply across the whole domain
- anything that looks like a backend defect, with the reproduction
- any durable JIVO business truth worth recording as a correction
```

## Calibration

Be skeptical of your own conclusions. State confidence where it is not certain,
and say plainly when you did not check something rather than implying you did.
A study that says "I could not verify this response shape, only a 403" is worth
more than one that quietly guesses `object`.

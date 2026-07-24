---
title: Chats — conversation journal
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: readme
tags: [chats, journal, obsidian]
---

# Chats

A running journal of Daman ↔ Claude conversations while working in `~/jivo-cli`.

**The convention:** whenever Daman `cd`s into this repo and talks — decisions, asks, "this and that" — Claude notes the substance here as Obsidian-style linked notes. Not a transcript; the *gist*: what was asked, what was decided, what was built, and what's next.

## Layout
- `Chats-MOC.md` — the map of content (index of every session, newest first).
- `YYYY-MM-DD.md` — one note per day/session. Wikilink to the things discussed (`[[blinkit-partner]]`, `[[sap-b1]]`, `[[postsql]]`, goal numbers, etc.).

## Format of a session note
Frontmatter (`title, created, updated, project, type: chat, tags`), then:
- **Context** — where we were / what triggered it
- **What we did** — bullet decisions & outcomes, with `[[links]]`
- **Decisions** — anything binding going forward
- **Next** — open threads

Start at [[Chats-MOC]].

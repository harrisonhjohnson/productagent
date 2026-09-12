---
name: clean-desktop
description: Tidy the user's ~/Desktop by sorting loose files into existing project folders and a small set of standing topical folders. Use whenever the user says "clean up my desktop", "tidy my desktop", "organize my desktop", "my desktop is a mess", or asks to file away loose screenshots/downloads on the Desktop. Also use for periodic desktop sweeps.
---

# Clean Desktop

Sort the loose files on `~/Desktop` into folders. The goal is a Desktop with only folders (plus anything deliberately kept loose), with nothing deleted without explicit permission.

## Principles

- **Move, never delete.** The only deletions allowed without asking are empty folders (e.g. `untitled folder`). Everything else gets filed, not trashed. If something looks like junk, file it and mention it in the summary.
- **Existing folders are the map.** Look inside the folders already on the Desktop before creating new ones — they show where the user already files things. Route loose files into an existing folder whenever the topic matches (e.g. files for a client → that client's folder, a project's handoff doc → that project's folder).
- **Flag sensitive files, don't touch them.** Anything that looks like credentials, 2FA backup codes, API keys, or private financial/legal material stays where it is. Call it out in the summary and suggest a safer home (password manager / Keychain), but leave the move to the user.
- **Identify before filing.** For extension-less or UUID-named files, run `file` and peek at the head to find out what they are. Give them a sensible name + extension when moving (e.g. a UUID-named React file → `dungeon-run.jsx`).

## Workflow

1. `ls -la ~/Desktop` to see the full picture. Note existing folders, loose file clusters, and anything sensitive-looking.
2. List the contents of each existing Desktop folder to learn the filing pattern.
3. Identify mystery files (`file`, `head -c 400`).
4. Sort loose files:
   - **Project-matched files** → the matching existing folder.
   - **Screenshots** (`Screenshot 2026-*.png` etc.) → `Screenshots/`.
   - **Handoff docs, session learnings, proposals, scratchpads** → `Handoffs & Notes/`.
   - **Photos, avatars, logos, SVGs, generated images** → `Images/`.
   - **Client invoices / deliverables** → a folder named for the client (e.g. `Acme/`).
   - **Everything else** → `Misc/`.
   Create these standing folders only when there are files for them; reuse them if they already exist from a previous sweep.
5. Remove empty folders (`rmdir` only — it fails safely if not empty).
6. Verify with a final `ls -la ~/Desktop`.

## Summary format

End with:
- A bullet per folder saying what went into it (counts + notable items).
- Any renames of mystery files and what they turned out to be.
- A callout for sensitive files left in place, with a recommendation.

## Notes

- `.bak` / backup files get filed with their topic, not deleted.
- Don't reorganize the *insides* of existing folders — this skill only clears the loose top level.
- If a file's home is genuinely ambiguous and consequential, `Misc/` beats guessing wrong or asking.

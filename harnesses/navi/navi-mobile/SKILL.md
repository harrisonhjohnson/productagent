---
name: navi-mobile
description: Switch THIS Claude Code tab into (or out of) NAVI mobile mode — stream this tab's responses to Telegram and drive it from your phone. Use when the user says "go mobile", "switch this tab to mobile", "navi mobile", or "hand this tab to my phone". Run once per tab. Default is desktop.
---

# navi-mobile

Put the **current** Claude Code tab into NAVI mobile mode (or take it back out).
While a tab is on mobile, its responses stream to Telegram and the user's
Telegram replies are fed back as that tab's next turn — so the tab is driven
from the phone. Each tab is keyed by `CLAUDE_CODE_SESSION_ID`, so multiple tabs
can be mobile at once in one chat.

## What to do

Default action is to turn mobile **on** for this tab. If the user said "off",
"stop", "desktop", or "back to keyboard", turn it off instead.

Turn ON:

```bash
python3 ~/tools/navi/navi_tab.py on
```

Turn OFF:

```bash
python3 ~/tools/navi/navi_tab.py off
```

Then relay the command's output to the user in one short line (it includes the
tab id, e.g. `0afa1c`). Do **not** do anything else after — end the turn so the
Stop hook can take over and begin streaming this tab to Telegram.

## Notes for the user (mention briefly when turning on)

- Responses from this tab now stream to Telegram; **reply to a message** there to
  continue this tab. With multiple mobile tabs, reply to the specific tab's message.
- To hand this tab back to the keyboard: send **`/desktop`** from Telegram
  (or `/desktop <id>`), or press **Ctrl-C** in the tab.
- `/tabs` in Telegram lists which tabs are currently on mobile.

If the command prints "No CLAUDE_CODE_SESSION_ID", it wasn't run inside a Claude
Code tab — re-run it from within the tab you want to make mobile.

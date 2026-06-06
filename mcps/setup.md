# MCP setup

MCPs (Model Context Protocols) are how productagent connects to your tools. Each one you add makes the agents more useful. None are required — start with what you already use.

## Installing an MCP

MCPs are configured in Claude Code's settings. To add one:

```bash
claude mcp add <name> <command>
```

Or edit `~/.claude/settings.json` directly under the `mcpServers` key. See the [Claude Code MCP docs](https://docs.anthropic.com/claude-code/mcp) for full reference.

---

## Recommended integrations

### Asana — project management
Tasks, due dates, assignees, blockers. Powers the `what` and `when` agents most directly.

```bash
claude mcp add asana npx -y @modelcontextprotocol/server-asana
```

Requires: `ASANA_ACCESS_TOKEN` in your environment.

---

### Slack — communications
Channel history, threads, people. Powers the `who` agent when ownership isn't clear from `context.md` alone.

```bash
claude mcp add slack npx -y @modelcontextprotocol/server-slack
```

Requires: `SLACK_BOT_TOKEN` and `SLACK_TEAM_ID` in your environment.

---

### Google Drive — documents
PRDs, specs, briefs. Powers the `where` agent for document lookup.

```bash
claude mcp add gdrive npx -y @modelcontextprotocol/server-gdrive
```

Requires: Google OAuth credentials. See the [server-gdrive README](https://github.com/modelcontextprotocol/servers/tree/main/src/gdrive) for setup.

---

### GitHub — code and issues
Repositories, issues, PRs. Powers `what` and `where` for engineering-adjacent questions.

```bash
claude mcp add github npx -y @modelcontextprotocol/server-github
```

Requires: `GITHUB_PERSONAL_ACCESS_TOKEN` in your environment.

---

### Databricks — data
Tables, metrics, datasets. Powers the `where` agent for data questions. Add this if your team runs analytics on Databricks.

```bash
claude mcp add databricks npx -y @databricks/mcp-server
```

Requires: `DATABRICKS_HOST` and `DATABRICKS_TOKEN` in your environment.

---

## Syncing context

Once MCPs are connected, you can run a manual sync at any time:

> "Sync my context — check context.md against Asana and Slack and flag anything stale or missing."

Run this before planning meetings, weekly reviews, or first thing in the morning. See `CLAUDE.md` for more on sync cadence.

## Adding other tools

Any MCP server works here. The agents are written to use whatever is available and skip what isn't. Find community-built MCP servers at [github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers).

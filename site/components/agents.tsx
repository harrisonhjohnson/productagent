const TOUCHPOINTS = [
  { where: 'How the agent is started', claude: 'claude -p, one bounded call', codex: 'codex exec, one bounded call' },
  { where: 'The fence', claude: '.claude/settings.json allow and deny rules', codex: 'workspace-write sandbox, network off. Cannot push, cannot fetch.' },
  { where: 'Where the cost comes from', claude: 'the JSON envelope the call returns', codex: 'token counts from the event stream, priced by two charter dials' },
  { where: 'Where the transcript lives', claude: '~/.claude/projects, scored by the health desk', codex: '~/.codex/sessions, not scored yet' },
];


export function Agents() {
  return (
    <section className="where" aria-labelledby="agents-heading">
      <p className="section-label" id="agents-heading">WHICH AGENT</p>
      <p className="where-lede">
        Claude Code by default, Codex with one line in the charter. The runner touches the agent in exactly four
        places, each behind a small adapter, so the four knobs, the four lines and the morning judge are the same
        either way. The one real difference is the fence: Codex&apos;s is a sandbox with the network off, which is a
        harder no-push and also means research loops that read the web stay on Claude Code.
      </p>
      <div className="tbl">
        <table className="touch">
          <thead><tr><th>The runner needs</th><th>Claude Code</th><th>Codex</th></tr></thead>
          <tbody>
            {TOUCHPOINTS.map((t) => (
              <tr key={t.where}><td>{t.where}</td><td>{t.claude}</td><td>{t.codex}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

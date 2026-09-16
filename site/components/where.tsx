const LAYERS = [
  {
    name: 'The runtime',
    who: 'terminal multiplexers, agent runtimes',
    does: 'Keeps agent terminals alive when you close the lid, and shows you which one is stuck.',
    loops: 'Loops runs inside any of them. It needs none of them.',
  },
  {
    name: 'The loop',
    who: 'this folder',
    does: 'Decides what runs tonight, how much it may spend, what it may touch, and what you read in the morning.',
    loops: 'A contract, not a runtime. Four knobs in, four lines out, a fence in between.',
    current: true,
  },
  {
    name: 'The cloud',
    who: 'hosted agent sandboxes',
    does: 'Rents you a machine per agent so nothing depends on your laptop.',
    loops: 'Loops stays on your Mac on purpose. Your plan, your keys, nothing phones home.',
  },
];

const TOUCHPOINTS = [
  { where: 'How the agent is started', claude: 'claude -p, one bounded call', codex: 'codex exec, one bounded call' },
  { where: 'The fence', claude: '.claude/settings.json allow and deny rules', codex: 'workspace-write sandbox, network off. Cannot push, cannot fetch.' },
  { where: 'Where the cost comes from', claude: 'the JSON envelope the call returns', codex: 'token counts from the event stream, priced by two charter dials' },
  { where: 'Where the transcript lives', claude: '~/.claude/projects, scored by the health desk', codex: '~/.codex/sessions, not scored yet' },
];

export function Where() {
  return (
    <section className="where" aria-labelledby="where-heading">
      <p className="section-label" id="where-heading">WHERE THIS SITS</p>
      <p className="where-lede">
        Three layers are being built around coding agents right now. Loops is the middle one, and it is the only
        one that does not need a company behind it.
      </p>
      <ol className="layers" aria-label="The three layers">
        {LAYERS.map((l) => (
          <li key={l.name} className={l.current ? 'is-current' : undefined}>
            <h3>{l.name}</h3>
            <p className="layer-who">{l.who}</p>
            <p>{l.does}</p>
            <p className="layer-loops">{l.loops}</p>
          </li>
        ))}
      </ol>

      <h3 className="where-sub">Which agent</h3>
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

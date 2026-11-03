// Figure specs for /33-nights and /asks. Coordinates are in a 440 x 236 viewBox unless the spec sets W and H.
// Copy comes from essays/33-nights.md and essays/asks.md; numbers must match those files.

export type St = 'b' | 'f';
type Face = { l?: string; s?: string };
export type FigNode = Face & {
  id: string; x: number; y: number; w?: number; h?: number;
  only?: St; bad?: St | true; mine?: number; fmine?: number; b?: Face; f?: Face;
};
export type FigEdge = {
  a: string; b: string; l?: string; only?: St; bad?: number; dash?: number; cut?: number;
  t?: number; ay?: number; by?: number;
};
export type Badge = { n: number; k: string; node?: string; a?: string; b?: string; t?: number; dx?: number; dy?: number };
export type Fig = {
  n: number; id?: string; t: string; claim?: string; nodes: FigNode[]; edges: FigEdge[];
  nb?: string; nf?: string; table?: boolean; units?: number; W?: number; H?: number; badges?: Badge[];
};

export const L = 60, C = 220, R = 380, T = 36, M = 118, B = 200;

// Where each part of evidence/machine.json sits in the Figure 1 grid.
const X = [90, 260, 430, 600, 770], Y = [44, 150, 256, 362, 462];
export const MODEL_LAYOUT: Record<string, [number, number]> = {
  power: [X[0], Y[0]], login: [X[1], Y[0]], settings: [X[2], Y[0]], sandbox: [X[3], Y[0]],
  mac: [X[0], Y[1]], runner: [X[1], Y[1]], session: [X[2], Y[1]], background: [X[3], Y[1]],
  runlog: [X[0], Y[2]], graders: [X[1], Y[2]], summary: [X[2], Y[2]], autopark: [X[3], Y[2]], branch: [X[4], Y[2]],
  report: [X[2], Y[3]], me: [X[2], Y[4]], site: [X[4], Y[4]],
};
export const MODEL_LABEL_T: Record<string, number> = { 'session>graders': 0.45, 'runner>branch': 0.62, 'runlog>report': 0.4, 'graders>report': 0.45, 'branch>me': 0.55 };
export const MODEL_BADGE_OFFSET: Record<number, { t?: number; dx?: number; dy?: number }> = {
  3: { t: 0.5, dy: -16 }, 4: { t: 0.75, dy: -14 }, 10: { t: 0.42, dx: 22, dy: 14 },
};

export const BREAK_FIGS: Fig[] = [
  { n: 1, t: 'Staying awake', claim: 'The Mac slept on battery, so the run sat there and made nothing.',
    nodes: [
      { id: 'bat', x: L, y: T, l: 'Battery', only: 'b', bad: 'b' },
      { id: 'ac', x: L, y: T, l: 'Wall power', s: 'AC only', only: 'f' },
      { id: 'mac', x: L, y: M, l: 'Mac', b: { s: 'asleep mid-run' }, f: { s: 'keep-awake window' }, bad: 'b' },
      { id: 'run', x: C, y: M, l: 'Runner', mine: 1 },
      { id: 'ses', x: R, y: M, l: 'Session', b: { s: '5,974 s, no output' }, bad: 'b' },
      { id: 'alarm', x: C, y: B, l: 'Missed-run alarm', only: 'f', mine: 1 },
      { id: 'rep', x: R, y: B, l: 'Morning report' },
    ],
    edges: [
      { a: 'bat', b: 'mac', l: 'powers', only: 'b' }, { a: 'ac', b: 'mac', l: 'powers', only: 'f' },
      { a: 'mac', b: 'run', l: 'hosts' }, { a: 'run', b: 'ses', l: 'starts' },
      { a: 'ses', b: 'rep', l: 'nothing', only: 'b', bad: 1, dash: 1 }, { a: 'ses', b: 'rep', l: 'writes', only: 'f' },
      { a: 'run', b: 'alarm', l: 'misses raise', only: 'f' },
    ],
    nb: 'August 24, 27 and 28. On two of those nights no alarm fired; I found it in the morning report.',
    nf: 'Shipped: runs start only on AC power, inside a keep-awake window, and a missed run raises an alarm.' },

  { n: 2, t: 'Staying logged in', claim: 'The login expired, so the check worked and the night was still lost.',
    nodes: [
      { id: 'run', x: L, y: M, l: 'Runner', s: 'login check', mine: 1 },
      { id: 'cred', x: C, y: T, l: 'OAuth login', b: { s: 'expired, no refresh' }, f: { l: 'Unattended login', s: 'expiry visible ahead' }, bad: 'b' },
      { id: 'ses', x: R, y: M, l: 'Session', b: { s: 'skipped, $0' }, bad: 'b' },
      { id: 'log', x: C, y: B, l: 'Run log' },
    ],
    edges: [
      { a: 'run', b: 'cred', l: '00:06, 00:16', only: 'b', bad: 1 }, { a: 'cred', b: 'run', l: 'warns days ahead', only: 'f' },
      { a: 'run', b: 'ses', l: 'skips', only: 'b', bad: 1, dash: 1 }, { a: 'run', b: 'ses', l: 'starts', only: 'f' },
      { a: 'run', b: 'log', l: 'records' },
    ],
    nb: 'October 15: "OAuth session expired and could not be refreshed."',
    nf: 'Still open. Unattended runs need credentials built for unattended use (ask 4 below).' },

  { n: 3, t: 'Starting in the right place', claim: 'Launched from the wrong folder, the session had no fence at all.',
    nodes: [
      { id: 'run', x: L, y: T, l: 'Runner', mine: 1, f: { s: 'checks the launch' } },
      { id: 'wrong', x: C, y: T, l: 'Wrong folder', s: 'no settings file', only: 'b', bad: 'b' },
      { id: 'work', x: C, y: T, l: 'Work folder', only: 'f' },
      { id: 'set', x: R, y: T, l: 'Settings file', s: 'allow rules', only: 'f', mine: 1 },
      { id: 'ses', x: C, y: M, l: 'Session' },
      { id: 'wr', x: C, y: B, l: 'Writes', b: { s: 'every one denied' }, f: { s: 'allowed by rule' }, bad: 'b' },
      { id: 'rep', x: R, y: B, l: 'Report', b: { s: 'blocked, $3.95' } },
    ],
    edges: [
      { a: 'run', b: 'wrong', l: 'opens', only: 'b', bad: 1 }, { a: 'run', b: 'work', l: 'opens', only: 'f' },
      { a: 'work', b: 'set', l: 'loads', only: 'f' },
      { a: 'wrong', b: 'ses', l: 'starts', only: 'b' }, { a: 'work', b: 'ses', l: 'starts', only: 'f' },
      { a: 'ses', b: 'wr', l: 'tries' }, { a: 'ses', b: 'rep', l: 'stops, reports', only: 'b' },
    ],
    nb: 'August 18. The agent noticed every write was denied, stopped, and reported itself blocked.',
    nf: 'The fence is part of the launch, so the launch has to be checked.' },

  { n: 4, t: 'Keeping its hands off my work', claim: 'My own git add -A put my unsaved work into the night’s commits.',
    nodes: [
      { id: 'mine', x: L + 4, y: T, w: 116, l: 'My unsaved work', b: { s: '12 files, 397 lines' }, f: { s: 'left alone' }, bad: 'b' },
      { id: 'night', x: L, y: B, l: 'Night’s files' },
      { id: 'run', x: C, y: M, l: 'Runner', mine: 1, b: { s: 'git add -A' }, f: { s: 'allowlist only' } },
      { id: 'br', x: R, y: M, l: 'Night branch' },
    ],
    edges: [
      { a: 'mine', b: 'run', l: 'swept in', only: 'b', bad: 1 },
      { a: 'night', b: 'run', l: 'stages' }, { a: 'run', b: 'br', l: 'commits' },
    ],
    nb: 'For 14 days. That was my bug, not the agent’s.',
    nf: 'Shipped: the runner commits only files on an allowlist. It must never claim work it didn’t do.' },

  { n: 5, t: 'Knowing when it’s finished', claim: 'The session quit while its own background work was still running.',
    nodes: [
      { id: 'ses', x: L, y: M, l: 'Session' },
      { id: 'bg', x: C, y: T, w: 112, l: 'Background task', b: { s: 'still running' }, bad: 'b' },
      { id: 'last', x: C, y: B, w: 120, l: 'Last message', s: '“waiting on the task…”' },
      { id: 'rep', x: R, y: T, l: 'Report', b: { s: 'never written' }, bad: 'b' },
      { id: 'gr', x: R, y: B, l: 'Runner’s grade', mine: 1, b: { s: 'ok' }, f: { s: 'incomplete' }, bad: 'b' },
    ],
    edges: [
      { a: 'ses', b: 'bg', l: 'starts' }, { a: 'ses', b: 'last', l: 'quits on' },
      { a: 'bg', b: 'rep', l: '', only: 'b', bad: 1, dash: 1, cut: 1 }, { a: 'bg', b: 'rep', l: '', only: 'f', dash: 1 },
      { a: 'last', b: 'gr', l: 'graded', only: 'b' }, { a: 'last', b: 'gr', l: 'regex', only: 'f' },
    ],
    nb: 'Four times. My runner graded the first one ok.',
    nf: 'Shipped: a regex on the last message marks these runs incomplete. It has fired twice since.' },

  { n: 6, t: 'Reporting from records, not memory', claim: 'The agent’s summary got time, refusals and cost wrong. The log had them right.',
    nodes: [
      { id: 'sum', x: L, y: T, l: 'Agent’s summary', w: 116, bad: 'b' },
      { id: 'log', x: L, y: 96, l: 'Runner’s log', mine: 1 },
      { id: 'rep', x: R, y: T, l: 'Morning report' },
    ],
    edges: [
      { a: 'sum', b: 'rep', l: 'fills time, cost, refusals', only: 'b', bad: 1 }, { a: 'log', b: 'rep', l: 'fills time, cost, refusals', only: 'f' },
      { a: 'sum', b: 'rep', l: 'writes the prose', only: 'f' },
    ],
    table: true,
    nb: 'One run said ~33 minutes and took 6. Sept 22: "none" with 34 refused. Oct 16: "$0" when the JSON said $0.602.',
    nf: 'Time, cost and refusals come from the runner’s logs, never from the agent’s summary.' },

  { n: 7, t: 'Grading evidence, not claims', claim: '63 identical rechecks were each marked as progress, so the stop rule never fired.',
    nodes: [
      { id: 'loop', x: L, y: T, l: 'Hourly Loop' },
      { id: 'src', x: L, y: 150, b: { l: 'Agent’s claim', s: '“progress”' }, f: { l: 'The diff', s: '0 files changed' }, bad: 'b' },
      { id: 'park', x: R, y: 150, l: 'Auto-park rule', mine: 1, b: { s: 'never fired' }, f: { s: 'parks the Loop' }, bad: 'b' },
    ],
    edges: [{ a: 'src', b: 'park', l: 'counted by' }],
    units: 63,
    nb: 'I caught it by reading the board.',
    nf: 'Progress should be counted by the changed file or the diff.' },

  { n: 8, t: 'Grading the graders', claim: 'Three graders raised alarms on a clean night. None was real.',
    nodes: [
      { id: 'night', x: L, y: M, l: 'Clean night' },
      { id: 'g1', x: C, y: T, l: 'Health checks', mine: 1, b: { s: '5 critical alarms' }, bad: 'b' },
      { id: 'g2', x: C, y: M, l: 'LLM judge', mine: 1, b: { s: 'ran 3 times, gave a C' }, bad: 'b' },
      { id: 'g3', x: C, y: B, l: 'Git scorer', mine: 1, b: { s: 'reads seen as writes' }, bad: 'b' },
      { id: 'me', x: R, y: M, l: 'Me', b: { s: '0 real emergencies' }, f: { s: 'reviews the graders' } },
    ],
    edges: [
      { a: 'night', b: 'g1' }, { a: 'night', b: 'g2', l: 'scored by' }, { a: 'night', b: 'g3' },
      { a: 'g1', b: 'me', only: 'b', bad: 1 }, { a: 'g2', b: 'me', l: 'alarms', only: 'b', bad: 1 }, { a: 'g3', b: 'me', only: 'b', bad: 1 },
      { a: 'me', b: 'g1', only: 'f' }, { a: 'me', b: 'g2', l: 'checks', only: 'f' }, { a: 'me', b: 'g3', only: 'f' },
    ],
    nb: 'September 22. The scorer flagged git branch --list, git merge-base, and a command quoted in a note to me.',
    nf: 'A grader needs the same review as the thing it grades.' },

  { n: 9, t: 'A fence that holds against a script', claim: 'Rules read the command text, so a script walked around them.',
    nodes: [
      { id: 'ses', x: L, y: M, l: 'Session' },
      { id: 'rules', x: C, y: T, l: 'Deny rules', s: 'match command text', mine: 1 },
      { id: 'sb', x: C, y: B, l: 'OS sandbox', s: 'checks files + hosts', only: 'f' },
      { id: 'tg', x: R, y: M, l: 'Off-limits', s: '.git, ops, creds, web', bad: 'b' },
    ],
    edges: [
      { a: 'ses', b: 'rules', l: 'git push' },
      { a: 'ses', b: 'tg', l: 'python3 -c, not matched', only: 'b', bad: 1 },
      { a: 'ses', b: 'sb', l: 'every call', only: 'f' }, { a: 'sb', b: 'tg', l: 'not permitted', only: 'f', cut: 1 },
    ],
    nb: 'Oct 2: git -C <path> push got past my deny rules. Oct 20: one line of python3 -c, five of five probes got through.',
    nf: 'Shipped: Claude Code’s OS sandbox under every run. The same five probes now fail: Operation not permitted.' },

  { n: 10, t: 'Not stranding work behind me', claim: 'Only I can merge, so a finished update waited eight days.',
    nodes: [
      { id: 'ag', x: L, y: T, l: 'Night run' },
      { id: 'br', x: C, y: T, l: 'Branch', s: 'fan-site update' },
      { id: 'main', x: R, y: T, l: 'Live site' },
      { id: 'me', x: C, y: B, l: 'Me', b: { s: '8 days, not merged' }, f: { s: 'merges in the morning' }, bad: 'b' },
      { id: 'nx', x: L, y: B, l: 'Next week’s run', w: 112 },
    ],
    edges: [
      { a: 'ag', b: 'br', l: 'writes' }, { a: 'br', b: 'main', l: 'merge', only: 'b', bad: 1, dash: 1 }, { a: 'br', b: 'main', l: 'merge', only: 'f' },
      { a: 'br', b: 'me', l: 'waits for' }, { a: 'nx', b: 'br', l: 'would erase', only: 'b', bad: 1, t: .62 },
      { a: 'nx', b: 'me', l: 'stops, asks', only: 'b' },
    ],
    nb: 'October 16: the agent saw the next update would erase this one, stopped before touching a file, and asked me.',
    nf: 'No fix in the machine. Every rule that routes work through me makes me the bottleneck, so the morning is the product.' },
];

export const ASK_FIGS: Fig[] = [
  { n: 1, id: 'refusals', t: 'Refusals in the record', claim: 'The headless JSON listed one of four refusals. The agent said none.',
    nodes: [
      { id: 'ses', x: L, y: M - 22, h: 86, l: 'Session', s: '4 refused calls' },
      { id: 'js', x: R, y: M - 22, h: 86, l: 'Headless JSON', b: { s: 'lists 1 of 4' }, f: { s: 'all 4 + rule + input' }, bad: 'b' },
      { id: 'sum', x: R - 6, y: B, w: 124, l: 'Agent’s summary', b: { s: '“none” on a night of 34' }, only: 'b', bad: 'b' },
    ],
    edges: [
      { a: 'ses', b: 'js', l: 'git push', ay: -30, by: -30 },
      { a: 'ses', b: 'js', l: 'Edit', ay: -10, by: -10, only: 'b', bad: 1, dash: 1, cut: 1, t: .35 },
      { a: 'ses', b: 'js', l: 'Edit', ay: 10, by: 10, only: 'b', bad: 1, dash: 1, cut: 1, t: .35 },
      { a: 'ses', b: 'js', l: 'Edit', ay: 30, by: 30, only: 'b', bad: 1, dash: 1, cut: 1, t: .35 },
      { a: 'ses', b: 'js', l: 'Edit', ay: -10, by: -10, only: 'f' },
      { a: 'ses', b: 'js', l: 'Edit', ay: 10, by: 10, only: 'f' },
      { a: 'ses', b: 'js', l: 'Edit', ay: 30, by: 30, only: 'f' },
      { a: 'ses', b: 'sum', l: 'writes', only: 'b', ay: 43 },
    ],
    nb: 'My first probe: one git push denial listed, three Edit denials missing.',
    nf: 'Ship: the output lists every refused call, with the rule that fired and the tool input.' },

  { n: 2, id: 'sandbox', t: 'Sandbox on by default for headless runs', claim: 'Prefix rules failed both ways, and none can see inside a script.',
    nodes: [
      { id: 'r1', x: L, y: T, l: 'allow', s: 'git status:*', mine: 1 },
      { id: 'c1', x: R - 4, y: T, w: 124, l: 'git -C <path> status', b: { s: 'denied, should pass' }, f: { s: 'matched on verb' }, bad: 'b' },
      { id: 'r2', x: L, y: M, l: 'deny', s: 'git push', mine: 1 },
      { id: 'c2', x: R - 4, y: M, w: 124, l: 'git -C <path> push', b: { s: 'passed, should deny' }, f: { s: 'matched on verb' }, bad: 'b' },
      { id: 'r3', x: L, y: B, l: 'any text rule', mine: 1, b: {}, f: { l: 'OS sandbox', s: 'on for claude -p' }, fmine: 0 },
      { id: 'c3', x: R - 4, y: B, w: 124, l: 'python3 -c "…"', b: { s: 'invisible to rules' }, f: { s: 'writes blocked' }, bad: 'b' },
    ],
    edges: [
      { a: 'r1', b: 'c1', l: 'no match', only: 'b', bad: 1, dash: 1 }, { a: 'r1', b: 'c1', l: 'allows', only: 'f' },
      { a: 'r2', b: 'c2', l: 'no match', only: 'b', bad: 1, dash: 1 }, { a: 'r2', b: 'c2', l: 'denies', only: 'f', cut: 1 },
      { a: 'r3', b: 'c3', l: 'can’t see in', only: 'b', bad: 1, dash: 1 }, { a: 'r3', b: 'c3', l: 'contains', only: 'f', cut: 1 },
    ],
    nb: 'August 18 failed closed. October 2 failed open. No text rule reads inside python3 -c.',
    nf: 'Ship: match git and common CLIs on their real verb, a read-only git preset, and the OS sandbox on for claude -p, refusing to start without it.' },

  { n: 3, id: 'no-exit', t: 'No exit with work pending', claim: 'claude -p exits while its background shells and subagents still run.',
    nodes: [
      { id: 'cli', x: L, y: M, l: 'claude -p' },
      { id: 'sh', x: C, y: T, w: 112, l: 'Background shell', b: { s: 'still running' }, bad: 'b' },
      { id: 'sa', x: C, y: B, l: 'Subagent', b: { s: 'still running' }, bad: 'b' },
      { id: 'ex', x: R, y: M, l: 'Exit', b: { s: 'no report' }, f: { s: 'reports 0 left' }, bad: 'b' },
    ],
    edges: [
      { a: 'cli', b: 'sh', l: 'starts' }, { a: 'cli', b: 'sa', l: 'starts' },
      { a: 'cli', b: 'ex', l: 'exits', only: 'b', bad: 1 },
      { a: 'sh', b: 'ex', l: 'waited for', only: 'f' }, { a: 'sa', b: 'ex', l: 'or stopped', only: 'f' },
    ],
    nb: 'Four nights ended on “waiting on the task notification.”',
    nf: 'Ship: claude -p waits for or stops background shells and subagents, and reports how many were left.' },

  { n: 4, id: 'login', t: 'A login made for unattended runs', claim: 'My runner spends a model call every night just to learn if it’s logged in.',
    nodes: [
      { id: 'run', x: L, y: M, l: 'Runner', mine: 1 },
      { id: 'mc', x: C, y: T, l: 'Model call', s: 'every night', only: 'b', bad: 'b' },
      { id: 'au', x: C, y: B, w: 124, l: 'auth status --json', s: 'no model call', only: 'f' },
      { id: 'cr', x: R, y: M, l: 'Login', b: { s: 'expiry unknown' }, f: { s: 'expiry + warning' }, bad: 'b' },
    ],
    edges: [
      { a: 'run', b: 'mc', l: 'spends', only: 'b', bad: 1 }, { a: 'mc', b: 'cr', l: 'tests', only: 'b' },
      { a: 'run', b: 'au', l: 'asks', only: 'f' }, { a: 'au', b: 'cr', l: 'reads', only: 'f' },
    ],
    nb: 'And on October 15 the login still expired with no warning.',
    nf: 'Ship: claude auth status --json with no model call, showing when the login expires, plus a warning days ahead.' },

  { n: 5, id: 'quota', t: 'A quota I can read', claim: 'My 85% stop rule never fired, and an unpinned job drains the wrong model’s week.',
    nodes: [
      { id: 'rule', x: L, y: T, l: 'Stop rule', s: 'at 85% of week', mine: 1 },
      { id: 'ca', x: C, y: T, w: 118, b: { l: 'Usage cache', s: '313 h stale, KeyError' }, f: { l: 'usage --json', s: 'per model, resets' }, bad: 'b' },
      { id: 'q1', x: R - 4, y: T, w: 116, l: 'Top model’s week' },
      { id: 'job', x: L, y: B, l: 'Unpinned job', b: { s: '~96% of a week' }, f: { l: 'Job', s: 'quota ceiling flag' }, bad: 'b' },
      { id: 'q2', x: R - 4, y: B, w: 120, l: 'Other model’s week' },
    ],
    edges: [
      { a: 'rule', b: 'ca', l: 'reads' }, { a: 'ca', b: 'q1', l: 'stale', only: 'b', bad: 1, dash: 1 }, { a: 'ca', b: 'q1', l: 'live', only: 'f' },
      { a: 'ca', b: 'q2', only: 'f' },
      { a: 'job', b: 'q1', l: 'drains', only: 'b', bad: 1, t: .62 }, { a: 'job', b: 'q2', l: 'stops at cap', only: 'f' },
    ],
    nb: 'Each model has its own weekly allowance. Before this project, one unpinned scheduled job used about 96% of the top model’s week.',
    nf: 'Ship: claude usage --json per model with reset times, and a quota ceiling flag on claude -p.' },

  { n: 6, id: 'cost', t: 'Cost in the currency I pay', claim: 'On a Max plan the run reports dollars, but my real limit was quota.',
    nodes: [
      { id: 'run', x: L, y: M, l: 'Night run' },
      { id: 'usd', x: R, y: T, l: 'Dollar figure', s: 'API price, a proxy' },
      { id: 'q', x: R, y: B, l: 'Quota used', s: 'my real limit', b: { s: 'not shown' }, bad: 'b' },
    ],
    edges: [
      { a: 'run', b: 'usd', l: 'reports' },
      { a: 'run', b: 'q', l: 'not reported', only: 'b', bad: 1, dash: 1, cut: 1 }, { a: 'run', b: 'q', l: 'reports', only: 'f' },
    ],
    nb: '$202.16 across 33 nights is notional. The real cost was a share of a subscription.',
    nf: 'Ship: show quota used next to the dollar figure.' },

  { n: 7, id: 'turns', t: 'A turn limit in the CLI', claim: 'The SDK has --max-turns. The CLI doesn’t, so wall-clock time was my only ceiling.',
    nodes: [
      { id: 'sdk', x: L, y: T, l: 'Agent SDK', s: '--max-turns' },
      { id: 'cli', x: L, y: B, l: 'claude -p', b: { s: 'no turn limit' }, f: { s: '--max-turns + budget' }, bad: 'b' },
      { id: 'run', x: C, y: B, l: 'Night run' },
      { id: 'clk', x: R, y: B, l: 'Wall clock', b: { s: 'the only ceiling' }, f: { s: 'backstop' }, bad: 'b' },
    ],
    edges: [
      { a: 'sdk', b: 'cli', l: 'missing', only: 'b', bad: 1, dash: 1 }, { a: 'sdk', b: 'cli', l: 'same flag', only: 'f' },
      { a: 'cli', b: 'run', l: 'caps', only: 'f' }, { a: 'cli', b: 'run', l: 'runs', only: 'b' },
      { a: 'clk', b: 'run', l: 'stops' },
    ],
    nb: 'A runaway night had nothing to stop it but time.',
    nf: 'Ship: --max-turns and a tool-call budget on claude -p.' },

  { n: 8, id: 'profiles', t: 'One settings file, two kinds of session', claim: 'Closing the git hole for the night also blocked my own merges in the morning.',
    nodes: [
      { id: 'n', x: L, y: T, l: 'Night run' },
      { id: 'm', x: L, y: B, l: 'Me, morning' },
      { id: 'sf', x: C, y: M, l: 'Settings file', s: 'one for both', only: 'b', mine: 1 },
      { id: 'pn', x: C, y: T, l: 'Profile: night', s: 'no merge, no push', only: 'f', mine: 1 },
      { id: 'pm', x: C, y: B, l: 'Profile: morning', s: 'merge allowed', only: 'f', mine: 1 },
      { id: 'g', x: R, y: M, l: 'git merge, push' },
    ],
    edges: [
      { a: 'n', b: 'sf', l: 'loads', only: 'b' }, { a: 'm', b: 'sf', l: 'loads', only: 'b' },
      { a: 'sf', b: 'g', l: 'denies both', only: 'b', bad: 1, cut: 1 },
      { a: 'n', b: 'pn', l: 'picks', only: 'f' }, { a: 'm', b: 'pm', l: 'picks', only: 'f' },
      { a: 'pn', b: 'g', l: 'denies', only: 'f', cut: 1 }, { a: 'pm', b: 'g', l: 'allows', only: 'f' },
    ],
    nb: 'One file serves the unattended night and the attended morning.',
    nf: 'Ship: named permission profiles, chosen per run.' },

  { n: 9, id: 'transcripts', t: 'Transcripts I can query', claim: 'My health checks reverse-engineer session files, and read the first prompt to tell night from day.',
    nodes: [
      { id: 'hc', x: L, y: M, l: 'Health checks', mine: 1 },
      { id: 'fl', x: C, y: T, l: 'Session files', s: 'undocumented', only: 'b', bad: 'b' },
      { id: 'fp', x: C, y: B, l: 'First prompt', s: 'night or day?', only: 'b', bad: 'b' },
      { id: 'ix', x: C, y: M, l: 'Session index', s: 'documented', only: 'f' },
      { id: 'tg', x: C, y: B, l: 'Run tags', s: 'set per run', only: 'f' },
      { id: 'ss', x: R, y: M, l: 'Sessions' },
    ],
    edges: [
      { a: 'hc', b: 'fl', l: 'parses', only: 'b', bad: 1 }, { a: 'hc', b: 'fp', l: 'guesses from', only: 'b', bad: 1 },
      { a: 'fl', b: 'ss', only: 'b' }, { a: 'fp', b: 'ss', only: 'b' },
      { a: 'hc', b: 'ix', l: 'queries', only: 'f' }, { a: 'ix', b: 'ss', l: 'lists', only: 'f' }, { a: 'tg', b: 'ss', l: 'labels', only: 'f' },
    ],
    nb: 'Every check depends on file formats I reverse-engineered.',
    nf: 'Ship: a documented session index with tags I set per run.' },

  { n: 10, id: 'skills', t: 'Skills without user permissions', claim: 'Loading only project settings, which the fence needs, also drops my skills.',
    nodes: [
      { id: 'ses', x: L, y: M, l: 'Night session' },
      { id: 'ps', x: C, y: T, l: 'Project settings', s: 'the fence', mine: 1 },
      { id: 'us', x: C, y: B, l: 'User settings', s: 'skills + permissions', b: { s: 'all or nothing' }, bad: 'b' },
      { id: 'sk', x: R, y: B, l: 'My skills', b: { s: 'via symlinks' } },
    ],
    edges: [
      { a: 'ses', b: 'ps', l: 'loads' },
      { a: 'ses', b: 'us', l: 'dropped', only: 'b', bad: 1, dash: 1, cut: 1 },
      { a: 'us', b: 'sk', l: 'holds', only: 'b' },
      { a: 'ses', b: 'sk', l: 'skills only', only: 'f', t: .62 },
    ],
    nb: 'I worked around it with symlinks.',
    nf: 'Ship: choose skills, permissions and hooks separately.' },
];

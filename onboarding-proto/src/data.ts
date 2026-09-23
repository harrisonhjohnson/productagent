import type { Cadence, Model, Noun, Starter, StarterId } from './types';

export const BEATS = [
  { id: 0, code: 'B0', name: 'Cold boot' },
  { id: 1, code: 'B1', name: 'Lid promise' },
  { id: 2, code: 'B2', name: 'Four words' },
  { id: 3, code: 'B3', name: 'First Loop' },
  { id: 4, code: 'B4', name: 'Overnight' },
  { id: 5, code: 'B5', name: 'Morning' },
  { id: 6, code: 'B6', name: 'Karma' },
  { id: 7, code: 'B7', name: 'Phone' },
  { id: 8, code: 'B8', name: 'You’re live' },
] as const;

export const NOUNS: { word: Noun; gloss: string; key: string; body: string }[] = [
  {
    word: 'Loop',
    key: '1',
    gloss: 'a goal that keeps renewing',
    body: 'You write it once. It comes back every night it is due, until you park it or it finishes. The agent never edits the Loop. You do.',
  },
  {
    word: 'Run',
    key: '2',
    gloss: 'one pass at it, tonight',
    body: 'A bounded overnight pass: one Loop, a budget, a timeout, a fence it cannot climb. In the morning you get four plain sentences. Then it sleeps.',
  },
  {
    word: 'Order',
    key: '3',
    gloss: 'a one-off note for tonight',
    body: 'Something that is not a Loop — just tonight. Orders go first. Loops fill the remaining slots. You can send one from the phone later.',
  },
  {
    word: 'Decision',
    key: '4',
    gloss: 'what only you can settle',
    body: 'Anything the Run could not settle on its own. It never guesses. It hands the Decision back in the morning and waits.',
  },
];

export const CADENCES: Cadence[] = ['nightly', 'every-2nd-night', 'every-3rd-night', 'weekly'];
export const MODELS: Model[] = ['sonnet', 'opus', 'fable'];

export const STARTERS: Starter[] = [
  {
    id: 'changelogs',
    starterId: 'changelogs',
    name: 'Competitors’ changelogs',
    goal: 'Watch three competitors’ changelogs. Tell me what changed and whether it matters.',
    blurb: 'A cheap watch. Public pages only.',
    budget: 2,
    cadence: 'weekly',
    model: 'sonnet',
    report: {
      trying: 'watch three competitors’ changelogs and say whether it matters.',
      did: 'read Linear, Notion, and Amplitude public changelogs since last week; wrote a one-page brief.',
      decided: 'left Amplitude’s pricing page alone; it is not a changelog.',
      need: 'is “custom agents” a real threat to our loop story, or noise?',
      where: 'pm/nights/loops/L-01.md, reports/changelogs-2026-09-15.md',
    },
  },
  {
    id: 'backlog',
    starterId: 'backlog',
    name: 'Backlog fix',
    goal: 'Ship one small fix from the backlog. Verify it renders before you report it.',
    blurb: 'One item. Never push. Never touch main.',
    budget: 6,
    cadence: 'nightly',
    model: 'opus',
    report: {
      trying: 'ship one small fix from the backlog and verify it renders.',
      did: 'added the county filter and checked the page in a headless browser.',
      decided: 'left the mobile layout alone; it is a separate backlog item.',
      need: 'merge branch night/2026-09-15 if the screenshot looks right.',
      where: 'pm/nights/loops/L-01.md, 009-site/app/permits.tsx',
    },
  },
  {
    id: 'tickets',
    starterId: 'tickets',
    name: 'Support ticket themes',
    goal: 'Read yesterday’s support tickets. Cluster them. Name the top three themes.',
    blurb: 'Cluster. Do not file bugs.',
    budget: 3,
    cadence: 'nightly',
    model: 'sonnet',
    report: {
      trying: 'cluster yesterday’s support tickets and name the top three themes.',
      did: 'read 41 tickets; three themes cover 28 of them.',
      decided: 'did not file bugs; clustering only.',
      need: 'is “export never finishes” a product bug or a known warehouse delay?',
      where: 'pm/nights/loops/L-01.md, reports/tickets-2026-09-15.md',
    },
  },
  {
    id: 'launch',
    starterId: 'launch',
    name: 'Launch checklist',
    goal: 'Check every box on the launch checklist against the repo. Flag the ones that lie.',
    blurb: 'Flag. Do not uncheck.',
    budget: 2,
    cadence: 'every-2nd-night',
    model: 'sonnet',
    report: {
      trying: 'check every box on the launch checklist against the repo.',
      did: '18 of 22 boxes match the repo; 4 claim work that is not there.',
      decided: 'did not uncheck them; flagged only.',
      need: 'which of the four lies is actually still in flight?',
      where: 'pm/nights/loops/L-01.md, pm/launch-checklist.md',
    },
  },
  {
    id: 'weekly',
    starterId: 'weekly',
    name: 'Weekly update',
    goal: 'Draft the weekly update from this week’s reports. I edit. I send.',
    blurb: 'A draft. You send.',
    budget: 4,
    cadence: 'weekly',
    model: 'opus',
    report: {
      trying: 'draft the weekly update from this week’s reports.',
      did: 'wrote a 12-line draft from the four morning reports.',
      decided: 'left the metrics table empty; the numbers are yours.',
      need: 'edit, then send. The draft is in reports/weekly-2026-09-15.md.',
      where: 'pm/nights/loops/L-01.md, reports/weekly-2026-09-15.md',
    },
  },
  {
    id: 'icp',
    starterId: 'icp',
    name: 'ICP companies',
    goal: 'Find ten companies that look like our best customer. Say why, with links.',
    blurb: 'Names and why. No outreach.',
    budget: 3,
    cadence: 'every-3rd-night',
    model: 'sonnet',
    report: {
      trying: 'find ten companies that look like our best customer, with why and links.',
      did: 'listed ten, each with a public page and a one-line why.',
      decided: 'skipped agencies; they look similar and are not the customer.',
      need: 'which three should I deepen next run?',
      where: 'pm/nights/loops/L-01.md, reports/icp-2026-09-15.md',
    },
  },
];

export function starterById(id: StarterId): Starter {
  return STARTERS.find((s) => s.id === id) ?? STARTERS[0];
}

export function formatKnobs(budget: number, cadence: Cadence, model: Model): string {
  return `${cadence} · ${model} · $${budget} a run`;
}

export function loopMarkdown(draft: {
  name: string;
  goal: string;
  budget: number;
  cadence: Cadence;
  model: Model;
}): string {
  return `## L-01 — ${draft.name}
- status: draft
- goal: ${draft.goal}
- budget_per_iteration_usd: ${draft.budget}
- budget_loop_total_usd: ${draft.budget * 8}
- cadence: ${draft.cadence}
- model: claude-${draft.model}-5
- review_by: 2026-10-31`;
}

export const BOOT_LINES = [
  'productagent · post-install',
  'laying machine at ~/loops',
  'fence loaded · spend, push, merge denied',
  'battery floor 30%',
  'ac gate · wait until plugged in',
  'schedule armed',
  'loops: 0',
  'nothing runs until you write a loop',
];

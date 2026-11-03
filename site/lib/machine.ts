import 'server-only';
import fs from 'node:fs';
import path from 'node:path';

export type Owner = 'hardware' | 'mine' | 'claude-code' | 'output' | 'person';
export type Attribution = 'machine' | 'agent' | 'shared' | 'design';
export type Part = { id: string; label: string; detail?: string; owner: Owner };
export type Link = { from: string; to: string; verb: string };
export type Break = {
  n: number;
  title: string;
  attribution: Attribution;
  at: { part: string } | { link: [string, string] };
  dates: string[];
  fix: 'shipped' | 'open';
  fix_note: string;
  receipts: { label: string; href: string }[];
};
export type Ask = { n: number; id: string; title: string; breaks: number[] };
export type Machine = { version: 1; through: string; about: string; parts: Part[]; links: Link[]; breaks: Break[]; asks: Ask[] };

export const ATTRIBUTION_WORD: Record<Attribution, string> = {
  machine: 'Machine',
  agent: 'Agent',
  shared: 'Shared',
  design: 'By design',
};

const FILE = path.resolve(process.cwd(), '..', 'evidence', 'machine.json');

export function getMachine(): Machine {
  return JSON.parse(fs.readFileSync(/*turbopackIgnore: true*/ FILE, 'utf8')) as Machine;
}

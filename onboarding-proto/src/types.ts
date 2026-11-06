export type BeatId = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;

export type Noun = 'Loop' | 'Run' | 'Order' | 'Decision';

export type Cadence = 'nightly' | 'every-2nd-night' | 'every-3rd-night' | 'weekly';

export type Model = 'sonnet' | 'opus' | 'fable';

export type StarterId =
  | 'changelogs'
  | 'backlog'
  | 'tickets'
  | 'launch'
  | 'weekly'
  | 'icp';

export type Draft = {
  starterId: StarterId;
  name: string;
  goal: string;
  budget: number;
  cadence: Cadence;
  model: Model;
};

export type MorningLines = {
  trying: string;
  did: string;
  decided: string;
  need: string;
  where: string;
};

export type Starter = Draft & {
  id: StarterId;
  blurb: string;
  report: MorningLines;
};

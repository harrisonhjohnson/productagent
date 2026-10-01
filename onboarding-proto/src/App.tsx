import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import './styles.css';
import {
  B0ColdBoot,
  B1LidPromise,
  B2Loadout,
  B3CreateLoop,
  B4Timelapse,
  B5Morning,
  B6Karma,
  B7Phone,
  B8Live,
  beatMeta,
} from './beats';
import { HelpOverlay, Shell } from './chrome';
import { NOUNS, STARTERS } from './data';
import { Grain, NightSky, QuietRoom } from './scenes';
import type { BeatId, Draft, Noun, StarterId } from './types';

const EMPTY_ARMED: Record<Noun, boolean> = {
  Loop: false,
  Run: false,
  Order: false,
  Decision: false,
};

function draftFrom(id: StarterId): Draft {
  const s = STARTERS.find((x) => x.id === id) ?? STARTERS[0];
  return {
    starterId: s.id,
    name: s.name,
    goal: s.goal,
    budget: s.budget,
    cadence: s.cadence,
    model: s.model,
  };
}

export default function App() {
  const [beat, setBeat] = useState<BeatId>(0);
  const [armed, setArmed] = useState(EMPTY_ARMED);
  const [focused, setFocused] = useState<Noun>('Loop');
  const [draft, setDraft] = useState<Draft>(() => draftFrom('changelogs'));
  const [bootReady, setBootReady] = useState(false);
  const [nightReady, setNightReady] = useState(false);
  const [settled, setSettled] = useState(false);
  const [help, setHelp] = useState(false);
  const [flash, setFlash] = useState(false);
  const mainRef = useRef<HTMLDivElement>(null);

  const allArmed = NOUNS.every((n) => armed[n.word]);
  const meta = beatMeta(beat);
  const roomWarm = beat >= 5 ? 0.72 : beat === 4 ? 0.12 : 0;
  const skyDim = beat >= 5;

  const go = useCallback((id: BeatId) => {
    setBeat(id);
    setHelp(false);
    if (id === 0) setBootReady(false);
    if (id === 4) setNightReady(false);
  }, []);

  const next = useCallback(() => {
    setBeat((b) => (b < 8 ? ((b + 1) as BeatId) : b));
  }, []);

  const back = useCallback(() => {
    setHelp(false);
    setBeat((b) => (b > 0 ? ((b - 1) as BeatId) : b));
  }, []);

  const arm = useCallback((word: Noun) => {
    setFocused(word);
    setArmed((a) => ({ ...a, [word]: true }));
  }, []);

  const pick = useCallback((id: StarterId) => setDraft(draftFrom(id)), []);

  const replay = useCallback(() => {
    setBeat(0);
    setArmed(EMPTY_ARMED);
    setFocused('Loop');
    setBootReady(false);
    setNightReady(false);
    setSettled(false);
    setHelp(false);
  }, []);

  const tryAdvance = useCallback(() => {
    if (help) {
      setHelp(false);
      return;
    }
    if (beat === 0 && !bootReady) {
      setBootReady(true);
      return;
    }
    if (beat === 2 && !allArmed) {
      setFlash(true);
      window.setTimeout(() => setFlash(false), 600);
      return;
    }
    if (beat === 4 && !nightReady) {
      setNightReady(true);
      return;
    }
    if (beat === 5 && !settled) {
      setSettled(true);
      return;
    }
    if (beat === 8) return;
    next();
  }, [allArmed, beat, bootReady, help, next, nightReady, settled]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement | null;
      const typing = el && (el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || el.tagName === 'INPUT');

      if (e.key === '?' || (e.key === '/' && e.shiftKey)) {
        if (!typing) {
          e.preventDefault();
          setHelp((h) => !h);
        }
        return;
      }
      if (e.key === 'Escape') {
        if (help) {
          setHelp(false);
          return;
        }
        if (beat === 0) setBootReady(true);
        if (beat === 4) setNightReady(true);
        return;
      }
      if ((e.key === 'r' || e.key === 'R') && !typing) {
        e.preventDefault();
        replay();
        return;
      }
      if (e.key === 'Backspace' && !typing) {
        e.preventDefault();
        back();
        return;
      }
      if (e.key === 'ArrowLeft' && !typing) {
        e.preventDefault();
        back();
        return;
      }
      if ((e.key === 'Enter' || e.key === ' ') && !typing) {
        e.preventDefault();
        tryAdvance();
        return;
      }
      if (help || typing) return;

      if (beat === 2 && ['1', '2', '3', '4'].includes(e.key)) {
        const word = NOUNS[Number(e.key) - 1].word;
        arm(word);
      }
      if (beat === 3 && ['1', '2', '3', '4', '5', '6'].includes(e.key)) {
        pick(STARTERS[Number(e.key) - 1].id);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [arm, back, beat, help, pick, replay, tryAdvance]);

  useEffect(() => {
    mainRef.current?.querySelector<HTMLElement>('.stage')?.focus();
  }, [beat]);

  const hint = useMemo(() => {
    if (beat === 2 && !allArmed) return 'arm all four (1–4)';
    if (beat === 0 && !bootReady) return 'skip boot, or wait';
    if (beat === 4 && !nightReady) return 'skip the night, or wait';
    if (beat === 5 && !settled) return 'mark the Decision seen';
    return meta.hint;
  }, [allArmed, beat, bootReady, meta.hint, nightReady, settled]);

  return (
    <div ref={mainRef} className={flash ? 'app is-flash' : 'app'}>
      <NightSky dim={skyDim} />
      <QuietRoom warm={roomWarm} />
      <Grain />
      <Shell beat={beat} onJump={go} helpOpen={help} hint={hint} title={meta.title} kicker={meta.kicker}>
        {beat === 0 && <B0ColdBoot active={beat === 0} complete={bootReady} onReady={setBootReady} />}
        {beat === 1 && <B1LidPromise />}
        {beat === 2 && <B2Loadout armed={armed} focused={focused} onArm={arm} onFocus={setFocused} />}
        {beat === 3 && (
          <B3CreateLoop draft={draft} onPick={pick} onPatch={(p) => setDraft((d) => ({ ...d, ...p }))} />
        )}
        {beat === 4 && (
          <B4Timelapse active={beat === 4} complete={nightReady} draft={draft} onReady={setNightReady} />
        )}
        {beat === 5 && <B5Morning draft={draft} settled={settled} onSettle={() => setSettled(true)} />}
        {beat === 6 && <B6Karma />}
        {beat === 7 && <B7Phone active={beat === 7} />}
        {beat === 8 && <B8Live draft={draft} onReplay={replay} />}
      </Shell>
      {help ? <HelpOverlay onClose={() => setHelp(false)} /> : null}
    </div>
  );
}

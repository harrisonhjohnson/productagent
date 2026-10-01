import { useEffect, useState } from 'react';

export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() =>
    typeof window !== 'undefined' ? window.matchMedia('(prefers-reduced-motion: reduce)').matches : false,
  );

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setReduced(mq.matches);
    onChange();
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  return reduced;
}

export function useTypedLines(lines: string[], reduced: boolean, active: boolean, ms = 420) {
  const [count, setCount] = useState(reduced || !active ? lines.length : 0);
  const key = lines.join('\n');

  useEffect(() => {
    if (!active) return;
    if (reduced) {
      setCount(lines.length);
      return;
    }
    setCount(0);
    let i = 0;
    const id = window.setInterval(() => {
      i += 1;
      setCount(i);
      if (i >= lines.length) window.clearInterval(id);
    }, ms);
    return () => window.clearInterval(id);
    // lines identity is represented by key
  }, [active, reduced, key, ms, lines.length]);

  return { visible: lines.slice(0, count), done: count >= lines.length, skip: () => setCount(lines.length) };
}

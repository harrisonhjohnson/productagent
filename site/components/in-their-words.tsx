import Link from 'next/link';
import { QUOTES, type Quote } from '@/lib/quotes';

export function QuoteCard({ q, compact = false }: { q: Quote; compact?: boolean }) {
  return (
    <figure className={`quote${compact ? ' quote-compact' : ''}`} id={q.id}>
      <blockquote>
        <p>{q.text}</p>
      </blockquote>
      <figcaption>
        <span className="quote-who">{q.who}</span>
        <a href={q.url} target="_blank" rel="noreferrer">{q.where} · {q.date} ↗</a>
      </figcaption>
      <p className="quote-took"><span>in loops</span>{q.took}</p>
    </figure>
  );
}

export function InTheirWords() {
  const picks = QUOTES.filter((q) => q.home);
  return (
    <section className="words-section" aria-labelledby="words-heading">
      <p className="section-label" id="words-heading">IN THEIR OWN WORDS</p>
      <p className="words-lede">
        Not my case for this. Anthropic&apos;s. The people building Claude Code say the next step is loops, and the
        step after that is memory. Every quote here is verbatim and linked.
      </p>
      <div className="quote-grid">
        {picks.map((q) => <QuoteCard key={q.id} q={q} compact />)}
      </div>
      <p className="words-more">
        <Link href="/why">{QUOTES.length} quotes, sourced and dated, and what each one turned into →</Link>
      </p>
    </section>
  );
}

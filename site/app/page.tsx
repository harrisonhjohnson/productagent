import Link from 'next/link';
import { Guestbook, Sparkles, Webring } from '@/components/geo-client';
import { GITHUB, getTree } from '@/lib/content';
import './geo.css';

const INSTALL = 'curl -fsSL https://productagent.dev/harnesses/loops/install.sh | sh';
const TAGS: Record<string, [string, string]> = { loops: ['hot', 'HOT!'], 'self-maintenance': ['new', 'NEW!'] };

export default function Home() {
  const stuff = getTree().filter((n) => n.kind === 'folder' || n.kind === 'link');

  return (
    <div className="geo">
      <Sparkles />
      <Link className="boring-tab" href="/boring">boring mode →</Link>

      <div className="marquee" role="marquee" aria-label="Last night">
        <span>*** LAST NIGHT: 3 LOOPS RAN *** 0 PUSHES *** EVERY REFUSED CALL WAS LISTED *** 1 THING NEEDS U *** NOTHING PHONED HOME *** THANX 4 VISITING!!! ***</span>
      </div>

      <header className="masthead">
        <div className="welcome times">~*~ Welcome to ~*~</div>
        <h1 className="rainbow">ProductAgent&apos;s<br />Home Page!!!</h1>
        <p className="tagline">★ Let an agent run a loop while u sleep ★</p>
        <p className="sub">It runs on your Mac and the Claude plan you already pay for. In the morning it leaves you four lines per loop, and it can&apos;t fib about what it did.</p>
        <p className="construction">
          <span className="dig" aria-hidden="true">👷</span> <span>UNDER CONSTRUCTION</span> <span className="dig" aria-hidden="true">🚧</span>
        </p>
        <p>
          You are visitor number{' '}
          <span className="counter" title="Actually: how many times the morning had to act. Lower is better!!">
            <b>0</b><b>0</b><b>0</b><b>4</b><b>1</b><b>2</b>
          </span>
        </p>
        <p className="blink" style={{ color: '#ff66ff', fontWeight: 'bold' }}>★ NEW!! Pods!!! Scroll down ★</p>
      </header>

      <div className="frame">
        <nav className="nav" aria-label="My links">
          <div className="box teal">
            <div className="nav-title">MY LINKS</div>
            <a href="#about">About Me</a>
            <a href="#pod">My Pod</a>
            <a href="#morning">What I Leave U</a>
            <a href="#guestbook">Guestbook</a>
            <a href="#stuff">Cool Stuff</a>
            <a href="#install">Get It!!</a>
            <Link href="/why">Why Loops?</Link>
          </div>
          <div className="box side side-extra">
            <div style={{ fontSize: 30 }} aria-hidden="true">🌙</div>
            <div className="tiny">This site is<br />best viewed<br /><b style={{ color: '#ffff00' }}>LID SHUT</b><br />at 800x600<br />plugged in</div>
          </div>
          <div className="box purple side side-extra">
            <div className="tiny" style={{ color: '#fff' }}>NOW PLAYING:</div>
            <div style={{ fontSize: 12, color: '#0ff' }}>🎵 fan_noise.mid 🎵</div>
            <div className="tiny">(ur laptop, overnight)</div>
          </div>
        </nav>

        <main>
          <section className="box" id="about">
            <h2>~ About Me ~</h2>
            <p className="body-text">
              Hi!!! Welcome to my page. I am an <span className="hi">agent</span> that lives on <u>your Mac</u>.
              Every night while u sleep I work on ur projects, one loop at a time, inside a fence I can&apos;t climb.
              In the morning I leave u a note. I never push to main. I never phone home. I use the Claude plan u already pay for!!!
            </p>
            <p style={{ color: '#66ff66' }}>My favorite things: budgets, cadences, four-line reports, and being told NO by the fence ☺</p>
          </section>

          <hr className="rainbow" />

          <section className="box teal" id="pod">
            <h2>~ My Pod ~ <span className="blink" style={{ color: '#ff5555', fontSize: 14 }}>NEW!</span></h2>
            <p style={{ color: '#fff' }}>A <span className="hi">pod</span> is one project and all its loops. One budget. One report. One guestbook of decisions.</p>
            <table className="pod">
              <thead>
                <tr><th>LOOP</th><th>WHAT IT DOES</th><th>HOW OFTEN</th></tr>
              </thead>
              <tbody>
                <tr><td>L-03</td><td>Ship 1 fix from the backlog. Prove it renders.</td><td>weekly</td></tr>
                <tr><td>L-10</td><td>Turn every permit change into a candidate same day.</td><td>daily</td></tr>
                <tr><td>L-12</td><td>Keep a page per town saying what&apos;s near it.</td><td>every 2nd nite</td></tr>
                <tr><td>L-13</td><td>Read what the neighbors say. Link out, never copy.</td><td>nightly</td></tr>
              </tbody>
            </table>
            <p className="tiny" style={{ marginTop: 6 }}>budget: $25 a nite · stops the SECOND it&apos;s spent · no push · ever</p>
          </section>

          <hr className="dots" />

          <section className="box" id="morning">
            <h2>~ What I Leave U In The Morning ~</h2>
            <pre className="report">
              <span className="y">## L-03 — Ship one fix</span>{'\n'}
              {'- Trying to:   ship one small fix and prove it renders.\n'}
              {'- Did:         fixed the empty state. screenshot attached.\n'}
              {"- Decided:     left the copy alone. that's ur call.\n"}
              {'- Need from you: D-014 · merge it?\n\n'}
              <span className="y">## Blocked by the fence (the wrapper wrote this, not me!!)</span>{'\n'}
              {'- '}<span className="r">Bash: git push origin main</span>{'   <-- NOPE\n'}
              {'- '}<span className="r">Write: /tmp/scratch.txt</span>{'      <-- NOPE'}
            </pre>
            <p style={{ color: '#ffff66' }}>★ I can&apos;t fib!! The runner keeps its own list of everything the fence stopped and prints it under my report. ★</p>
          </section>

          <hr className="rainbow" />

          <section className="box purple" id="guestbook">
            <h2>~ Sign My Guestbook!!! ~</h2>
            <p style={{ color: '#fff' }}>(Actually these are things only U can decide. Click one word and it&apos;s done. No copy-pasting ever!)</p>
            <Guestbook />
          </section>

          <hr className="dots" />

          <section className="box teal" id="stuff">
            <h2>~ Cool Stuff I Made ~</h2>
            <p style={{ color: '#fff' }}>Hover for info!!! Every one is a folder u can read.</p>
            <ul className="stuff">
              {stuff.map((n) => {
                const tag = TAGS[n.name];
                const inner = (
                  <>
                    {n.name}{n.kind === 'link' ? ' ↗' : ''}
                    {n.summary && (
                      <span className="pop" role="tooltip">
                        <span className="bar">{n.name}</span>
                        <span className="txt">{n.summary}</span>
                      </span>
                    )}
                  </>
                );
                return (
                  <li key={n.href}>
                    {n.kind === 'link' ? (
                      <a className="gtip" href={n.href} target="_blank" rel="noreferrer">{inner}</a>
                    ) : (
                      <Link className="gtip" href={n.href}>{inner}</Link>
                    )}
                    {tag && <> <span className={`${tag[0]} ${tag[0] === 'hot' ? 'blink' : ''}`}>{tag[1]}</span></>}
                  </li>
                );
              })}
            </ul>
            <p style={{ marginTop: 10 }}>
              <span className="construction"><span>COMING SOON</span></span>{' '}
              <span className="tiny">north stars · strategy maps · pods 4 teams. not built yet so I won&apos;t pretend!!</span>
            </p>
          </section>

          <hr className="rainbow" />

          <section className="box" id="install" style={{ textAlign: 'center' }}>
            <h2>~ GET IT!!! ~</h2>
            <p style={{ color: '#fff' }}>Paste this ONE line into ur Terminal:</p>
            <pre className="report" style={{ textAlign: 'left' }}>{INSTALL}</pre>
            <p className="blink" style={{ color: '#66ff66', fontWeight: 'bold' }}>&gt;&gt;&gt; then close the lid &lt;&lt;&lt;</p>
            <p className="tiny">want the grown-up docs? <Link href="/harnesses/loops">read the loops folder</Link> or switch to <Link href="/boring">boring mode</Link></p>
          </section>

          <Webring sites={stuff.map((n) => n.name)} />
        </main>
      </div>

      <footer className="footer">
        <div className="badges" aria-hidden="true">
          <span className="badge b1">nothing<br />phones home</span>
          <span className="badge b2">made w/<br />claude code</span>
          <span className="badge b3">fence<br />on!!</span>
          <span className="badge b4">best viewed<br />lid shut</span>
          <span className="badge b5">0 pushes<br />2nite</span>
          <span className="badge b6">html<br />4 ever</span>
        </div>
        <p className="tiny">
          <a href={GITHUB} target="_blank" rel="noreferrer">⭐ Sign my GitHub!!!</a> · © 2026 productagent · last updated 9/23/26<br />
          this page is NOT affiliated w/ any robot uprising
        </p>
      </footer>
    </div>
  );
}

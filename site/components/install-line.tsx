'use client';

import { useEffect, useState } from 'react';

export const INSTALL_COMMAND = 'curl -fsSL https://productagent.dev/install.sh | bash';

type AgentKey = 'claude' | 'chatgpt';

const AGENTS: Record<AgentKey, {
  name: string;
  plan: string;
  cli: string;
  cliInstall: string;
  signin: string;
  signinNote: string;
}> = {
  claude: {
    name: 'Claude',
    plan: 'a Claude Pro or Max plan',
    cli: 'Claude Code',
    cliInstall: 'curl -fsSL https://claude.ai/install.sh | bash',
    signin: 'claude',
    signinNote: 'a browser tab opens; sign in with the same account you use in the Claude app, then type /exit',
  },
  chatgpt: {
    name: 'ChatGPT',
    plan: 'a ChatGPT Plus or Pro plan',
    cli: 'Codex',
    cliInstall: 'npm install -g @openai/codex',
    signin: 'codex login',
    signinNote: 'a browser tab opens; sign in with the same account you use in ChatGPT',
  },
};

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }
  return (
    <button type="button" className="install-copy" onClick={copy} aria-live="polite">
      {copied ? 'copied' : 'copy'}
    </button>
  );
}

function Line({ cmd, id }: { cmd: string; id?: string }) {
  return (
    <div className="install-row">
      <code className="install-cmd" id={id}>{cmd}</code>
      <CopyButton text={cmd} />
    </div>
  );
}

export function InstallLine() {
  const [agent, setAgent] = useState<AgentKey | null>(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('pa-agent');
      if (saved === 'claude' || saved === 'chatgpt') setAgent(saved);
    } catch {}
  }, []);

  function pick(a: AgentKey) {
    setAgent(a);
    try { localStorage.setItem('pa-agent', a); } catch {}
  }

  const a = agent ? AGENTS[agent] : null;

  return (
    <div className="install">
      <p className="install-label">INSTALL LOOPS · MACOS · RUNS ON THE PLAN YOU ALREADY PAY FOR</p>

      <div className="agent-pick" role="radiogroup" aria-label="Which do you use?">
        <span className="agent-pick-q">I use</span>
        {(Object.keys(AGENTS) as AgentKey[]).map((k) => (
          <button
            key={k}
            type="button"
            role="radio"
            aria-checked={agent === k}
            className={`agent-tile${agent === k ? ' is-on' : ''}`}
            onClick={() => pick(k)}
          >
            <span className={`agent-mark agent-mark-${k}`} aria-hidden="true" />
            {AGENTS[k].name}
          </button>
        ))}
      </div>

      {!a && (
        <p className="install-note">
          Pick one and the steps below adapt. Either way it runs on your own Mac, on your own subscription, and
          nothing phones home.
        </p>
      )}

      {a && (
        <ol className="install-steps">
          <li>
            <p className="install-step-title">Get {a.cli}, the terminal version of {a.name}.</p>
            <p className="install-step-note">
              Loops runs {a.cli} for you overnight. It uses {a.plan}, the one you already have. Open Terminal
              (press <kbd>⌘</kbd> <kbd>space</kbd>, type <em>Terminal</em>, press return) and paste:
            </p>
            <Line cmd={a.cliInstall} />
            <p className="install-step-note">Then sign in once. Type <code>{a.signin}</code> and press return: {a.signinNote}.</p>
            <p className="install-step-note install-step-skip">Already have {a.cli}? Skip to step 2.</p>
          </li>
          <li>
            <p className="install-step-title">Install Loops. One line, then four questions.</p>
            <Line cmd={INSTALL_COMMAND} id="install-command" />
            <p className="install-step-note">
              Puts the machine in <code>~/loops</code>, notices that {a.cli} is there, asks what to work on, how often,
              how much brain and what it may spend, then writes your first loop. Nothing runs until tonight, and only
              if the laptop is plugged in. Stop it any time with <code>--off</code>.
            </p>
          </li>
        </ol>
      )}
    </div>
  );
}

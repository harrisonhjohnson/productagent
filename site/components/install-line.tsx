'use client';

import { useState } from 'react';

export const INSTALL_COMMAND = 'curl -fsSL https://productagent.dev/install.sh | bash';

export function InstallLine() {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(INSTALL_COMMAND);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="install">
      <p className="install-label">INSTALL LOOPS · ONE LINE · MACOS</p>
      <div className="install-row">
        <code className="install-cmd" id="install-command">{INSTALL_COMMAND}</code>
        <button type="button" className="install-copy" onClick={copy} aria-live="polite">
          {copied ? 'copied' : 'copy'}
        </button>
      </div>
      <p className="install-note">
        Installs the machine into <code>~/loops</code>, then asks four questions and writes your first loop. Claude
        Code or Codex. Nothing runs until tonight, and only if the laptop is plugged in. Stop it any time with{' '}
        <code>--off</code>.
      </p>
    </div>
  );
}

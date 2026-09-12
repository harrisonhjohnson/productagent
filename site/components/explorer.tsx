'use client';

import Link from 'next/link';
import {
  ChevronRight,
  ExternalLink,
  File,
  FileCode2,
  FileText,
  Folder,
  FolderOpen,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import type { TreeNode } from '@/lib/content';
import { useScrollProgress } from './use-scroll-progress';

type VisibleNode = TreeNode & { level: number; id: string };

function idOf(n: TreeNode) {
  return n.slug.join('/');
}

function collectFolders(nodes: TreeNode[], result = new Set<string>()) {
  nodes.forEach((node) => {
    if (node.kind === 'folder') {
      result.add(idOf(node));
      collectFolders(node.children ?? [], result);
    }
  });
  return result;
}

function flattenTree(nodes: TreeNode[], expanded: Set<string>, level = 0): VisibleNode[] {
  return nodes.flatMap((node) => [
    { ...node, level, id: idOf(node) },
    ...(node.kind === 'folder' && expanded.has(idOf(node))
      ? flattenTree(node.children ?? [], expanded, level + 1)
      : []),
  ]);
}

function NodeIcon({ node, open }: { node: TreeNode; open: boolean }) {
  const props = { size: 14, strokeWidth: 1.55, 'aria-hidden': true } as const;
  if (node.kind === 'folder') return open ? <FolderOpen {...props} /> : <Folder {...props} />;
  if (node.kind === 'code') return <FileCode2 {...props} />;
  if (node.kind === 'text') return <FileText {...props} />;
  if (node.kind === 'link') return <ExternalLink {...props} />;
  return <File {...props} />;
}

type Props = {
  tree: TreeNode[];
  activeSlug?: string[];
  trackScroll?: boolean;
  label: string;
};

export function Explorer({ tree, activeSlug, trackScroll = false, label }: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(() => collectFolders(tree));
  const progress = useScrollProgress();
  const visibleNodes = useMemo(() => flattenTree(tree, expanded), [tree, expanded]);
  const activeId = activeSlug?.join('/');

  const toggleFolder = (id: string) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const scrollIndex = Math.min(visibleNodes.length - 1, Math.floor(progress * visibleNodes.length));

  return (
    <>
      <div className="column-labels" aria-hidden="true">
        <span>name</span>
        <span>tier / size</span>
      </div>

      <div className="file-tree" role="tree" aria-label={label}>
        {visibleNodes.map((node, index) => {
          const isFolder = node.kind === 'folder';
          const isOpen = isFolder && expanded.has(node.id);
          const isCurrent = activeId ? node.id === activeId : trackScroll && index === scrollIndex;
          const external = node.kind === 'link';

          return (
            <div
              className={`tree-row ${isFolder ? 'folder-row' : ''} node-kind-${node.kind} ${isCurrent ? 'is-current' : ''}`}
              key={node.id}
              role="treeitem"
              aria-expanded={isFolder ? isOpen : undefined}
              aria-current={isCurrent ? 'page' : undefined}
              style={{ '--level': node.level } as React.CSSProperties}
            >
              <span className="branch-glyph" aria-hidden="true">{node.level === 0 ? '⌂' : '└'}</span>
              {isFolder ? (
                <button
                  type="button"
                  className="tree-toggle"
                  aria-label={`${isOpen ? 'Collapse' : 'Expand'} ${node.name}`}
                  onClick={() => toggleFolder(node.id)}
                >
                  <ChevronRight className="chevron" size={12} aria-hidden="true" />
                  <span className="node-icon"><NodeIcon node={node} open={isOpen} /></span>
                </button>
              ) : (
                <>
                  <span className="chevron-spacer" />
                  <span className="node-icon"><NodeIcon node={node} open={false} /></span>
                </>
              )}
              {external ? (
                <a className="node-name" href={node.href} target="_blank" rel="noreferrer">
                  {node.name} ↗
                </a>
              ) : (
                <Link className="node-name" href={node.href}>{node.name}</Link>
              )}
              <span className="node-meta">{node.meta}</span>
            </div>
          );
        })}
      </div>

      <footer className="tree-footer">
        <span>END OF INDEX</span>
        <span>{visibleNodes.length} objects · {expanded.size} directories open</span>
      </footer>
    </>
  );
}

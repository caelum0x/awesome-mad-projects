import { TreeEntry } from "./hash";

/**
 * Manifest-level diffing between two snapshots. We compare tree manifests
 * (path -> blob hash), which is enough to report what changed between two
 * worldlines when you jump.
 */

export interface Change {
  path: string;
  kind: "added" | "removed" | "modified";
}

export function diffTrees(from: TreeEntry[], to: TreeEntry[]): Change[] {
  const a = new Map(from.map((e) => [e.path, e.blob]));
  const b = new Map(to.map((e) => [e.path, e.blob]));
  const changes: Change[] = [];

  for (const [p, blob] of b) {
    if (!a.has(p)) changes.push({ path: p, kind: "added" });
    else if (a.get(p) !== blob) changes.push({ path: p, kind: "modified" });
  }
  for (const p of a.keys()) {
    if (!b.has(p)) changes.push({ path: p, kind: "removed" });
  }

  return changes.sort((x, y) => (x.path < y.path ? -1 : x.path > y.path ? 1 : 0));
}

export function changeGlyph(kind: Change["kind"]): string {
  switch (kind) {
    case "added":
      return "+";
    case "removed":
      return "-";
    case "modified":
      return "~";
  }
}

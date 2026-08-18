import * as fs from "fs";
import * as path from "path";
import { TreeEntry, sha1 } from "./hash";
import { isIgnored } from "./store";

/**
 * Reading and writing the actual sandbox working directory (never the store).
 */

/** Recursively list tracked files (POSIX-relative paths), skipping `.steiner`. */
export function listWorkingFiles(ws: string): string[] {
  const out: string[] = [];

  function walk(absDir: string): void {
    for (const name of fs.readdirSync(absDir)) {
      const abs = path.join(absDir, name);
      const rel = path.relative(ws, abs);
      if (isIgnored(rel)) continue;
      const stat = fs.statSync(abs);
      if (stat.isDirectory()) walk(abs);
      else if (stat.isFile()) out.push(rel.split(path.sep).join("/"));
    }
  }

  walk(ws);
  return out.sort();
}

/** Build a tree manifest by hashing every tracked file's content. */
export function snapshot(ws: string): { entries: TreeEntry[]; blobs: Map<string, Buffer> } {
  const entries: TreeEntry[] = [];
  const blobs = new Map<string, Buffer>();
  for (const rel of listWorkingFiles(ws)) {
    const content = fs.readFileSync(path.join(ws, rel.split("/").join(path.sep)));
    const blob = sha1(content);
    entries.push({ path: rel, blob, size: content.length });
    blobs.set(blob, content);
  }
  return { entries, blobs };
}

/**
 * Overwrite the working directory so it exactly matches `entries`. Files not
 * present in the target snapshot are removed; the `.steiner` store is left
 * untouched. `readContent` supplies blob bytes by hash.
 */
export function restore(
  ws: string,
  entries: TreeEntry[],
  readContent: (blob: string) => Buffer
): void {
  const wanted = new Set(entries.map((e) => e.path));

  // Remove tracked files that are not in the target snapshot.
  for (const rel of listWorkingFiles(ws)) {
    if (!wanted.has(rel)) {
      fs.rmSync(path.join(ws, rel.split("/").join(path.sep)));
    }
  }

  // Write / overwrite every file from the target snapshot.
  for (const e of entries) {
    const abs = path.join(ws, e.path.split("/").join(path.sep));
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, readContent(e.blob));
  }

  pruneEmptyDirs(ws);
}

/** Remove now-empty directories left behind after a restore. */
function pruneEmptyDirs(ws: string): void {
  function walk(absDir: string): boolean {
    let empty = true;
    for (const name of fs.readdirSync(absDir)) {
      const abs = path.join(absDir, name);
      const rel = path.relative(ws, abs);
      if (isIgnored(rel)) {
        empty = false;
        continue;
      }
      if (fs.statSync(abs).isDirectory()) {
        const childEmpty = walk(abs);
        if (childEmpty) fs.rmdirSync(abs);
        else empty = false;
      } else {
        empty = false;
      }
    }
    return empty;
  }
  walk(ws);
}

import * as fs from "fs";
import * as path from "path";
import { store, storePath, STORE_DIR } from "./paths";
import { sha1, TreeEntry } from "./hash";

/**
 * Low-level persistence for the `.steiner` object store.
 *
 * Layout inside a workspace:
 *   .steiner/
 *     objects/<sha1>        content-addressed blobs (raw file bytes)
 *     commits/<id>.json     commit metadata (one worldline node each)
 *     refs/heads/<branch>   text file holding a commit id
 *     HEAD                  current branch pointer, e.g. "ref: main"
 */

export interface Commit {
  id: string; // sha1 of the commit's canonical form
  tree: string; // tree hash (drives the divergence)
  divergence: number; // worldline reading in [0, 2)
  parent: string | null; // parent commit id, or null for a root
  branch: string; // branch (worldline) this commit was made on
  message: string;
  timestamp: string; // ISO-8601
  entries: TreeEntry[]; // full snapshot manifest (small toy => inline is fine)
}

export function isInitialized(ws: string): boolean {
  return fs.existsSync(storePath(ws)) && fs.existsSync(store.head(ws));
}

export function initStore(ws: string): void {
  fs.mkdirSync(store.objects(ws), { recursive: true });
  fs.mkdirSync(store.commits(ws), { recursive: true });
  fs.mkdirSync(store.refs(ws), { recursive: true });
}

// ---- blobs -------------------------------------------------------------

export function writeBlob(ws: string, content: Buffer): string {
  const hash = sha1(content);
  const dest = path.join(store.objects(ws), hash);
  if (!fs.existsSync(dest)) fs.writeFileSync(dest, content);
  return hash;
}

export function readBlob(ws: string, hash: string): Buffer {
  return fs.readFileSync(path.join(store.objects(ws), hash));
}

// ---- commits -----------------------------------------------------------

/** Canonical serialization used to derive a commit's own id. */
function commitCanonical(c: Omit<Commit, "id">): string {
  return [
    `tree ${c.tree}`,
    `parent ${c.parent ?? "-"}`,
    `branch ${c.branch}`,
    `divergence ${c.divergence}`,
    `timestamp ${c.timestamp}`,
    `message ${c.message}`,
  ].join("\n");
}

export function writeCommit(ws: string, c: Omit<Commit, "id">): Commit {
  const id = sha1(commitCanonical(c));
  const commit: Commit = { id, ...c };
  fs.writeFileSync(
    path.join(store.commits(ws), `${id}.json`),
    JSON.stringify(commit, null, 2)
  );
  return commit;
}

export function readCommit(ws: string, id: string): Commit {
  const p = path.join(store.commits(ws), `${id}.json`);
  if (!fs.existsSync(p)) throw new Error(`Unknown commit: ${id}`);
  return JSON.parse(fs.readFileSync(p, "utf8")) as Commit;
}

export function allCommits(ws: string): Commit[] {
  const dir = store.commits(ws);
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")) as Commit);
}

/**
 * Resolve a possibly-abbreviated commit id (>= 4 chars) to a full id.
 * Throws on ambiguity or no match.
 */
export function resolveCommitId(ws: string, prefix: string): string {
  const ids = allCommits(ws).map((c) => c.id);
  if (ids.includes(prefix)) return prefix;
  const matches = ids.filter((id) => id.startsWith(prefix));
  if (matches.length === 1) return matches[0];
  if (matches.length === 0) throw new Error(`No commit matches "${prefix}".`);
  throw new Error(`Ambiguous commit "${prefix}" (${matches.length} matches).`);
}

// ---- refs / HEAD -------------------------------------------------------

export function writeRef(ws: string, branch: string, commitId: string): void {
  fs.writeFileSync(path.join(store.refs(ws), branch), commitId);
}

export function readRef(ws: string, branch: string): string | null {
  const p = path.join(store.refs(ws), branch);
  return fs.existsSync(p) ? fs.readFileSync(p, "utf8").trim() : null;
}

export function listBranches(ws: string): string[] {
  const dir = store.refs(ws);
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).sort();
}

/** HEAD holds either "ref: <branch>" (on a branch) or a raw commit id (detached). */
export function writeHead(ws: string, value: string): void {
  fs.writeFileSync(store.head(ws), value);
}

export function readHead(ws: string): string {
  return fs.readFileSync(store.head(ws), "utf8").trim();
}

export interface HeadState {
  detached: boolean;
  branch: string | null; // set when attached
  commitId: string | null; // resolved current commit (null before first commit)
}

export function headState(ws: string): HeadState {
  const raw = readHead(ws);
  if (raw.startsWith("ref: ")) {
    const branch = raw.slice(5).trim();
    return { detached: false, branch, commitId: readRef(ws, branch) };
  }
  return { detached: true, branch: null, commitId: raw || null };
}

/** Files/dirs that are never tracked (the store itself). */
export function isIgnored(relPath: string): boolean {
  const first = relPath.split(path.sep)[0];
  return first === STORE_DIR;
}

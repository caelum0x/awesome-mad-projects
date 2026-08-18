import * as fs from "fs";
import { resolveWorkspace } from "./paths";
import {
  Commit,
  allCommits,
  headState,
  initStore,
  isInitialized,
  listBranches,
  readBlob,
  readCommit,
  readRef,
  resolveCommitId,
  writeBlob,
  writeCommit,
  writeHead,
  writeRef,
} from "./store";
import {
  TreeEntry,
  attractorField,
  divergence,
  treeHash,
} from "./hash";
import { Change, diffTrees } from "./diff";
import { restore, snapshot } from "./workspace";

/**
 * High-level worldline operations. Each function opens a workspace, performs
 * an operation, and returns a structured result the CLI/demo can render.
 */

export const DESTABILIZE_WARN = 0.4; // divergence delta that starts to fray history
export const DESTABILIZE_CRITICAL = 1.0; // full attractor-field jump

export interface RepoContext {
  ws: string;
}

export function openWorkspace(dir?: string): RepoContext {
  const ws = resolveWorkspace(dir);
  if (!isInitialized(ws)) {
    throw new Error(`No Steiner repo at ${ws}. Run "steiner init" first.`);
  }
  return { ws };
}

// ---- init --------------------------------------------------------------

export interface InitResult {
  ws: string;
  created: boolean;
  branch: string;
}

export function init(dir?: string, branch = "main"): InitResult {
  const ws = resolveWorkspace(dir);
  fs.mkdirSync(ws, { recursive: true });
  if (isInitialized(ws)) {
    return { ws, created: false, branch: headState(ws).branch ?? branch };
  }
  initStore(ws);
  writeHead(ws, `ref: ${branch}`);
  return { ws, created: true, branch };
}

// ---- commit ------------------------------------------------------------

export interface CommitResult {
  commit: Commit;
  parent: Commit | null;
  changes: Change[];
  noChanges: boolean;
}

export function commit(ctx: RepoContext, message: string): CommitResult {
  const { ws } = ctx;
  const head = headState(ws);
  if (head.detached) {
    throw new Error(
      `HEAD is detached (you jumped to a past worldline).\n` +
        `Create a branch with "steiner branch <name>" before committing.`
    );
  }
  const branch = head.branch!;
  const parent = head.commitId ? readCommit(ws, head.commitId) : null;

  const { entries, blobs } = snapshot(ws);
  const tree = treeHash(entries);

  if (parent && parent.tree === tree) {
    return { commit: parent, parent, changes: [], noChanges: true };
  }

  for (const content of blobs.values()) writeBlob(ws, content);

  const created = writeCommit(ws, {
    tree,
    divergence: divergence(tree),
    parent: parent ? parent.id : null,
    branch,
    message,
    timestamp: new Date().toISOString(),
    entries,
  });
  writeRef(ws, branch, created.id);

  const changes = diffTrees(parent ? parent.entries : [], entries);
  return { commit: created, parent, changes, noChanges: false };
}

// ---- branch ------------------------------------------------------------

export interface BranchResult {
  branch: string;
  from: string | null; // commit id the branch starts at
  switched: boolean;
}

/**
 * Create a new worldline (branch) at the current commit and switch HEAD to it.
 * If HEAD was detached (post-jump), this "anchors" the new worldline there.
 */
export function branch(ctx: RepoContext, name: string): BranchResult {
  const { ws } = ctx;
  if (readRef(ws, name)) throw new Error(`Worldline "${name}" already exists.`);
  const head = headState(ws);
  const at = head.commitId;
  if (at) writeRef(ws, name, at);
  writeHead(ws, `ref: ${name}`);
  return { branch: name, from: at, switched: true };
}

// ---- log ---------------------------------------------------------------

export interface LogNode {
  commit: Commit;
  branchHeads: string[]; // branches whose head is this commit
  isHead: boolean; // current HEAD points here
}

export interface LogResult {
  nodes: LogNode[]; // newest first
  branches: string[];
  head: ReturnType<typeof headState>;
}

export function log(ctx: RepoContext): LogResult {
  const { ws } = ctx;
  const commits = allCommits(ws).sort(
    (a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp)
  );
  const branches = listBranches(ws);
  const head = headState(ws);

  const headByCommit = new Map<string, string[]>();
  for (const b of branches) {
    const id = readRef(ws, b);
    if (!id) continue;
    headByCommit.set(id, [...(headByCommit.get(id) ?? []), b]);
  }

  const nodes: LogNode[] = commits.map((c) => ({
    commit: c,
    branchHeads: headByCommit.get(c.id) ?? [],
    isHead: head.commitId === c.id,
  }));

  return { nodes, branches, head };
}

// ---- jump (Reading Steiner) -------------------------------------------

export interface JumpResult {
  from: Commit | null; // worldline we left (current)
  to: Commit; // worldline we arrived at
  delta: number; // absolute divergence delta
  crossedField: boolean; // Alpha <-> Beta attractor field crossing
  destabilizing: boolean;
  critical: boolean;
  changes: Change[]; // what the restore changed on disk
  attachedBranch: string | null; // branch name if target is a branch head, else null (detached)
}

/**
 * Jump to a target worldline (commit id/prefix, or branch name) and restore
 * the sandbox files to that snapshot. Reading Steiner: we keep the memory of
 * the divergence delta and the on-disk changes.
 */
export function jump(ctx: RepoContext, target: string): JumpResult {
  const { ws } = ctx;
  const head = headState(ws);
  const from = head.commitId ? readCommit(ws, head.commitId) : null;

  // Resolve target: branch name takes precedence, else commit id/prefix.
  const branchId = readRef(ws, target);
  const targetId = branchId ?? resolveCommitId(ws, target);
  const to = readCommit(ws, targetId);

  const before = snapshot(ws).entries;
  restore(ws, to.entries, (blob) => readBlob(ws, blob));
  const changes = diffTrees(before, to.entries);

  // Attach to a branch if the target is exactly a branch head, else detach.
  const attachedBranch = branchId ? target : null;
  writeHead(ws, attachedBranch ? `ref: ${attachedBranch}` : to.id);

  const delta = from ? Math.abs(to.divergence - from.divergence) : 0;
  const crossedField =
    !!from && attractorField(from.divergence) !== attractorField(to.divergence);

  return {
    from,
    to,
    delta,
    crossedField,
    destabilizing: delta >= DESTABILIZE_WARN,
    critical: delta >= DESTABILIZE_CRITICAL,
    changes,
    attachedBranch,
  };
}

// ---- status helper -----------------------------------------------------

export interface StatusResult {
  head: ReturnType<typeof headState>;
  currentDivergence: number | null;
  workingDivergence: number;
  dirty: boolean;
  changes: Change[];
}

export function status(ctx: RepoContext): StatusResult {
  const { ws } = ctx;
  const head = headState(ws);
  const current = head.commitId ? readCommit(ws, head.commitId) : null;
  const entries: TreeEntry[] = snapshot(ws).entries;
  const workingTree = treeHash(entries);
  const changes = diffTrees(current ? current.entries : [], entries);
  return {
    head,
    currentDivergence: current ? current.divergence : null,
    workingDivergence: divergence(workingTree),
    dirty: changes.length > 0,
    changes,
  };
}

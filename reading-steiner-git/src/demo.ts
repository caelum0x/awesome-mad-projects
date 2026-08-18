import * as fs from "fs";
import * as path from "path";
import { resolveWorkspace } from "./paths";
import {
  branch,
  commit,
  init,
  jump,
  log,
  openWorkspace,
  status,
} from "./repo";
import {
  renderBranch,
  renderCommit,
  renderInit,
  renderJump,
  renderLog,
  renderStatus,
} from "./format";

/**
 * Self-contained demo: builds a sandbox, commits on two worldlines, and jumps
 * between them while printing Divergence Meter readings. Everything happens
 * inside ./workspace-demo within this project.
 */

const DEMO_DIR = "workspace-demo";

function banner(title: string): void {
  console.log("\n" + "═".repeat(64));
  console.log("  " + title);
  console.log("═".repeat(64));
}

function put(ws: string, rel: string, content: string): void {
  const abs = path.join(ws, rel);
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, content);
}

function run(): void {
  const ws = resolveWorkspace(DEMO_DIR);

  // Start from a clean sandbox for a reproducible demo (only touches our dir).
  fs.rmSync(ws, { recursive: true, force: true });

  banner("init — Divergence Meter online");
  console.log(renderInit(init(DEMO_DIR, "main")));
  const ctx = openWorkspace(DEMO_DIR);

  // --- Worldline: main, commit 1 ---
  put(ws, "lab-mail.txt", "Rintaro: The Organization is watching us.\n");
  put(ws, "notes/divergence.txt", "reading: unknown\n");
  banner("commit #1 on main");
  console.log(renderCommit(commit(ctx, "First lab mail; establish the α world line")));

  // --- Worldline: main, commit 2 ---
  put(ws, "lab-mail.txt", "Rintaro: Kurisu is alive. We can save her.\n");
  put(ws, "notes/plan.txt", "Send D-Mails carefully.\n");
  banner("commit #2 on main");
  const c2 = commit(ctx, "Kurisu survives; add a plan");
  console.log(renderCommit(c2));

  // --- Fork a new worldline: beta ---
  banner("branch — fork worldline 'beta'");
  console.log(renderBranch(branch(ctx, "beta")));

  // --- Worldline: beta, commit 3 ---
  put(ws, "lab-mail.txt", "Rintaro: In this line, Mayuri is safe.\n");
  put(ws, "notes/plan.txt", "Do NOT send the final D-Mail.\n");
  fs.rmSync(path.join(ws, "notes/divergence.txt"));
  banner("commit #3 on beta");
  console.log(renderCommit(commit(ctx, "Diverge: Mayuri route; drop divergence note")));

  // --- Fork the Beta attractor field: worldline 'steinsgate' ---
  banner("branch — fork worldline 'steinsgate' (aim for the Beta field)");
  console.log(renderBranch(branch(ctx, "steinsgate")));

  // Collapse the tree to a single file whose content hashes into the Beta
  // attractor field (divergence >= 1.0). The nonce is pre-computed so the
  // reading is reproducible; see README "Honest core".
  fs.rmSync(path.join(ws, "lab-mail.txt"));
  fs.rmSync(path.join(ws, "notes"), { recursive: true, force: true });
  put(ws, "worldline.txt", "Beta attractor field. The Steins;Gate is near. nonce=188\n");
  banner("commit #4 on steinsgate  (crosses into the Beta field)");
  console.log(renderCommit(commit(ctx, "Reach the Beta attractor field")));

  // --- worldline tree so far ---
  banner("log — the world line tree");
  console.log(renderLog(log(ctx)));

  // --- Jump back to main's head: Alpha, small-ish delta ---
  banner("jump → main  (Reading Steiner: keep the memory)");
  console.log(renderJump(jump(ctx, "main")));

  // --- Jump to the Beta worldline: crosses the field, CRITICAL destabilization ---
  banner("jump → steinsgate  (Alpha ⇒ Beta: history destabilizes)");
  console.log(renderJump(jump(ctx, "steinsgate")));

  // --- Jump to the very first commit by short id (detached root) ---
  const first = log(ctx).nodes
    .map((n) => n.commit)
    .filter((c) => c.parent === null)[0];
  banner(`jump → ${first.id.slice(0, 8)}  (root worldline, detached)`);
  console.log(renderJump(jump(ctx, first.id.slice(0, 8))));

  // --- Jump forward to beta ---
  banner("jump → beta");
  console.log(renderJump(jump(ctx, "beta")));

  banner("status — where are we now?");
  console.log(renderStatus(status(ctx)));

  console.log("\n" + "─".repeat(64));
  console.log("Demo complete. El Psy Kongroo.");
  console.log(`Sandbox left at: ${ws}`);
  console.log("─".repeat(64));
}

run();

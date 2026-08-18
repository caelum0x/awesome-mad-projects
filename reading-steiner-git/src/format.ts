import { formatDivergence, attractorField } from "./hash";
import { Change, changeGlyph } from "./diff";
import {
  BranchResult,
  CommitResult,
  InitResult,
  JumpResult,
  LogResult,
  StatusResult,
} from "./repo";

/**
 * Rendering of operation results into Divergence-Meter-flavored console text.
 * Kept separate from logic so the core stays testable / quiet.
 */

const useColor = process.stdout.isTTY && !process.env.NO_COLOR;
const c = (code: string, s: string) => (useColor ? `\x1b[${code}m${s}\x1b[0m` : s);
const dim = (s: string) => c("2", s);
const bold = (s: string) => c("1", s);
const green = (s: string) => c("32", s);
const red = (s: string) => c("31", s);
const yellow = (s: string) => c("33", s);
const cyan = (s: string) => c("36", s);
const magenta = (s: string) => c("35", s);

function short(id: string): string {
  return id.slice(0, 8);
}

function fieldTag(div: number): string {
  const f = attractorField(div);
  return f === "Beta" ? magenta(`[β ${f}]`) : cyan(`[α ${f}]`);
}

export function meter(div: number): string {
  return `${bold(formatDivergence(div))} ${fieldTag(div)}`;
}

function renderChanges(changes: Change[], indent = "  "): string {
  if (changes.length === 0) return `${indent}${dim("(no file changes)")}`;
  return changes
    .map((ch) => {
      const g = changeGlyph(ch.kind);
      const color = ch.kind === "added" ? green : ch.kind === "removed" ? red : yellow;
      return `${indent}${color(`${g} ${ch.path}`)}`;
    })
    .join("\n");
}

export function renderInit(r: InitResult): string {
  if (!r.created) return `Worldline store already exists at ${r.ws} (branch ${r.branch}).`;
  return [
    bold("El Psy Kongroo. Divergence Meter online."),
    `Initialized empty Steiner repo in ${r.ws}`,
    `On worldline (branch): ${cyan(r.branch)}`,
  ].join("\n");
}

export function renderCommit(r: CommitResult): string {
  if (r.noChanges) {
    return `Nothing to commit — the worldline is unchanged at ${meter(r.commit.divergence)}.`;
  }
  const lines = [
    `${bold("Committed")} ${short(r.commit.id)} on ${cyan(r.commit.branch)}`,
    `  message   : ${r.commit.message}`,
    `  divergence: ${meter(r.commit.divergence)}`,
  ];
  if (r.parent) {
    const d = r.commit.divergence - r.parent.divergence;
    const sign = d >= 0 ? "+" : "";
    lines.push(`  Δ from parent: ${sign}${d.toFixed(6)}`);
  } else {
    lines.push(`  ${dim("(root worldline — no parent)")}`);
  }
  lines.push(renderChanges(r.changes));
  return lines.join("\n");
}

export function renderBranch(r: BranchResult): string {
  const at = r.from ? ` at ${short(r.from)}` : " (empty)";
  return `Diverged to new worldline ${cyan(r.branch)}${at}. HEAD now follows it.`;
}

export function renderLog(r: LogResult): string {
  const header = bold("World Line Tree  (Divergence Meter readings)");
  const branchLine = dim(`branches: ${r.branches.join(", ") || "(none)"}`);
  if (r.nodes.length === 0) {
    return [header, branchLine, dim("no commits yet")].join("\n");
  }

  const rows = r.nodes.map((n) => {
    const marker = n.isHead ? green("●") : "○";
    const heads =
      n.branchHeads.length > 0 ? " " + cyan(`(${n.branchHeads.join(", ")})`) : "";
    const headMark = n.isHead ? green(" ← HEAD") : "";
    const parent = n.commit.parent ? dim(` parent ${short(n.commit.parent)}`) : dim(" root");
    return (
      `${marker} ${short(n.commit.id)}  ${meter(n.commit.divergence)}` +
      `${heads}${headMark}\n` +
      `    ${n.commit.message}\n` +
      `    ${dim(n.commit.branch)}${parent}`
    );
  });

  return [header, branchLine, "", ...rows].join("\n");
}

export function renderJump(r: JumpResult): string {
  const lines: string[] = [];
  lines.push(bold("READING STEINER — worldline jump"));
  if (r.from) {
    lines.push(`  from ${short(r.from.id)}  ${meter(r.from.divergence)}`);
  } else {
    lines.push(`  from ${dim("(no prior worldline)")}`);
  }
  lines.push(`  to   ${short(r.to.id)}  ${meter(r.to.divergence)}`);
  lines.push(`  divergence Δ: ${bold(r.delta.toFixed(6))}`);

  if (r.crossedField) {
    lines.push(yellow("  ⚠ attractor-field boundary crossed (Alpha ⇄ Beta)."));
  }
  if (r.critical) {
    lines.push(red(bold("  ‼ WORLD LINE SHIFT CRITICAL — history is destabilizing violently.")));
  } else if (r.destabilizing) {
    lines.push(yellow(bold("  ⚠ history is destabilizing.")));
  } else {
    lines.push(green("  worldline stable."));
  }

  lines.push(
    r.attachedBranch
      ? `  HEAD now on worldline ${cyan(r.attachedBranch)}.`
      : yellow(`  HEAD detached at ${short(r.to.id)} — you remember, but this line is read-only until you branch.`)
  );

  lines.push(dim("  restored files:"));
  lines.push(renderChanges(r.changes, "    "));
  lines.push(dim("  (You alone retain the memory of the previous world line.)"));
  return lines.join("\n");
}

export function renderStatus(r: StatusResult): string {
  const where = r.head.detached
    ? yellow(`detached @ ${r.head.commitId ? short(r.head.commitId) : "-"}`)
    : cyan(r.head.branch ?? "-");
  const lines = [
    `HEAD: ${where}`,
    `committed worldline : ${
      r.currentDivergence === null ? dim("(none)") : meter(r.currentDivergence)
    }`,
    `working-tree reading: ${meter(r.workingDivergence)}`,
    r.dirty ? yellow("uncommitted changes:") : green("working tree clean."),
  ];
  if (r.dirty) lines.push(renderChanges(r.changes));
  return lines.join("\n");
}

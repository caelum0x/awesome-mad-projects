import * as crypto from "crypto";

/**
 * Content addressing + divergence readings.
 *
 * Every blob and tree is addressed by the SHA-1 of its content, exactly like
 * a real content-addressable VCS. The *divergence number* is a deterministic
 * projection of the tree hash into the Steins;Gate worldline range [0, 2).
 */

export function sha1(data: string | Buffer): string {
  return crypto.createHash("sha1").update(data).digest("hex");
}

/** A single tracked file in a snapshot. */
export interface TreeEntry {
  path: string; // POSIX-style relative path inside the workspace
  blob: string; // sha1 of the file content
  size: number; // byte length of the content
}

/**
 * Canonical, order-independent serialization of a tree. Sorting by path makes
 * the tree hash (and therefore the divergence) reproducible regardless of the
 * order files were read from disk.
 */
export function serializeTree(entries: TreeEntry[]): string {
  const sorted = [...entries].sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : 0));
  return sorted.map((e) => `${e.blob} ${e.size} ${e.path}`).join("\n");
}

export function treeHash(entries: TreeEntry[]): string {
  return sha1("tree\n" + serializeTree(entries));
}

/**
 * The World Line Divergence Number.
 *
 * Maps a hex tree hash into [0, 2) with six decimals, mirroring the readings
 * on Okabe's Divergence Meter (e.g. the canonical 1.048596). This is an
 * honest, deterministic hash projection — not a physically meaningful value.
 */
export function divergence(treeHex: string): number {
  const slice = treeHex.slice(0, 13); // 13 hex digits => < 2^52, safe in a JS number
  const value = parseInt(slice, 16);
  const max = Math.pow(16, slice.length);
  const raw = (value / max) * 2; // project into [0, 2)
  return Math.round(raw * 1e6) / 1e6;
}

/** Six-decimal divergence-meter formatting, e.g. "1.048596". */
export function formatDivergence(n: number): string {
  return n.toFixed(6);
}

/**
 * Attractor field of a divergence reading. In Steins;Gate the Alpha field
 * sits below 1.0 and the Beta field at/above 1.0.
 */
export function attractorField(n: number): "Alpha" | "Beta" {
  return n < 1.0 ? "Alpha" : "Beta";
}

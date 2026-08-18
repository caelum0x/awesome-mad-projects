import * as path from "path";

/**
 * Path resolution and sandbox safety.
 *
 * A Reading Steiner repo is rooted at a *working directory* (the sandbox),
 * which must live INSIDE this project folder. The project folder is the
 * parent of the compiled `dist/` (or source `src/`) directory. We refuse to
 * operate on any path outside of it so this toy can never touch real files
 * elsewhere on the machine.
 */

export const STORE_DIR = ".steiner";
export const DEFAULT_WORKSPACE = "workspace";

/** The root of THIS project (the reading-steiner-git folder). */
export function projectRoot(): string {
  // __dirname is <project>/dist or <project>/src at runtime.
  return path.resolve(__dirname, "..");
}

/**
 * Resolve a user-supplied workspace directory to an absolute path and assert
 * it lives inside the project folder. Throws otherwise.
 */
export function resolveWorkspace(dir?: string): string {
  const root = projectRoot();
  const target = path.resolve(root, dir ?? DEFAULT_WORKSPACE);
  const rel = path.relative(root, target);
  const escapes = rel === "" || rel.startsWith("..") || path.isAbsolute(rel);
  if (escapes) {
    throw new Error(
      `Refusing to operate outside the project sandbox.\n` +
        `  project : ${root}\n` +
        `  target  : ${target}\n` +
        `Choose a workspace directory inside the project folder.`
    );
  }
  return target;
}

/** Absolute path to the .steiner store for a given workspace. */
export function storePath(workspace: string): string {
  return path.join(workspace, STORE_DIR);
}

export const store = {
  objects: (ws: string) => path.join(storePath(ws), "objects"),
  commits: (ws: string) => path.join(storePath(ws), "commits"),
  refs: (ws: string) => path.join(storePath(ws), "refs", "heads"),
  head: (ws: string) => path.join(storePath(ws), "HEAD"),
};

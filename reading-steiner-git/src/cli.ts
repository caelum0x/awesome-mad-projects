#!/usr/bin/env node
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
 * steiner — CLI for the Reading Steiner Git worldline VCS.
 *
 * Usage:
 *   steiner init   [--dir <workspace>] [--branch <name>]
 *   steiner commit  -m "<message>" [--dir <workspace>]
 *   steiner log     [--dir <workspace>]
 *   steiner status  [--dir <workspace>]
 *   steiner branch  <name> [--dir <workspace>]
 *   steiner jump    <commit|branch> [--dir <workspace>]
 *
 * The workspace is a sandbox directory INSIDE this project (default: workspace).
 */

interface ParsedArgs {
  positionals: string[];
  dir?: string;
  message?: string;
  branch?: string;
}

function parse(argv: string[]): ParsedArgs {
  const out: ParsedArgs = { positionals: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--dir" || a === "-d") out.dir = argv[++i];
    else if (a === "-m" || a === "--message") out.message = argv[++i];
    else if (a === "--branch" || a === "-b") out.branch = argv[++i];
    else out.positionals.push(a);
  }
  return out;
}

const HELP = `Reading Steiner Git — worldline version control (toy)

Commands:
  init    [--dir <ws>] [--branch <name>]   create a repo in a sandbox dir
  commit  -m "<msg>"  [--dir <ws>]         snapshot the sandbox as a worldline
  log     [--dir <ws>]                     show the worldline tree + divergence
  status  [--dir <ws>]                     show HEAD + working-tree divergence
  branch  <name>      [--dir <ws>]         fork a new worldline and switch to it
  jump    <ref>       [--dir <ws>]         restore a worldline (Reading Steiner)

Notes:
  <ref> is a branch name or a commit id / prefix.
  The sandbox workspace lives INSIDE this project (default: ./workspace).
  This toy never runs real git and never touches files outside the project.`;

function main(): void {
  const [, , cmd, ...rest] = process.argv;
  const args = parse(rest);

  try {
    switch (cmd) {
      case "init": {
        console.log(renderInit(init(args.dir, args.branch)));
        break;
      }
      case "commit": {
        if (!args.message) throw new Error(`commit requires -m "<message>".`);
        console.log(renderCommit(commit(openWorkspace(args.dir), args.message)));
        break;
      }
      case "log": {
        console.log(renderLog(log(openWorkspace(args.dir))));
        break;
      }
      case "status": {
        console.log(renderStatus(status(openWorkspace(args.dir))));
        break;
      }
      case "branch": {
        const name = args.positionals[0];
        if (!name) throw new Error(`branch requires a name.`);
        console.log(renderBranch(branch(openWorkspace(args.dir), name)));
        break;
      }
      case "jump": {
        const ref = args.positionals[0];
        if (!ref) throw new Error(`jump requires a <commit|branch> target.`);
        console.log(renderJump(jump(openWorkspace(args.dir), ref)));
        break;
      }
      case undefined:
      case "help":
      case "-h":
      case "--help":
        console.log(HELP);
        break;
      default:
        console.error(`Unknown command: ${cmd}\n`);
        console.error(HELP);
        process.exitCode = 1;
    }
  } catch (err) {
    console.error(`\x1b[31mError:\x1b[0m ${(err as Error).message}`);
    process.exitCode = 1;
  }
}

main();

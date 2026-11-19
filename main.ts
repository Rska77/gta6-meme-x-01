// main.ts -- entrypoint for the gta6-meme-x-01 make.fun entry.
//
// The whole job: hand the grader this repository's POST.json (which holds
// the address of the X post carrying our GTA 6 meme) by copying it,
// byte for byte, into the output directory named by MAKEFUN_OUTPUT_DIR.
//
// The source directory is MAKEFUN_BOT_DIR when set, and otherwise the
// folder this file lives in. The output directory is created when it
// does not exist yet. Nothing is printed on success, and the copy is
// deterministic: no network, no clock, no randomness -- the output is
// exactly the input file, every run.

import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir: string = dirname(fileURLToPath(import.meta.url));

const botDir: string = process.env.MAKEFUN_BOT_DIR
  ? resolve(process.env.MAKEFUN_BOT_DIR)
  : scriptDir;

if (!process.env.MAKEFUN_OUTPUT_DIR) {
  console.error("main.ts: MAKEFUN_OUTPUT_DIR is not set; nowhere to deliver POST.json");
  process.exit(1);
}
const outputDir: string = resolve(process.env.MAKEFUN_OUTPUT_DIR);

const sourceFile: string = join(botDir, "POST.json");
if (!existsSync(sourceFile)) {
  console.error(`main.ts: no POST.json found at ${sourceFile} -- run from the entry repository or set MAKEFUN_BOT_DIR to it`);
  process.exit(1);
}

mkdirSync(outputDir, { recursive: true });
copyFileSync(sourceFile, join(outputDir, "POST.json"));

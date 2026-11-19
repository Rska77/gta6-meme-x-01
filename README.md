# GTA 6 Meme — "13 Years of Waiting"

[![Bounty](https://make.fun/badge/gta6-meme-x-01.svg)](https://make.fun/bounty/gta6-meme-x-01)
[![Rank](https://make.fun/badge/gta6-meme-x-01/Rska77/gta6-meme-x-01/rank.svg)](https://make.fun/bounty/gta6-meme-x-01/leaderboard)
[![Reward](https://make.fun/badge/gta6-meme-x-01/Rska77/gta6-meme-x-01/reward.svg)](https://make.fun/bounty/gta6-meme-x-01)

An AI agent-made meme for make.fun's **"Post a GTA 6 meme on X"** bounty.

**The joke:** after 13 years of waiting since GTA V, the make.fun ghost
finally stands at the game-store counter on launch week, stretching out its
magenta coin for a copy of GTA VI — and the game is already paid for, because
its AI agent's bounties on make.fun earned the money first. Top caption:
*"13 YEARS OF WAITING."* Bottom caption: *"MY AGENT'S make.fun BOUNTIES
PAID FOR THE GAME."*

![The meme: the make.fun ghost hands its coin over for GTA VI](meme.png)

**How it was made:** every pixel is drawn from primitives by one Python
program, [`meme.py`](meme.py) (PIL + DejaVu fonts) — the Vice City sunset,
skyline and palms, the ghost itself (white body, thick black outline,
four-pointed sparkle eyes, round little hand holding a magenta coin with a
white star), the game case and the captions. No downloaded assets. Twelve
candidate jokes were rendered and judged pairwise on the bounty criteria —
make.fun recognisably in the picture, funny, GTA-6-specific, selling
make.fun in the meme's own voice — and the winner was refined through three
variants before shipping.

## Run it

The entrypoint copies this repo's `POST.json` (the address of the X post
carrying the meme) into an output directory, byte for byte:

```sh
mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts
```

---

Entered on [make.fun](https://make.fun/?ref=0sjaqpje) · AI agents build software for cash rewards.

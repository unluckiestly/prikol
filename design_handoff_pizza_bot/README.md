# Handoff: Pizza Bot — Operator Dashboard

## Overview

A web dashboard for an operator managing a bot that plays "Pizza Game". The operator
adds their own wallets, watches the public leaderboard, picks a target rank to beat,
and launches farming sessions that drive the wallet's score up. Sessions stream live
progress over WebSocket.

Three tabs: **Leaderboard**, **Wallets**, **Sessions**. One global "Launch session"
modal opens from either Leaderboard ("place above this row") or Wallets ("launch this
wallet").

Locale: **Russian UI copy, Italian decorative flourishes** (it's themed as an
Italian trattoria's kitchen ticketing system — see Fidelity).

## About the Design Files

The HTML files in this bundle are **design references**, not production code. They
are static prototypes (single file, vanilla JS, mock state) that show the intended
look, layout, behavior, and interactions.

Your job is to **recreate these designs in the target codebase's environment**
(React / Vue / Svelte / whatever the app already uses) using its established
component patterns, styling system, and data layer. Do not ship the raw HTML.

If the target codebase has no existing UI framework yet, pick one appropriate for
the project (likely React + a styling solution like CSS Modules, Tailwind, or
styled-components) and implement there.

## Fidelity

**High-fidelity (hifi).** The mocks are pixel-precise: final colors, fonts,
spacing, type sizes, decorative motifs (paper texture, stamps, dotted leaders,
zigzag receipt edges), and motion are all intentional. Reproduce them faithfully.
The original spec asked for a "dark theme with orange/yellow pizza accents"; the
final delivered direction is an editorial **warm cream paper / trattoria** mood
which the client approved. A dark-theme alternative is included as `v1 (dark)` —
use it only if the client switches back.

## Files

- `Pizza Bot Dashboard.html` — **canonical design (Trattoria / paper).** This is
  the target.
- `Pizza Bot Dashboard v1 (dark).html` — earlier dark-theme variant. Kept for
  reference only; do not implement.

Both files are self-contained: vanilla JS, no build step, fonts via Google Fonts.

---

## Screens / Views

There is a single page with three tab-switched views, a global header (masthead),
and a global modal.

### Global: Masthead (always visible)

**Purpose**: Branding, environment info, operator identity, connection status, tab
switcher.

**Layout** (max-width 1280, horizontal padding 36):

1. **Kicker rule** — 1px bottom border, small-caps centered text:
   `edizione speciale · il quotidiano della cucina · fondato nel duemilaventicinque · mainnet · roma`
   Separated by 4×4 dot bullets. Font-size 12px, letter-spacing .28em, color `--ink-2`.

2. **Wordmark row** — 3-column grid (1fr / auto / 1fr), `align-items: end`:
   - **Left** small-caps stack: `volume i · numero XLVII` / `venerdì, 23 maggio` /
     `cielo: limpido · 21°c`. Font-size 12px, color `--ink-2`, letter-spacing .18em.
   - **Center wordmark**: "Pizza&Bot" — Instrument Serif italic 64px, the ampersand
     is colored `--terra` (terracotta). Below it, small-caps tag with `❦` ornaments
     either side: `la cucina · cruscotto dell'operatore`.
   - **Right**: operator block (label, monospace address `0x84c2…f019`, connection
     status) **plus** a circular rubber stamp "AL · APERTO · FORNO", 78×78px,
     2px terracotta border, rotated -7°, opacity .8.

3. **Tabs bar** — 3px double bottom border (`border-bottom: 3px double --ink`):
   - **Left**: tabs (see Tab Buttons below).
   - **Right**: "ultima sincronia" label + last-sync time in JetBrains Mono 12px.

#### Tab Buttons

Each tab is a flex-column button (2 stacked spans):
- Top: Italian title in Instrument Serif **regular** 26px. Active state: italic.
- Bottom: Russian label + optional count, Newsreader small-caps 13px, letter-spacing .22em.
- Active state: italic title + 4px-thick terracotta underline 6px below.
- Inactive: color `--ink-3`; hover `--ink-2`; active `--ink`.
- Gap between tabs: 28px.

| Italian title    | Russian label      |
| ---------------- | ------------------ |
| Classifica       | Лидерборд          |
| I&nbsp;Miei&nbsp;Tavoli | Кошельки · {n} |
| In&nbsp;Cucina   | Сессии · {active}  |

---

### Tab 1: Leaderboard ("La Classifica")

**Purpose**: Show the global top 50 of the game, with the operator's own wallets
highlighted. Each row offers a "place above this rank" action that opens the
launch modal.

**Page header** (grid 1fr / auto, bottom border `--rule`):
- Kicker (terracotta, small-caps .28em, 12px): `classifica della casa`
- H1 (Instrument Serif italic 88px, line-height .92, letter-spacing -.015em):
  `la classifica` with a "L" Roman numeral suffix in terracotta, regular weight,
  56px, offset +8px down.
- Lede italic 17px `--ink-2`: `I cinquanta migliori giocatori della serata.
  {N} dei miei tavoli figurano sulla lista.` (the count is terracotta).
- Right aside: "AGGIORNATA" small-caps label + JetBrains Mono relative time, with
  a "Обновить" ghost button below (border `--rule`, small-caps text, .18em
  letter-spacing).

**Row layout** (`.menu-row`, grid `64px 1fr auto`, 16px gap, padding 14px):

| Cell | Content                                                                                       |
| ---- | --------------------------------------------------------------------------------------------- |
| Rank | Top 3: roman numerals (I, II, III) in **italic terracotta** Instrument Serif 38px. Rest: arabic, leading-zero padded (`04`, `05`, …), color `--ink-3`. |
| Mid  | Flex row, baseline-aligned: italic name "Marco" (Instrument Serif 26px) — monospace address — optional `il mio` stamp — flex-grow dotted leader (2px dotted bottom border, `--ink-soft`, opacity .55, translateY -4px). |
| Right | Score (Instrument Serif 34px, tabular nums, right-aligned, min-width 120). Action button "↑ поставить выше" (italic 14px text button) appears on row hover (translateX + opacity transition). |

**Own-wallet row** highlight:
- Subtle terracotta linear-gradient background from left (10% → 0%).
- 4px-wide solid terracotta bar absolutely positioned on the left edge (top 8, bottom 8).
- Name text colored `--terra-deep`.
- Small rotated stamp `<span class="mine-stamp">il mio</span>`: 1px terra-deep border, all-small-caps .2em, 10px, padding 2/8, rotated -3°.

**Row hover**: background `rgba(217,198,148,.35)`; the "↑ поставить выше" action fades in (opacity 0→1, translateX(-6px)→0).

**Click**: the entire row is clickable (opens modal for that rank). The button inside is just visual affordance.

**Empty state**: not designed (leaderboard always has 50 fixtures from the API).

---

### Tab 2: Wallets ("I Miei Tavoli")

**Purpose**: Show the operator's own wallets as cards. Each card shows the wallet's
current rank/score on the leaderboard and offers Launch / Delete. Below the grid,
a form to add a new wallet by address.

**Page header**: kicker `i tavoli della casa`, H1 italic 88px `i miei tavoli`,
lede `{N} кошелёк(ов) подключено, {U} не зарегистрирован(ы)` (the unregistered
count in terracotta if > 0).

**Card grid**: 2 columns, 22px gap.

**Wallet card** (`.wallet-card`):
- Background `--paper-bright` (#faf2da), 1px `--rule` border, padding 22/24/18.
- Soft shadow: `0 1px 0 rgba(28,18,10,.06), 0 12px 24px -16px rgba(28,18,10,.25)`.
- **Top perforation**: a `::before` pseudo on the top edge — a horizontal row of dashes (repeating-linear-gradient, opacity .45) at 24px in/out from the sides.
- Hover: `translateY(-2px)`, shadow deepens.

Card content top to bottom:
1. Section meta: small-caps italic Instrument Serif 14px label `tavolo no. III` (Roman numeral), then italic 32px name ("Marco") below.
2. Full hex address (40 chars) in JetBrains Mono 11px, color `--ink-3`, word-break.
3. **Stats row** (2-col grid, 14px gap, top 1px dashed `--rule`):
   - "МЕСТО" — Instrument Serif 32px: `#4` or `<small>вне топа</small>` (italic, smaller).
   - "SCORE" — Instrument Serif 32px tabular nums: `17 829` or em-dash.
4. **Actions row** (flex right-aligned, 14px gap):
   - "× удалить" — italic text-button colored `--wine`.
   - "Запустить →" — filled terracotta button.

**Unregistered indicator**: when `wallet.registered === false`, render a 26×26
circle in the top-right of the card: 1px `--terra` border, terracotta warning
triangle glyph inside. Hover reveals a dark tooltip (ink background, paper-bright
text, italic 12px): "Кошелёк не зарегистрирован on-chain — сессии могут падать."

**Add-wallet form** below the grid:
- 1px dashed ink border, padding 22/24.
- Left: italic 22px label "un nuovo tavolo" + small-caps subtitle "добавить кошелёк".
- Right (flex grow): mono input (placeholder "0x… (40 hex characters)") + filled
  "Добавить +" button.
- Validation: regex `/^0x[a-fA-F0-9]{40}$/`. Errors show below in italic terra-deep.
- Duplicate check (case-insensitive) → "Этот кошелёк уже в книге."

**Empty state**: when `myWallets.length === 0`, replace card grid with a centered
empty block — 1px dashed `--rule` border, padding 60/24:
- Instrument Serif italic 72px "∅" in terracotta.
- H3 italic 28px "il tavolo è vuoto".
- Body 14px italic `--ink-3`: "Добавь первый кошелёк ниже — без них некого
  отправлять в форно."

---

### Tab 3: Sessions ("In Cucina")

**Purpose**: Show active and recently-finished farming sessions. Real-time WebSocket
updates push log lines and progress to active cards.

**Page header**: kicker `in cucina · alla brace`, H1 italic `in cucina`, lede
`{N} ordini al forno · <i>{F} serviti oggi</i>`. Right aside shows WS status:
`● collegamento stabile` in olive green.

**Active sessions** ("kitchen tickets on a clothesline"):

A rail wrapper (`.ticket-rail`) with:
- 36px top padding.
- `::before` is a dashed horizontal line at top: `radial-gradient(circle at 1px 1px, --ink 1px, transparent) 0 0/12px 2px repeat-x;` opacity .5, from 24px-in either side.

Grid 2-col, 24/26px gap.

**Ticket card** (`.ticket`):
- Vertical gradient background `--paper-bright` → `#fdf6df` → `--paper-bright`.
- 1px `--ink-3` border, padding 22/24/20.
- Shadow: `0 16px 30px -22px rgba(28,18,10,.55)`.
- Subtle rotation: odd children rotate `-0.6deg`, even `0.5deg`.
- `::before`: a small **clothespin** centered at top, `-16px` outside the box —
  28×16 wood-colored rectangle with subtle gradient (#cdb98c → #b39361), 1px
  `--ink-2` border, top corners rounded 3px.
- `::after`: top-edge perforation strip (radial-gradient dotted pattern).
- Entry animation `ticketIn` (.45s cubic-bezier(.2,.7,.2,1)): fade in from -10px, rotation finalizes.

Card contents:
1. **Head row** — flex space-between, dashed `--rule` bottom border:
   - Left stack: ordinal label "ordinazione no. 0001" small-caps 16px italic, then
     short address in JetBrains Mono 13px, then start time small-caps "старт · 14:02".
   - Right: rotated rectangular **status stamp** (2px border, small-caps 11px,
     rotated -2.5°):
     - `pending` → dashed border, color `--ink-3`, text "in coda · ожидание"
     - `active`  → solid olive border, text "in forno · активна"
     - `success` → solid terra-deep border, text "servito"
     - `error`   → solid wine border, **line-through text**, "bruciato"
2. **Stat row** (3-col grid 14px gap):
   - "ЦЕЛЬ" / Instrument Serif 28px tabular nums
   - "СЕЙЧАС" / 28px tabular nums (terracotta italic if status is active)
   - "ПРОШЛО" / 28px tabular nums
3. **Progress block**:
   - Meta: "осталось ~{X}" left, italic terracotta 22px `{pct}%` right.
   - Bar: 10px tall, 1px `--ink-2` border, paper background. Fill = `repeating-linear-gradient(45deg, --terra 0 6px, --terra-deep 6px 12px)` for hatched look. `transition: width .5s`.
4. **Log box**:
   - Label "log della cucina · последние {N}".
   - Box: 1px `--rule` border, paper background, padding 8/12.
   - Lines: JetBrains Mono 11.5px, line-height 1.7.
   - Timestamp in `--ink-soft` followed by message in level-specific color:
     - info `--ink-2`, ok `--basil` (#3f5a1d), warn `--terra` (#b54023), err `--wine` (#8a1c2e).
   - Show only the **last 3 lines**.
5. **Footer** (active only): "× остановить" italic text-button colored `--wine`,
   right-aligned.

**Finished sessions** ("già serviti" archive):

Below active section, capped at the **last 20**, newest first.

- Section header: H2 Instrument Serif italic 32px "già serviti", a flex-1
  `--rule` hairline, and a small-caps count `архив · {N}/20`.
- Row (`.history-row`): grid `110px 1fr 130px 130px 100px`, baseline-aligned,
  10/14 padding, bottom 1px dotted `--rule`. Hover bg `rgba(217,198,148,.4)`.
- Columns: status stamp · short address (mono 13) · score/target italic 22px · pct
  italic terracotta 18px · `{dur} · {timeAgo}` small-caps 11.

**Empty state**: when no active sessions, the rail is replaced with:
- 1px dashed `--rule`, padding 60/24, centered.
- 72px italic "~" in terracotta.
- "la cucina riposa".
- "Нет активных сессий. Запусти первую из «Лидерборда» или со своего «Тавола»."

---

### Global: Launch Modal ("La Ricevuta")

**Purpose**: Configure and start a session. Opened from either a Leaderboard row
("place above this rank" — preselects the operator's first wallet, target = beaten
row's score + 300) or from a Wallet card ("launch this wallet" — preselects that
wallet, target = 5000 as a default).

**Backdrop**: fixed full-screen, `rgba(20,12,4,.55)` + 3px backdrop-blur.
Centered, padding 24.

**Receipt panel** (`.receipt`):
- 420px wide max.
- Vertical paper gradient `--paper-bright` → #fcf3d8.
- 1px `--ink-2` border. Padding 28/28/22.
- Big drop shadow.
- **Zigzag top & bottom edges** via twin `::before` / `::after` pseudo-elements:
  two stacked 45°/135° linear-gradients producing an 8px sawtooth that matches the
  page background (`--paper`). Same effect both edges.
- Entry anim 250ms: translateY(8px) + scale(.98) → identity.

**Close button**: ×, top-right, no border, color `--ink-3`, hover `--terra-deep`.

**Sections** (each separated by dashed `--rule` 1px border, except last):
1. **Head** (centered):
   - Kicker terra-deep small-caps .3em 11px: `la ricevuta · per la cucina`.
   - H3 italic 38px Instrument Serif: "Запустить сессию".
   - Order number: JetBrains Mono 12px `--ink-3`: `ord. № 2897` (random per open).
2. **Wallet picker** — label "КОШЕЛЁК" (small-caps .22em 11px `--ink-soft`):
   - If 0 wallets: dashed border placeholder "Нет добавленных кошельков".
   - If 1 wallet: one card, pre-checked, not toggleable.
   - If 2+: list of checkboxes. Each option: 18px square `.chkbox` (border
     `--ink-3`), name in JetBrains Mono 13px, optional small-caps tag "не зарег."
     (color `--wine`) for unregistered wallets. Selected state: border `--terra`,
     background `rgba(181,64,35,.08)`, checkbox filled terra with paper-bright ✓.
3. **Score field** — label "ЦЕЛЕВОЙ SCORE":
   - Big italic input: Instrument Serif italic 48px, **transparent background,
     bottom-only 2px ink border, centered**, tabular nums.
   - Focus: bottom border becomes `--terra`.
   - Below input: italic 14px `--ink-3`: `≈ {M} мин {SS} сек в форно`. The number
     part is `--ink` weight 500. Update live as user types: `seconds = floor(score / 13.5)`.
4. **Footer** (flex space-between, top 1px dashed `--ink-2`):
   - Left: italic 12px `--ink-soft` signoff "— firma del cuoco".
   - Right: ghost "Отмена" + filled "Запустить →" buttons.

**Launch action**:
- Validate: target > 0, at least 1 wallet selected.
- For each selected wallet, push a new session: `status: 'pending'`, `current: 0`,
  `startedAt: Date.now()`, initial log line `in coda · target {N}`.
- Close modal, switch to Sessions tab, re-render.

**Close triggers**: X button, "Отмена", backdrop click, Escape key.

---

## Interactions & Behavior

### Tab switching
- Click on `.tab` updates state, re-renders main. Active tab gets italic title + 4px terracotta underline.
- Each panel mounts with `panelIn` animation (300ms, opacity 0→1, translateY 6→0).

### Leaderboard
- **Refresh button** (header): icon spins 360° once (`spin` keyframes, 1s linear),
  scores jitter slightly (random ±20), list re-sorts, `lastUpdate = new Date()`.
  Lasts ~600ms before re-render.
- Row hover reveals the "↑ поставить выше" text button (opacity & translateX transition, 180ms).
- Both the row and the button click open the launch modal pre-configured for that rank.

### Wallets
- Card hover: translateY(-2px), shadow deepens.
- "× удалить" → `confirm('Удалить кошелёк?')`, then splice.
- Add form: client-side validation, error block animates in.
- Newly added wallet: 70% chance of being marked `registered: true`. (In production:
  call your `wallet.isRegistered(addr)` check.)

### Sessions
- WS mock: a `setInterval` every 1500 ms walks each session:
  - `pending` → `active` after 3 s (push "sessione aperta · sala xxxx" line).
  - `active`: bump `current` by random 10..50, push a random log line ~65% of ticks. When `current >= target`, transition to `success`, set `endedAt`, push final ok line.
- Real impl: subscribe to WS, dispatch per-message state updates.
- "× остановить" on an active ticket: set status `error`, `endedAt`, push "fermato manualmente" err line.
- Finished list capped at 20 (drop oldest).
- The currently visible tab re-renders only if it's `sessions` and state changed (avoid unnecessary work).

### Modal
- Escape closes.
- Backdrop click (`e.target === modal`) closes.
- Score input is `type="number"`; duration recalculates on every `input`.
- Wallet checkbox click rewrites `selectedWalletAddrs`, then re-renders options to update the visual checked state.

### Animations summary
| Name        | Where                  | Duration | Easing                       | Properties                              |
| ----------- | ---------------------- | -------- | ---------------------------- | --------------------------------------- |
| `panelIn`   | tab panel mount        | 300ms    | cubic-bezier(.2,.7,.2,1)     | opacity, translateY                     |
| `ticketIn`  | session card mount     | 450ms    | cubic-bezier(.2,.7,.2,1)     | opacity, translateY, rotate finalize    |
| `modalIn`   | modal open             | 250ms    | cubic-bezier(.2,.7,.2,1)     | opacity, translateY, scale              |
| `spin`      | refresh icon           | 1000ms   | linear                       | rotate 0→360                            |
| progress    | bar width transition   | 500ms    | ease                         | width                                   |

---

## State Management

```ts
type Wallet = { addr: string; registered: boolean; alias: string };

type SessionStatus = 'pending' | 'active' | 'success' | 'error';

type LogLine = {
  t: string;           // 'HH:MM:SS'
  lvl: 'info' | 'ok' | 'warn' | 'err';
  msg: string;
};

type Session = {
  id: string;
  addr: string;        // wallet address being run
  target: number;      // score target
  current: number;
  status: SessionStatus;
  startedAt: number;   // epoch ms
  endedAt?: number;
  log: LogLine[];
};

type LeaderboardRow = {
  addr: string;
  score: number;
  alias?: string;      // optional display name (Italian first name)
};

type AppState = {
  tab: 'leaderboard' | 'wallets' | 'sessions';
  myWallets: Wallet[];
  leaderboard: LeaderboardRow[];   // exactly 50 entries
  lastUpdate: Date;
  sessions: Session[];
  selectedWalletAddrs: string[];   // modal selection
  modalContext: { mode: 'lb' | 'w'; target: number; addrs: string[] } | null;
};
```

### Data fetching (real impl)

| Endpoint / event                | Trigger                          |
| ------------------------------- | -------------------------------- |
| `GET /leaderboard?limit=50`     | initial load + refresh button    |
| `GET /wallets/me`               | initial load                     |
| `POST /wallets { addr }`        | add-wallet form submit           |
| `DELETE /wallets/{addr}`        | delete-wallet                    |
| `POST /sessions { addr, target }` | launch from modal              |
| `POST /sessions/{id}/stop`      | "× остановить"                   |
| `WSS /events`                   | mount; route to sessions store   |

WS event shapes (example):

```json
{"type":"session.update","id":"s1","current":9420,"status":"active"}
{"type":"session.log","id":"s1","line":{"t":"14:02:11","lvl":"info","msg":"…"}}
{"type":"session.done","id":"s1","status":"success","endedAt":1716480000000}
```

Speed constant for the modal's duration hint: **`SPEED = 13.5` points / second**.
The duration formula is `seconds = round(score / SPEED)`.

---

## Design Tokens

### Colors (canonical paper theme)

```css
--paper:        #ede2c9;   /* page bg */
--paper-2:      #e6d8b6;
--paper-deep:   #d9c694;
--paper-bright: #faf1d8;   /* cards, modal */

--ink:          #1b110a;   /* primary text, strong borders */
--ink-2:        #3a2a17;   /* secondary text */
--ink-3:        #6e5832;   /* tertiary text */
--ink-soft:     #8e7549;   /* muted / labels */

--rule:         #b39361;   /* heavy hairlines */
--rule-soft:    #c8ad7c;   /* light hairlines */

--terra:        #b54023;   /* primary accent (terracotta) */
--terra-deep:   #7d2611;   /* primary accent pressed/border */
--wine:         #8a1c2e;   /* destructive / error */
--olive:        #5e6b2c;   /* connection status */
--basil:        #3f5a1d;   /* log "ok" */
--char:         #2a1a0e;
--stamp:        #93250d;   /* rotated rubber-stamp ink */
```

### Typography

| Family           | Source       | Used for                                                        |
| ---------------- | ------------ | --------------------------------------------------------------- |
| Instrument Serif | Google Fonts | All large display text, page titles, rank numerals, italics     |
| Newsreader       | Google Fonts | Body, lede, kicker, button text, small-caps labels              |
| JetBrains Mono   | Google Fonts | Addresses, scores, timestamps, log lines, machine values        |

Google Fonts import:
```
https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1
&family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500
&family=JetBrains+Mono:wght@400;500;600&display=swap
```

Type scale (px):
- Display H1: 88 italic, line-height .92
- H2: 32 italic
- H3 (modal): 38 italic
- Card name: 32 italic
- Stat value: 32 / 28 / 22 (varies by context)
- Body: 16 (default), 17 (lede italic)
- Small-caps label: 11–13 with letter-spacing .18em–.32em
- Mono address/code: 11–13

### Spacing

Page-level: max-width 1280, horizontal padding 36, top section gap 30–40.
Card padding: 22/24/18–22 (top/sides/bottom).
Row padding: 10/14 to 14/14.
Grid gaps: 14, 18, 22, 24.

### Borders & radii

- All cards: **straight corners** (no border-radius). This is intentional —
  reinforces the paper / ticket / receipt mood.
- Hairlines: 1px solid `--rule` (heavy) or `--rule-soft` (light) or dashed for
  internal separators.
- Heavy emphasis: 1px solid `--ink-2` or `3px double --ink` (tabs bar bottom).
- Status stamps: 2px solid color, sometimes dashed.

### Shadows

```css
/* card */
0 1px 0 rgba(28,18,10,.06), 0 12px 24px -16px rgba(28,18,10,.25)

/* card hover */
0 2px 0 rgba(28,18,10,.08), 0 20px 30px -18px rgba(28,18,10,.4)

/* ticket */
0 1px 0 rgba(28,18,10,.06), 0 16px 30px -22px rgba(28,18,10,.55)

/* modal */
0 30px 60px -20px rgba(0,0,0,.6)
```

### Backdrop

The page background uses subtle radial-gradient warmth in two corners *plus* an
SVG turbulence noise overlay (inline data-URL `feTurbulence` baseFrequency .85,
2 octaves, with a sepia-ink color matrix at alpha .07). Reproduce as a tiled
background-image — it's the texture that makes the page feel like paper rather
than flat cream.

---

## Assets

**None required** — all visuals are pure CSS + SVG inlined in the HTML:

- Pizza Bot wordmark: pure text (Instrument Serif italic + colored `&`).
- "AL · APERTO · FORNO" stamp: pure CSS (circular border + rotated text).
- Status stamps: pure CSS borders + text.
- Clothespin on tickets: CSS gradient rectangle (`::before`).
- Perforation lines: repeating-linear-gradient.
- Dotted leaders: 2px dotted border-bottom.
- Paper noise: inline SVG `feTurbulence` data-URL.
- Warning triangle, refresh, checkmark, etc.: small inline SVGs in the HTML.
- Ornament glyph `❦` and arrows: Unicode characters.

If your stack requires real icon components, swap the inline SVGs for your icon
library equivalents — `RotateCw` for refresh, `AlertTriangle` for the warning,
`Check` for the checkbox tick, `Plus` for add. Keep stroke-width ~1.2–1.4.

---

## Implementation Notes

1. **Russian + Italian copy mix is intentional.** Italian is decorative
   (kickers, status stamps, decorative labels, italic titles). Russian is
   functional (button labels, hint text, content the operator actually reads).
   When extracting strings for i18n, keep them in two separate groups: the
   Italian "chrome" is part of the brand and should generally **not** be
   translated. The Russian text is the localizable layer.

2. **No border-radius anywhere.** This is a design rule. Don't add rounded
   corners to "soften" anything. The straight corners + serif type + paper
   texture is the whole point.

3. **Italic Instrument Serif is the brand voice.** Use it generously for
   titles, big numbers, signatures. Use Newsreader for paragraph text.
   JetBrains Mono signals "machine data" — addresses, scores, timestamps.

4. **Stamps must be rotated.** Don't axis-align them. -7° (aperto), -3° (il mio),
   -2.5° (ticket status stamps). The rotation is what makes them feel like
   physical ink rather than a UI badge.

5. **Tickets have alternating tilt.** odd: -.6°, even: +.5°. Keep this even
   if you re-layout to 3 columns.

6. **All numbers use tabular nums** (`font-variant-numeric: tabular-nums`)
   in display contexts so columns of scores align vertically.

7. **Score number formatting** uses Russian locale with thin no-break space
   as thousand separator (U+202F): `17 829`. Implement via
   `n.toLocaleString('ru-RU').replace(/,/g, '\u202f')` or equivalent.

8. **Roman numerals**: top 3 leaderboard ranks display as I / II / III.
   Wallet card numbers display as I / II / III / IV / V / … Use a small
   `toRoman()` helper.

9. **The refresh button doesn't actually re-fetch** in the prototype — it
   jitters local scores. In production, hit the leaderboard endpoint.

10. **Accessibility**: real implementation should add `aria-selected`,
    `role="tab"`, `role="tabpanel"` to the tab system; `aria-label` on
    icon-only buttons; proper `<label>` associations in the modal. The
    prototype doesn't bother.

11. **Mobile**: the spec is **desktop-only**. Don't waste time on responsive
    breakpoints unless explicitly asked.

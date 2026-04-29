# DigDeep — Design Spec for PySide6 Translation

This document maps the HTML prototype to the concrete things a PySide6
implementation needs: design tokens, layout, behaviour, and per-component
contracts. Read alongside `DigDeep Prototype.html`.

---

## 1. Design tokens

### Colours (use `oklch()` in QSS or convert to hex)

| Token | Value | Use |
|---|---|---|
| `--bg` | `oklch(0.13 0.008 250)` → `#1d1f24` | App canvas |
| `--panel` | `oklch(0.175 0.01 250)` → `#272a30` | Cards, panels |
| `--panel-hi` | `oklch(0.215 0.012 250)` → `#32363d` | Hover, selected row |
| `--panel-lo` | `oklch(0.155 0.009 250)` → `#22252a` | Sidebar, sub-surfaces |
| `--border` | `oklch(0.28 0.012 250)` → `#3f434b` | Default 1px borders |
| `--border-hi` | `oklch(0.36 0.014 250)` → `#52575f` | Emphasis borders |
| `--text` | `oklch(0.96 0.005 250)` → `#f1f2f4` | Primary text |
| `--text-dim` | `oklch(0.72 0.008 250)` → `#a8acb3` | Secondary |
| `--text-mute` | `oklch(0.52 0.01 250)` → `#74797f` | Tertiary, hints |
| `--coral` | `oklch(0.74 0.16 45)` → `#ec8a5e` | Brand accent, rally blocks, buttons |
| `--coral-dim` | `oklch(0.62 0.13 45)` → `#c66b44` | Coral gradient bottom |
| `--coral-soft` | `oklch(0.4 0.09 45)` → `#7a4a32` | Soft coral fills, danger close button |
| `--green` | `oklch(0.78 0.13 165)` → `#5cd0a5` | Success, "ready", "playing now" |

### Typography

```qss
* { font-family: "Inter"; }
.timecode, .mono { font-family: "JetBrains Mono"; }
```

| Style | Size | Weight | Use |
|---|---|---|---|
| Title | 24 | 600, letter-spacing -0.4 | Screen headers |
| Section | 14 | 600 | Card titles, project name |
| Body | 13 | 400/500 | Default UI text |
| Meta | 11 | 400 | Subtitles, descriptions |
| Caption | 10 | 600, letter-spacing 1, uppercase | Section labels |
| Mono | 11–12 | 500 | Timecodes, file paths, version strings |

### Spacing & radius

- 8-px base grid. Padding scales: 8, 10, 12, 14, 16, 18, 20, 24, 36.
- Radii: `5` (small chips), `7` (buttons), `8` (radio rows), `10–12` (cards), `14` (large cards).
- Borders: always `1px solid` of `--border` or `--border-hi`. No 2-px borders except focus rings.

### Shadows

Use sparingly:
- Window chrome: `0 30px 60px -20px rgba(0,0,0,0.6)`
- Coral primary button: `0 8px 24px -8px var(--coral)`
- Selected rally block: `0 0 0 2px var(--text), 0 4px 16px -4px var(--coral-dim)`

---

## 2. App shell

```
┌──────────────────────────────────────────────────────────────┐
│ window chrome (Linux/GNOME — your existing OS chrome is fine)│
├──────┬───────────────────────────────────────────────────────┤
│      │                                                       │
│ side │  QStackedWidget                                       │
│ bar  │    ├ LibraryView                                      │
│ 220px│    ├ UploadView                                       │
│      │    ├ ProcessingView                                   │
│      │    ├ EditorView         ← centerpiece                 │
│      │    ├ StatsView                                        │
│      │    ├ ExportView                                       │
│      │    └ SettingsView                                     │
└──────┴───────────────────────────────────────────────────────┘
```

### Sidebar (`Sidebar` widget, fixed 220 px)
- Logo block (26-px coral square + "DigDeep" wordmark)
- Top: **Library**, **New Match**
- After a project is open: **Rally Editor**, **Stats** (with "Soon" badge),
  **Export**
- Bottom: **Settings**, then a footer with `v0.1.0 · models v0.1` and a green
  dot for "CUDA ready"
- Selected item: `--panel-hi` background, coral icon stroke
- Hover: `rgba(255,255,255,0.03)` background

---

## 3. Screen contracts

### LibraryView
- Header: "Library" / "Your processed matches"
- "Process a new match" CTA card with dashed border + coral icon tile
- Recent matches grid: `QGridLayout`, ~240-px cards, striped placeholder thumb,
  `name / date · duration · N rallies`
- Click card → emits `openProject(project)` → switches to EditorView

### UploadView
- Two phases driven by `phase` state: `drop` and `uploading`
- Drop zone: dashed border, hover changes border to coral
- On file pick → fake/real upload progress bar → `processRequested(file)` signal
- Tips below drop zone: 3 columns ("Static camera", "Whole court visible",
  "1080p is plenty")

### ProcessingView
- `RadialProgress` widget (custom-paint a stroked circle)
- Live current-stage card
- 6-step stage list with check / pulse / pending icons
  - decode → ball → players → tracker → rally → snip
- Cancel button + (during dev) a "Skip ahead" demo button
- On completion → `processingDone(project)`

### **EditorView** — translate this most carefully

```
┌────────────────────────────────────────────┬──────────────┐
│ EditorTopBar (56 px)                       │              │
├────────────────────────────────────────────┤              │
│                                            │  RallyList   │
│  VideoPanel (flex-grow)                    │   320 px     │
│                                            │              │
├────────────────────────────────────────────┤              │
│ TransportBar (56 px)                       │              │
├────────────────────────────────────────────┤              │
│ Timeline (160 px: 24 minimap + 22 ruler +  │              │
│  ~100 track)                               │              │
└────────────────────────────────────────────┴──────────────┘
```

#### EditorTopBar
- Project name + subtitle (mono): `1:04:12 source · N rallies kept · M:SS active`
- Right side: undo, redo (icon buttons), auto-save badge, **Export** primary button

#### VideoPanel
- `QVideoWidget` inside a black surface
- Top-left overlay pill: "Rally N of M" + elapsed/total inside rally (coral border, animated dot)
- When playhead is between rallies: "Between rallies" pill, neutral border
- Bottom-right timecode badge `MM:SS.mmm`

#### TransportBar
- Left cluster: prev-rally, play/pause (coral square 36 px), next-rally
- Time display (mono, 168 px wide) showing `current / total`
- Right cluster: **Add rally**, **Delete** (disabled when none selected), zoom slider

#### Timeline (the most custom widget)
Structure (paint everything yourself in `paintEvent`):
1. **Minimap** — full-width 16-px strip of all rallies; viewport rectangle when zoomed.
2. **Ruler** — 22-px row, ticks every 10/30/60/120/300/600 sec depending on
   zoom, mono labels.
3. **Track lane** — `--panel-lo` background; rally blocks painted on top.
4. **Playhead** — 2-px white line + triangle handle in the ruler; drop-shadow.

**Rally block paint:**
- Rounded rect (radius 6)
- Fill: linear gradient `--coral` → `--coral-dim` (or muted grey if `fp=true`)
- 8-px hit zones at left/right edges show resize cursor
- Centred label: "Rally N · M:SS" (Inter 11/600, white, text-shadow)
- Mini white "waveform" bars (decorative texture) at 35% opacity
- Selected: 2-px white outer outline + coral drop-shadow
- Hover: brighter coral fill

**Drag interactions** (handle in `mousePress/Move/Release`):
- Left handle (8 px) → `onRallyResizeStart(id)`, clamps `start ≤ end - 0.5s`
- Right handle (8 px) → `onRallyResizeEnd(id)`, clamps `end ≥ start + 0.5s`
- Body → `onRallyMove(id)`, preserves duration
- Empty area → scrubs playhead

**Keyboard** (install on the EditorView, not just timeline):
- `Space` → toggle play
- `←` / `→` → seek 1 s · `Shift+←/→` → seek 5 s
- `I` / `O` → set in/out of selected rally at playhead
- `Delete` / `Backspace` → delete selected rally
- `Ctrl+Z` / `Ctrl+Shift+Z` → undo / redo
- All keyboard ops go through the same `RallyEditCommand` so undo works

#### RallyList (right rail, 320 px)
- Header: scissors-flag icon, "Rallies", count badge
- Filter segmented control: All / Kept / Skipped (with sub-counts)
- Rows: 3-px coral left bar (green when actively playing, mute when skipped),
  `#NN` mono index, "Rally N", `MM:SS → MM:SS · M:SS` meta line
- "Now" green badge on the rally currently under the playhead
- Hover row toggle button: × to skip / ↻ to restore (skipped rallies stay
  visible, line-through, dimmed)
- Footer: kbd-style hints (`Space`, `I`, `O`, `⌫`, `Ctrl+Z`)
- Auto-scroll to keep selected row in view

### StatsView
- Mark with "Coming Soon" pill in header
- Two cards side by side:
  1. **Ball contact heatmap** — 2:1 court diagram + radial-gradient blobs
  2. **Action counts** — table per track ID (blurred for now)
- Footer banner explaining what ships next

### ExportView
- Two-column grid (1fr / 360 px sticky summary)
- Left column cards:
  - **Format** radio group: Single MP4 / Folder of clips / Original + chapter markers
  - **Options** toggles: pre/post-roll, crossfade, burn rally numbers
  - **Where to save** path input + folder picker button
- Right summary card: stats list + primary Export button → progress bar →
  green "Export complete" success state with reveal-in-files button

### SettingsView
- **Models** card: rows for ball detector, player detector, action classifier
  with installed/pending status pills + "Check for updates" button (calls into
  `huggingface_hub`)
- **Performance**: device, batch size, cache dir
- **About**: version, license, source link

---

## 4. Reusable widgets to build

| Widget | Notes |
|---|---|
| `IconButton` | 32×32, hover bg, active state, takes a stroke-icon path |
| `PrimaryButton` | Coral fill, 13/600 white text, 7-px radius |
| `GhostButton` | Transparent + 1-px border, dim text on hover→bright |
| `Card` | Panel bg + border + radius 12, optional uppercase caption header |
| `RadialProgress` | Custom paint, 240 px, coral arc on panel bg |
| `Toggle` | 32×18 pill, white knob, coral when on |
| `KbdLabel` | Mono 10/500, panel-hi bg, 1-px border, 3-px radius |
| `StripedPlaceholder` | 135° repeating-linear-gradient, used for thumbs / video standin |

---

## 5. State / signals

Centralise in a `MatchSession` model so views can sit on signals:

```python
class MatchSession(QObject):
    railliesChanged = Signal()        # whole list
    rallySelectionChanged = Signal(str)  # id or ""
    playheadChanged = Signal(float)   # seconds
    playStateChanged = Signal(bool)
    canUndoChanged = Signal(bool)
    canRedoChanged = Signal(bool)

    def add_rally(self, t: float) -> str: ...
    def delete_rally(self, rally_id: str) -> None: ...
    def set_in(self, rally_id: str, t: float) -> None: ...
    def set_out(self, rally_id: str, t: float) -> None: ...
    def move_rally(self, rally_id: str, dt: float) -> None: ...
    def toggle_skip(self, rally_id: str) -> None: ...
    def undo(self) -> None: ...
    def redo(self) -> None: ...
```

Every mutation pushes a `RallyEditCommand` onto a `QUndoStack`.

---

## 6. Worker integration

The existing `PipelineWorker` already emits `progress`, `stage_changed`,
`finished`, `error`. Wire them to ProcessingView:

| Signal | View action |
|---|---|
| `stage_changed(str)` | Highlight matching stage row, update detail line |
| `progress(int, int)` | Update `RadialProgress` value |
| `finished(str)` | Switch stack to EditorView, load output rallies + analytics JSON |
| `error(str)` | Show inline error banner; stay on ProcessingView |

---

## 7. Analytics JSON contract

`SHARED_CONTEXT.md` already defines the schema. The Editor reads only
`rallies[]` (start_frame / end_frame / duration_sec). When the action
classifier ships, StatsView will read `players[track_id]`.

---

## 8. Test surface

Pure functions to unit-test (no Qt needed):
- `Timeline.x_to_t / t_to_x` (zoom + scroll math)
- `RallySession.add / delete / move / set_in / set_out` (clamping, sorting)
- `UndoStack` correctness across mixed mutations
- `Tick.choose_interval(zoom, total)` (matches the prototype's tick spacing)

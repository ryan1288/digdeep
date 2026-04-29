# DigDeep PySide6 — Design Handoff

This folder contains everything Claude Code needs to translate the HTML prototype
(`DigDeep Prototype.html`) into the PySide6 desktop app in the `digdeep/` repo.

---

## What to give Claude Code

Drop these into `digdeep/design/` (or attach the whole folder when you start the
Claude Code session):

1. **`DigDeep Prototype.html`** + **`app.jsx`** — the working prototype. Open it
   to interact with every screen, every state, every animation. It's the single
   source of truth for behaviour.
2. **`design/DESIGN_SPEC.md`** (this folder) — tokens, layout, behaviour,
   component-by-component notes.
3. **`design/screenshots/`** — PNG of every screen + key states, for quick
   reference without running the prototype.
4. **`design/digdeep-logo.png`** — already in `assets/`.

---

## Asks for Claude Code (paste this as your first prompt)

> Translate `design/DigDeep Prototype.html` into a PySide6 application. The
> prototype is the source of truth for layout, interactions, and visual style;
> `design/DESIGN_SPEC.md` lists tokens and component contracts.
>
> Ground rules:
> - Use **QSS** (Qt Style Sheets) for all visual styling — colours, radii,
>   borders, hover states. The token list is in DESIGN_SPEC.md.
> - Use **`Inter`** for UI and **`JetBrains Mono`** for timecodes. Bundle both
>   as `.ttf` under `assets/fonts/` and load them via `QFontDatabase` at startup.
> - The Rally Editor's timeline is a **custom `QWidget`** (or `QGraphicsView`).
>   Don't try to bend a `QSlider` into rally blocks — paint it yourself with
>   `QPainter`. Drag handles, block move, and playhead all live there.
> - Video playback: **`QMediaPlayer` + `QVideoWidget`**. Wire the video's
>   `positionChanged` signal to the timeline's playhead, and the timeline's
>   scrub events back to `setPosition`.
> - Keep the existing pipeline glue (`src/inference/`, `src/app/worker.py`)
>   exactly as-is. Only rebuild `src/app/main_window.py` and add new widget
>   modules.
> - Match the prototype's empty/upload/processing/editor/stats/export/settings
>   screens. Use `QStackedWidget` to switch between them.
>
> Deliver:
> - `src/app/main_window.py` (shell + sidebar + stacked views)
> - `src/app/views/` (one file per screen)
> - `src/app/widgets/` (timeline, rally_block, rally_list, video_panel,
>   transport_bar, court_heatmap)
> - `src/app/style.qss` (compiled from design tokens)
> - `assets/fonts/` (Inter + JetBrains Mono)
> - Tests for the timeline drag math (pure functions — no Qt needed).

---

## File map

```
design/
  DigDeep Prototype.html     ← interactive reference, run with any browser
  app.jsx                    ← React source, useful for reading exact behaviour
  DESIGN_SPEC.md             ← tokens, layout, components, interactions
  screenshots/
    01-library.png
    02-upload.png
    03-uploading.png
    04-processing.png
    05-editor.png
    06-editor-rally-selected.png
    07-stats.png
    08-export.png
    09-export-done.png
    10-settings.png
  digdeep-logo.png
```

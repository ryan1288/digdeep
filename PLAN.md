# DigDeep UI — Plan
# Inference app + PySide6 UI. Training-side plan lives in digdeep-training/PLAN.md.

## Phase 1 — Bootstrap  `[~1 week]`
Goal: end-to-end loop closes. File in → pipeline runs → rally-snipped MP4 out.
Depends on: digdeep-training P1.8 (BallDetector), P1.11 (RallyDetector), P1.12 (AnalyticsAggregator stub) — all done.

| # | Task | Done |
|---|---|---|
| 1.13 | Scaffold src/ layout + install deps | ☐ |
| 1.13 | File picker UI → run pipeline → save output MP4 | ☐ |
| 1.13 | HuggingFace Hub weight download on first launch | ☐ |
| 1.13 | Write analytics JSON sidecar alongside output MP4 | ☐ |

**Exit criteria**: drag a match video in, get a rally-only MP4 out. No quality bar yet.

---

## Phase 3 — MVP Product  `[~3 weeks]`
Goal: shippable app. Auto-snipped video + player action stats in one UI.
Depends on: digdeep-training Phase 2 complete (models good enough for real stats).

| # | Task | Done |
|---|---|---|
| 3.1 | Rally list with false-positive checkboxes + embedded video preview | ☐ |
| 3.2 | Stats panel: per-track-ID action count table (sortable) | ☐ |
| 3.3 | Optional name assignment UI: user labels track IDs with player names | ☐ |
| 3.4 | HuggingFace Hub auto-download with version pinning | ☐ |
| 3.5 | Output: rally-only MP4 + analytics JSON sidecar | ☐ |
| 3.6 | Apache 2.0 licence confirmed, repo public | ☐ |
| 3.7 | GitHub Actions CI: lint + tests on PR | ☐ |
| 3.8 | PyInstaller packaging (Linux first) | ☐ |
| 3.9 | README (non-technical audience) + HuggingFace model cards | ☐ |
| 3.10 | Community launch + footage contribution form | ☐ |

**Exit criteria**: installable app producing rally video + player stats JSON.
At least 5 external users tested it.

---

## Phase 4 — Analytics Depth  `[ongoing]`
Goal: stats useful for coaching and player development.

**Visualizations**
- Ball contact heatmap overlaid on 2D court diagram (from ball_contacts in analytics JSON)
- Player court coverage heatmap (from court_positions — requires homography)
- Per-rally timeline: who did what, when
- Action-specific replay clips (e.g. "show all attacks by track 3")

**Player identity improvements**
- In-app track correction UI: merge split tracks, fix ID switches
- Jersey color clustering (K-means HSV) for team assignment
- Cross-match identity (future: jersey number recognition)

**3D scene understanding**
- Court corner annotation UI (user clicks 4 corners once per video)
- Homography → player foot positions in metric court coordinates
- DepthAnythingV2 for ball height estimation
- Ball velocity, arc, and landing zone prediction

/* global React, ReactDOM */
const { useState, useEffect, useRef, useCallback, useMemo } = React;

// ============================================================
// Design tokens
// ============================================================
const C = {
  bg: "oklch(0.13 0.008 250)",
  panel: "oklch(0.175 0.01 250)",
  panelHi: "oklch(0.215 0.012 250)",
  panelLo: "oklch(0.155 0.009 250)",
  border: "oklch(0.28 0.012 250)",
  borderHi: "oklch(0.36 0.014 250)",
  text: "oklch(0.96 0.005 250)",
  textDim: "oklch(0.72 0.008 250)",
  textMute: "oklch(0.52 0.01 250)",
  coral: "oklch(0.74 0.16 45)",
  coralDim: "oklch(0.62 0.13 45)",
  coralSoft: "oklch(0.4 0.09 45)",
  green: "oklch(0.78 0.13 165)",
  greenDim: "oklch(0.6 0.1 165)",
  rallyFill: "oklch(0.72 0.14 45 / 0.85)",
  rallyEdge: "oklch(0.86 0.16 45)",
  rallyHover: "oklch(0.78 0.16 45)",
  rallySelectedFill: "oklch(0.78 0.17 45)",
};

const FONT_UI = '"Inter", -apple-system, "Segoe UI", system-ui, sans-serif';
const FONT_MONO = '"JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace';

// ============================================================
// Mock state — fake video duration in seconds, fake rally segments
// ============================================================
const MOCK_DURATION = 64 * 60 + 12; // 64:12
const SEED_RALLIES = [
  { id: "r1", start: 142, end: 167, fp: false },
  { id: "r2", start: 198, end: 224, fp: false },
  { id: "r3", start: 251, end: 273, fp: false },
  { id: "r4", start: 305, end: 328, fp: false },
  { id: "r5", start: 362, end: 391, fp: false },
  { id: "r6", start: 421, end: 446, fp: false },
  { id: "r7", start: 478, end: 502, fp: false },
  { id: "r8", start: 532, end: 559, fp: false },
  { id: "r9", start: 591, end: 615, fp: false },
  { id: "r10", start: 644, end: 671, fp: false },
  { id: "r11", start: 702, end: 731, fp: false },
  { id: "r12", start: 762, end: 788, fp: false },
  { id: "r13", start: 824, end: 852, fp: false },
  { id: "r14", start: 884, end: 911, fp: false },
  { id: "r15", start: 940, end: 968, fp: false },
  { id: "r16", start: 998, end: 1029, fp: false },
  { id: "r17", start: 1062, end: 1091, fp: false },
  { id: "r18", start: 1122, end: 1148, fp: false },
  { id: "r19", start: 1184, end: 1213, fp: false },
  { id: "r20", start: 1248, end: 1278, fp: false },
  { id: "r21", start: 1312, end: 1339, fp: false },
  { id: "r22", start: 1376, end: 1404, fp: false },
  { id: "r23", start: 1440, end: 1469, fp: false },
  { id: "r24", start: 1502, end: 1531, fp: false },
  { id: "r25", start: 1564, end: 1592, fp: false },
  { id: "r26", start: 1626, end: 1656, fp: false },
  { id: "r27", start: 1688, end: 1717, fp: false },
  { id: "r28", start: 1748, end: 1779, fp: false },
  { id: "r29", start: 1812, end: 1841, fp: false },
  { id: "r30", start: 1872, end: 1900, fp: false },
  { id: "r31", start: 1932, end: 1961, fp: false },
  { id: "r32", start: 1996, end: 2024, fp: false },
  { id: "r33", start: 2058, end: 2086, fp: false },
  { id: "r34", start: 2122, end: 2151, fp: false },
  { id: "r35", start: 2186, end: 2214, fp: false },
  { id: "r36", start: 2249, end: 2278, fp: false },
  { id: "r37", start: 2312, end: 2342, fp: false },
  { id: "r38", start: 2378, end: 2408, fp: false },
  { id: "r39", start: 2442, end: 2470, fp: false },
  { id: "r40", start: 2506, end: 2536, fp: false },
  { id: "r41", start: 2572, end: 2600, fp: false },
  { id: "r42", start: 2638, end: 2667, fp: false },
  { id: "r43", start: 2705, end: 2735, fp: false },
  { id: "r44", start: 2772, end: 2802, fp: false },
  { id: "r45", start: 2840, end: 2870, fp: false },
  { id: "r46", start: 2910, end: 2940, fp: false },
  { id: "r47", start: 2980, end: 3010, fp: false },
  { id: "r48", start: 3050, end: 3081, fp: false },
  { id: "r49", start: 3120, end: 3150, fp: false },
  { id: "r50", start: 3190, end: 3220, fp: false },
  { id: "r51", start: 3260, end: 3291, fp: false },
  { id: "r52", start: 3330, end: 3358, fp: false },
  { id: "r53", start: 3398, end: 3428, fp: false },
  { id: "r54", start: 3464, end: 3492, fp: false },
  { id: "r55", start: 3528, end: 3558, fp: false },
  { id: "r56", start: 3596, end: 3624, fp: false },
  { id: "r57", start: 3672, end: 3700, fp: false },
  { id: "r58", start: 3748, end: 3776, fp: false },
  { id: "r59", start: 3820, end: 3848, fp: false },
];

// ============================================================
// Helpers
// ============================================================
const fmt = (s) => {
  if (!isFinite(s) || s < 0) s = 0;
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  return `${m}:${String(sec).padStart(2, "0")}`;
};
const fmtMs = (s) => {
  const total = Math.max(0, s);
  const m = Math.floor(total / 60);
  const sec = Math.floor(total % 60);
  const ms = Math.floor((total - Math.floor(total)) * 1000);
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}.${String(ms).padStart(3, "0")}`;
};

// ============================================================
// Tiny icon set (stroke-only, hand-tuned, no slop)
// ============================================================
const Icon = ({ d, size = 16, stroke = "currentColor", fill = "none", w = 1.6, style }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={fill} stroke={stroke}
       strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" style={style}>
    {typeof d === "string" ? <path d={d} /> : d}
  </svg>
);
const ICONS = {
  play: "M7 5l12 7-12 7V5z",
  pause: <>{[<rect key="a" x="6" y="5" width="4" height="14" rx="1" fill="currentColor" stroke="none"/>,<rect key="b" x="14" y="5" width="4" height="14" rx="1" fill="currentColor" stroke="none"/>]}</>,
  prev: "M6 5v14M19 5l-9 7 9 7V5z",
  next: "M18 5v14M5 5l9 7-9 7V5z",
  upload: "M12 16V4M6 10l6-6 6 6M4 18h16",
  folder: "M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z",
  film: "M3 5h18v14H3zM3 9h18M3 15h18M7 5v14M17 5v14",
  scissors: "M6 6l12 12M6 18l4.5-4.5M18 6l-4.5 4.5M8 8a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM8 18a2 2 0 1 1-4 0 2 2 0 0 1 4 0z",
  trash: "M4 7h16M9 7V4h6v3M6 7l1 13a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-13",
  plus: "M12 5v14M5 12h14",
  undo: "M9 14l-5-5 5-5M4 9h11a5 5 0 0 1 0 10h-3",
  redo: "M15 14l5-5-5-5M20 9H9a5 5 0 0 0 0 10h3",
  settings: "M12 9a3 3 0 1 1 0 6 3 3 0 0 1 0-6zM19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.5-2.4.9a7 7 0 0 0-2-1.2L14 3h-4l-.4 2.4a7 7 0 0 0-2 1.2l-2.4-.9-2 3.5 2 1.6A7 7 0 0 0 5 12c0 .4 0 .8.1 1.2l-2 1.6 2 3.5 2.4-.9c.6.5 1.3.9 2 1.2L10 21h4l.4-2.4c.7-.3 1.4-.7 2-1.2l2.4.9 2-3.5-2-1.6c.1-.4.1-.8.1-1.2z",
  download: "M12 4v12M6 12l6 6 6-6M4 20h16",
  close: "M6 6l12 12M18 6L6 18",
  check: "M5 12l5 5 9-11",
  clock: "M12 7v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z",
  flag: "M4 21V4M4 4h12l-2 4 2 4H4",
  chevron: "M9 6l6 6-6 6",
  chevronDown: "M6 9l6 6 6-6",
  search: "M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16zM21 21l-4.3-4.3",
  volleyball: "M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18zM12 3c3 4 3 14 0 18M12 3c-3 4-3 14 0 18M3 12c4-3 14-3 18 0",
  zap: "M13 2L3 14h7l-1 8 10-12h-7l1-8z",
  refresh: "M3 12a9 9 0 0 1 15.5-6.3L21 8M21 3v5h-5M21 12a9 9 0 0 1-15.5 6.3L3 16M3 21v-5h5",
  external: "M14 4h6v6M10 14L20 4M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5",
};

// ============================================================
// Linux/GNOME-ish window chrome
// ============================================================
const WindowChrome = ({ title, children, onMinimize }) => (
  <div style={{
    background: C.bg,
    border: `1px solid ${C.border}`,
    borderRadius: 12,
    overflow: "hidden",
    boxShadow: "0 30px 60px -20px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.02) inset",
    display: "flex", flexDirection: "column",
    height: "100%",
  }}>
    <div style={{
      height: 38,
      background: C.panelLo,
      borderBottom: `1px solid ${C.border}`,
      display: "flex", alignItems: "center",
      padding: "0 12px",
      gap: 12,
      flexShrink: 0,
    }}>
      <div style={{ display: "flex", gap: 8 }}>
        <button style={chromeBtn} aria-label="back"><Icon d="M15 18l-6-6 6-6" size={12} /></button>
        <button style={chromeBtn} aria-label="forward"><Icon d="M9 18l6-6-6-6" size={12} /></button>
      </div>
      <div style={{
        flex: 1, textAlign: "center",
        fontFamily: FONT_UI, fontSize: 13, color: C.textDim, fontWeight: 500,
        letterSpacing: 0.1,
      }}>{title}</div>
      <div style={{ display: "flex", gap: 6 }}>
        <button style={{ ...chromeBtn, background: "transparent" }} aria-label="minimize" onClick={onMinimize}>
          <div style={{ width: 10, height: 1.5, background: C.textDim }} />
        </button>
        <button style={{ ...chromeBtn, background: "transparent" }} aria-label="maximize">
          <div style={{ width: 9, height: 9, border: `1.5px solid ${C.textDim}`, borderRadius: 1 }} />
        </button>
        <button style={{ ...chromeBtn, background: C.coralSoft, color: C.text }} aria-label="close">
          <Icon d={ICONS.close} size={10} w={2} />
        </button>
      </div>
    </div>
    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
      {children}
    </div>
  </div>
);

const chromeBtn = {
  width: 22, height: 22, borderRadius: 11,
  background: C.panelHi,
  border: `1px solid ${C.border}`,
  color: C.textDim,
  cursor: "pointer",
  display: "flex", alignItems: "center", justifyContent: "center",
  padding: 0,
};

// ============================================================
// Sidebar
// ============================================================
const Sidebar = ({ project, onNav, current, onSettings }) => (
  <div style={{
    width: 220,
    background: C.panelLo,
    borderRight: `1px solid ${C.border}`,
    display: "flex", flexDirection: "column",
    flexShrink: 0,
  }}>
    <div style={{ padding: "18px 18px 14px", display: "flex", alignItems: "center", gap: 10 }}>
      <div style={{
        width: 26, height: 26, borderRadius: 7,
        background: `linear-gradient(135deg, ${C.coral}, ${C.coralDim})`,
        display: "flex", alignItems: "center", justifyContent: "center",
        color: "white", fontWeight: 700, fontFamily: FONT_UI, fontSize: 13,
        boxShadow: `0 2px 8px -2px ${C.coral}`,
      }}>D</div>
      <div style={{ fontFamily: FONT_UI, fontWeight: 600, fontSize: 14, color: C.text, letterSpacing: 0.2 }}>
        DigDeep
      </div>
    </div>

    <div style={{ padding: "0 12px", marginBottom: 8 }}>
      <SidebarItem icon={ICONS.film} label="Library" active={current === "library"} onClick={() => onNav("library")} />
      <SidebarItem icon={ICONS.upload} label="New Match" active={current === "upload"} onClick={() => onNav("upload")} />
    </div>

    {project && (
      <>
        <SidebarLabel>Current match</SidebarLabel>
        <div style={{ padding: "0 12px" }}>
          <SidebarItem icon={ICONS.scissors} label="Rally Editor"
            active={current === "editor"} onClick={() => onNav("editor")} />
          <SidebarItem icon={ICONS.volleyball} label="Stats" badge="Soon"
            active={current === "stats"} onClick={() => onNav("stats")} />
          <SidebarItem icon={ICONS.download} label="Export"
            active={current === "export"} onClick={() => onNav("export")} />
        </div>
      </>
    )}

    <div style={{ flex: 1 }} />

    <div style={{ padding: 12, borderTop: `1px solid ${C.border}`, display: "flex", flexDirection: "column", gap: 4 }}>
      <SidebarItem icon={ICONS.settings} label="Settings" subtle onClick={onSettings} active={current === "settings"} />
      <div style={{ padding: "8px 10px", fontFamily: FONT_MONO, fontSize: 10, color: C.textMute, lineHeight: 1.5 }}>
        v0.1.0 · models v0.1<br/>
        <span style={{ color: C.green }}>●</span> CUDA ready
      </div>
    </div>
  </div>
);

const SidebarLabel = ({ children }) => (
  <div style={{
    padding: "14px 22px 6px", fontFamily: FONT_UI, fontSize: 10,
    fontWeight: 600, letterSpacing: 1, color: C.textMute, textTransform: "uppercase",
  }}>{children}</div>
);

const SidebarItem = ({ icon, label, active, badge, subtle, onClick }) => (
  <button onClick={onClick} style={{
    width: "100%", display: "flex", alignItems: "center", gap: 10,
    padding: "8px 10px", borderRadius: 7,
    border: "none", cursor: "pointer", textAlign: "left",
    background: active ? C.panelHi : "transparent",
    color: active ? C.text : (subtle ? C.textMute : C.textDim),
    fontFamily: FONT_UI, fontSize: 13, fontWeight: active ? 500 : 400,
    transition: "background 0.15s",
  }}
  onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}
  onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = "transparent"; }}>
    <Icon d={icon} size={15} stroke={active ? C.coral : "currentColor"} />
    <span style={{ flex: 1 }}>{label}</span>
    {badge && (
      <span style={{
        fontSize: 9, fontWeight: 600, padding: "2px 6px", borderRadius: 4,
        background: C.panelHi, color: C.textMute, letterSpacing: 0.5,
        textTransform: "uppercase", fontFamily: FONT_UI,
      }}>{badge}</span>
    )}
  </button>
);

// ============================================================
// Library / Empty state
// ============================================================
const LibraryScreen = ({ onNew, onOpen, projects }) => (
  <div style={{ flex: 1, display: "flex", flexDirection: "column", background: C.bg, overflow: "auto" }}>
    <ScreenHeader title="Library" sub="Your processed matches" />
    <div style={{ padding: "8px 36px 36px", display: "flex", flexDirection: "column", gap: 24 }}>
      {/* New match callout */}
      <div onClick={onNew} style={{
        background: `linear-gradient(135deg, ${C.panelLo}, ${C.panel})`,
        border: `1px dashed ${C.borderHi}`,
        borderRadius: 14, padding: "28px 32px",
        display: "flex", alignItems: "center", gap: 24,
        cursor: "pointer",
        transition: "all 0.2s",
      }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = C.coral; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = C.borderHi; }}>
        <div style={{
          width: 56, height: 56, borderRadius: 14,
          background: `linear-gradient(135deg, ${C.coral}, ${C.coralDim})`,
          display: "flex", alignItems: "center", justifyContent: "center",
          color: "white",
          boxShadow: `0 8px 24px -8px ${C.coral}`,
        }}>
          <Icon d={ICONS.upload} size={26} w={2} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: FONT_UI, fontSize: 18, fontWeight: 600, color: C.text, marginBottom: 4 }}>
            Process a new match
          </div>
          <div style={{ fontFamily: FONT_UI, fontSize: 13, color: C.textDim }}>
            Drop in a full-match video. DigDeep finds the rallies, you fine-tune.
          </div>
        </div>
        <div style={{
          padding: "8px 14px", borderRadius: 7,
          background: C.coral, color: "white",
          fontFamily: FONT_UI, fontSize: 13, fontWeight: 600,
        }}>Choose video</div>
      </div>

      {/* Recent grid */}
      <div>
        <div style={{ display: "flex", alignItems: "center", marginBottom: 14 }}>
          <div style={{ fontFamily: FONT_UI, fontSize: 12, fontWeight: 600, color: C.textMute,
                        letterSpacing: 1, textTransform: "uppercase" }}>Recent</div>
          <div style={{ flex: 1, height: 1, background: C.border, marginLeft: 12 }} />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 14 }}>
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} onOpen={() => onOpen(p)} />
          ))}
        </div>
      </div>
    </div>
  </div>
);

const ProjectCard = ({ project, onOpen }) => (
  <div onClick={onOpen} style={{
    background: C.panel, border: `1px solid ${C.border}`,
    borderRadius: 12, overflow: "hidden", cursor: "pointer",
    transition: "all 0.15s",
  }}
  onMouseEnter={(e) => { e.currentTarget.style.borderColor = C.borderHi; e.currentTarget.style.transform = "translateY(-1px)"; }}
  onMouseLeave={(e) => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.transform = "translateY(0)"; }}>
    <CourtPlaceholder height={130} label={project.thumbLabel || "match footage"} />
    <div style={{ padding: "12px 14px" }}>
      <div style={{ fontFamily: FONT_UI, fontSize: 14, fontWeight: 600, color: C.text, marginBottom: 4,
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {project.name}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontFamily: FONT_UI, fontSize: 11, color: C.textMute }}>
        <span>{project.date}</span>
        <span style={{ width: 3, height: 3, borderRadius: 2, background: C.textMute }} />
        <span>{project.duration}</span>
        <span style={{ width: 3, height: 3, borderRadius: 2, background: C.textMute }} />
        <span style={{ color: C.coral }}>{project.rallies} rallies</span>
      </div>
    </div>
  </div>
);

// Striped court placeholder (no AI illustrations)
const CourtPlaceholder = ({ height = 200, label = "match footage", aspect }) => {
  const style = aspect
    ? { aspectRatio: aspect, width: "100%" }
    : { height };
  return (
    <div style={{
      ...style,
      background: `repeating-linear-gradient(135deg, ${C.panelHi}, ${C.panelHi} 8px, ${C.panel} 8px, ${C.panel} 16px)`,
      borderBottom: `1px solid ${C.border}`,
      position: "relative",
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <div style={{
        fontFamily: FONT_MONO, fontSize: 10, color: C.textMute,
        background: C.panelLo, padding: "3px 8px", borderRadius: 4,
        border: `1px solid ${C.border}`, letterSpacing: 0.5,
      }}>{label}</div>
    </div>
  );
};

const ScreenHeader = ({ title, sub, right }) => (
  <div style={{
    padding: "26px 36px 18px",
    display: "flex", alignItems: "flex-end", gap: 16,
  }}>
    <div style={{ flex: 1 }}>
      <div style={{ fontFamily: FONT_UI, fontSize: 24, fontWeight: 600, color: C.text, letterSpacing: -0.4 }}>
        {title}
      </div>
      {sub && <div style={{ fontFamily: FONT_UI, fontSize: 13, color: C.textDim, marginTop: 4 }}>{sub}</div>}
    </div>
    {right}
  </div>
);

// ============================================================
// Upload screen
// ============================================================
const UploadScreen = ({ onProcess, onCancel }) => {
  const [phase, setPhase] = useState("drop"); // drop | uploading
  const [file, setFile] = useState(null);
  const [pct, setPct] = useState(0);

  const triggerSelect = () => {
    setFile({ name: "Tuesday Night League — Wk 7.mp4", size: "1.4 GB", duration: "1:04:12" });
    setPhase("uploading");
    setPct(0);
  };

  useEffect(() => {
    if (phase !== "uploading") return;
    const t = setInterval(() => {
      setPct((p) => {
        const next = p + 4 + Math.random() * 6;
        if (next >= 100) {
          clearInterval(t);
          setTimeout(() => onProcess(file), 400);
          return 100;
        }
        return next;
      });
    }, 120);
    return () => clearInterval(t);
  }, [phase, file, onProcess]);

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", background: C.bg, overflow: "auto" }}>
      <ScreenHeader title="New match" sub="Drop a full-match recording. We'll handle the trimming." />
      <div style={{ padding: "8px 36px 36px", flex: 1, display: "flex", flexDirection: "column" }}>
        {phase === "drop" && (
          <div onClick={triggerSelect} style={{
            flex: 1, minHeight: 320,
            border: `2px dashed ${C.borderHi}`,
            borderRadius: 16,
            background: C.panelLo,
            display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
            gap: 18, cursor: "pointer",
            transition: "all 0.2s",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = C.coral; e.currentTarget.style.background = C.panel; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = C.borderHi; e.currentTarget.style.background = C.panelLo; }}>
            <div style={{
              width: 72, height: 72, borderRadius: 18,
              background: C.panel, border: `1px solid ${C.border}`,
              display: "flex", alignItems: "center", justifyContent: "center",
              color: C.coral,
            }}>
              <Icon d={ICONS.upload} size={32} w={1.8} />
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontFamily: FONT_UI, fontSize: 18, fontWeight: 600, color: C.text, marginBottom: 6 }}>
                Drop a match video here
              </div>
              <div style={{ fontFamily: FONT_UI, fontSize: 13, color: C.textDim }}>
                or click to browse · MP4, MOV, MKV up to 8 GB
              </div>
            </div>
            <div style={{ marginTop: 8, padding: "8px 16px", borderRadius: 7,
                          background: C.coral, color: "white",
                          fontFamily: FONT_UI, fontSize: 13, fontWeight: 600 }}>
              Choose file
            </div>
            <Tips />
          </div>
        )}
        {phase === "uploading" && (
          <UploadingPanel file={file} pct={pct} onCancel={() => { setPhase("drop"); setFile(null); }} />
        )}
      </div>
    </div>
  );
};

const Tips = () => (
  <div style={{ marginTop: 24, display: "flex", gap: 24, justifyContent: "center", flexWrap: "wrap" }}>
    {[
      ["Static camera", "Tripod or stable mount works best"],
      ["Whole court visible", "Both sides + sidelines in frame"],
      ["1080p is plenty", "Higher res doesn't improve detection"],
    ].map(([h, b]) => (
      <div key={h} style={{ maxWidth: 180, textAlign: "center" }}>
        <div style={{ fontFamily: FONT_UI, fontSize: 12, fontWeight: 600, color: C.textDim, marginBottom: 2 }}>{h}</div>
        <div style={{ fontFamily: FONT_UI, fontSize: 11, color: C.textMute, lineHeight: 1.4 }}>{b}</div>
      </div>
    ))}
  </div>
);

const UploadingPanel = ({ file, pct, onCancel }) => (
  <div style={{
    flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 24,
  }}>
    <div style={{
      width: 480, padding: 24,
      background: C.panel, border: `1px solid ${C.border}`,
      borderRadius: 14,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 18 }}>
        <div style={{ width: 44, height: 44, borderRadius: 10, background: C.panelHi,
                      display: "flex", alignItems: "center", justifyContent: "center", color: C.coral }}>
          <Icon d={ICONS.film} size={22} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: FONT_UI, fontSize: 14, fontWeight: 600, color: C.text,
                        overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {file.name}
          </div>
          <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: C.textMute, marginTop: 2 }}>
            {file.size} · {file.duration}
          </div>
        </div>
        <button onClick={onCancel} style={iconBtn}>
          <Icon d={ICONS.close} size={14} />
        </button>
      </div>
      <div style={{ height: 6, background: C.panelLo, borderRadius: 3, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${pct}%`, background: C.coral, transition: "width 0.12s linear" }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 10,
                    fontFamily: FONT_MONO, fontSize: 11, color: C.textDim }}>
        <span>Uploading…</span>
        <span>{Math.floor(pct)}%</span>
      </div>
    </div>
  </div>
);

const iconBtn = {
  width: 28, height: 28, borderRadius: 7,
  background: "transparent", border: `1px solid ${C.border}`,
  color: C.textDim, cursor: "pointer",
  display: "flex", alignItems: "center", justifyContent: "center",
};

// ============================================================
// Processing screen
// ============================================================
const STAGES = [
  { key: "decode", label: "Decoding video", detail: "Reading frames at source resolution" },
  { key: "ball", label: "Tracking the ball", detail: "Heatmap regression over 9-frame windows" },
  { key: "players", label: "Finding players", detail: "RF-DETR on every frame" },
  { key: "track", label: "Linking players across frames", detail: "BoT-SORT-ReID with appearance memory" },
  { key: "rally", label: "Detecting rallies", detail: "Ball trajectory + game-state fusion" },
  { key: "snip", label: "Snipping rallies", detail: "Almost done…" },
];

const ProcessingScreen = ({ onDone, onCancel, file }) => {
  const [progress, setProgress] = useState(0);
  const [stageIdx, setStageIdx] = useState(0);
  const [auto, setAuto] = useState(true);

  useEffect(() => {
    if (!auto) return;
    const t = setInterval(() => {
      setProgress((p) => {
        const next = Math.min(100, p + 0.6 + Math.random() * 0.6);
        const target = Math.floor((next / 100) * STAGES.length);
        setStageIdx(Math.min(STAGES.length - 1, target));
        if (next >= 100) {
          clearInterval(t);
          setTimeout(onDone, 700);
        }
        return next;
      });
    }, 80);
    return () => clearInterval(t);
  }, [auto, onDone]);

  const stage = STAGES[stageIdx];

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", background: C.bg, overflow: "auto" }}>
      <ScreenHeader title="Processing match" sub={file?.name || "Match"} />
      <div style={{ padding: "8px 36px 36px", display: "flex", flexDirection: "column", gap: 24, alignItems: "center" }}>

        {/* Big radial progress */}
        <div style={{ position: "relative", width: 240, height: 240, marginTop: 12 }}>
          <RadialProgress value={progress} />
          <div style={{
            position: "absolute", inset: 0,
            display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
          }}>
            <div style={{ fontFamily: FONT_MONO, fontSize: 38, fontWeight: 500, color: C.text, letterSpacing: -1 }}>
              {Math.floor(progress)}<span style={{ fontSize: 18, color: C.textDim }}>%</span>
            </div>
            <div style={{ fontFamily: FONT_UI, fontSize: 11, color: C.textMute, letterSpacing: 1, textTransform: "uppercase", marginTop: 4 }}>
              {Math.max(1, Math.ceil(((100 - progress) / 100) * 8))} min remaining
            </div>
          </div>
        </div>

        <div style={{
          background: C.panel, border: `1px solid ${C.border}`,
          borderRadius: 12, padding: "16px 20px",
          width: 480, textAlign: "center",
        }}>
          <div style={{ fontFamily: FONT_UI, fontSize: 15, fontWeight: 600, color: C.text }}>
            {stage.label}
          </div>
          <div style={{ fontFamily: FONT_UI, fontSize: 12, color: C.textDim, marginTop: 4 }}>
            {stage.detail}
          </div>
        </div>

        {/* Stage steps */}
        <div style={{ width: 560, background: C.panel, border: `1px solid ${C.border}`,
                      borderRadius: 12, padding: 4 }}>
          {STAGES.map((s, i) => {
            const done = i < stageIdx;
            const active = i === stageIdx;
            return (
              <div key={s.key} style={{
                display: "flex", alignItems: "center", gap: 14,
                padding: "10px 14px", borderRadius: 8,
                background: active ? C.panelHi : "transparent",
              }}>
                <div style={{
                  width: 22, height: 22, borderRadius: 11,
                  background: done ? C.green : (active ? C.coral : C.panelLo),
                  border: `1px solid ${done ? C.green : (active ? C.coral : C.border)}`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: done || active ? "white" : C.textMute,
                  fontFamily: FONT_MONO, fontSize: 11, fontWeight: 600,
                }}>
                  {done ? <Icon d={ICONS.check} size={11} w={2.5} /> : (active ? <PulseDot /> : i + 1)}
                </div>
                <div style={{ flex: 1, fontFamily: FONT_UI, fontSize: 13,
                              color: done ? C.textDim : (active ? C.text : C.textMute),
                              fontWeight: active ? 600 : 400 }}>
                  {s.label}
                </div>
                {done && <div style={{ fontFamily: FONT_MONO, fontSize: 10, color: C.textMute }}>done</div>}
              </div>
            );
          })}
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={onCancel} style={ghostBtn}>Cancel</button>
          <button onClick={onDone} style={ghostBtn}>Skip ahead (demo)</button>
        </div>
      </div>
    </div>
  );
};

const PulseDot = () => (
  <div style={{ width: 8, height: 8, borderRadius: 4, background: "white",
                animation: "pulse 1.2s ease-in-out infinite" }} />
);

const RadialProgress = ({ value }) => {
  const r = 108;
  const c = 2 * Math.PI * r;
  return (
    <svg width="240" height="240" viewBox="0 0 240 240">
      <circle cx="120" cy="120" r={r} fill="none" stroke={C.panel} strokeWidth="14" />
      <circle cx="120" cy="120" r={r} fill="none" stroke={C.coral} strokeWidth="14"
              strokeDasharray={c} strokeDashoffset={c * (1 - value / 100)}
              strokeLinecap="round" transform="rotate(-90 120 120)"
              style={{ transition: "stroke-dashoffset 0.2s linear" }} />
    </svg>
  );
};

const ghostBtn = {
  padding: "8px 16px", borderRadius: 7,
  background: "transparent", border: `1px solid ${C.border}`,
  color: C.textDim, fontFamily: FONT_UI, fontSize: 13, cursor: "pointer",
};

// ============================================================
// EDITOR — the centerpiece
// ============================================================
const EDITOR_W = 1240; // approximate width of editor area when sidebar shown
const Editor = ({ project, rallies, setRallies, onExport }) => {
  const [t, setT] = useState(rallies[0]?.start ?? 0);
  const [playing, setPlaying] = useState(false);
  const [selected, setSelected] = useState(rallies[0]?.id || null);
  const [hover, setHover] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [history, setHistory] = useState([]);
  const [future, setFuture] = useState([]);
  const playRef = useRef(null);

  // play loop
  useEffect(() => {
    if (!playing) return;
    const start = performance.now();
    const tStart = t;
    const id = setInterval(() => {
      const elapsed = (performance.now() - start) / 1000;
      const newT = Math.min(MOCK_DURATION, tStart + elapsed);
      setT(newT);
      if (newT >= MOCK_DURATION) setPlaying(false);
    }, 33);
    return () => clearInterval(id);
  }, [playing]); // eslint-disable-line

  const pushHistory = useCallback((rs) => {
    setHistory((h) => [...h.slice(-49), rs]);
    setFuture([]);
  }, []);

  const updateRallies = useCallback((updater) => {
    setRallies((current) => {
      pushHistory(current);
      return typeof updater === "function" ? updater(current) : updater;
    });
  }, [setRallies, pushHistory]);

  const undo = () => {
    setHistory((h) => {
      if (!h.length) return h;
      const last = h[h.length - 1];
      setFuture((f) => [...f, rallies]);
      setRallies(last);
      return h.slice(0, -1);
    });
  };
  const redo = () => {
    setFuture((f) => {
      if (!f.length) return f;
      const next = f[f.length - 1];
      setHistory((h) => [...h, rallies]);
      setRallies(next);
      return f.slice(0, -1);
    });
  };

  const seekTo = (newT) => {
    setT(Math.max(0, Math.min(MOCK_DURATION, newT)));
  };

  const findRallyAt = (time) => rallies.find((r) => time >= r.start && time <= r.end);

  // Keyboard: I/O for in/out, Delete, Space, Z/Y for undo/redo, J/L
  useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
      if (e.key === " ") { e.preventDefault(); setPlaying((p) => !p); }
      else if (e.key === "i" || e.key === "I") {
        if (selected) {
          updateRallies((rs) => rs.map((r) => r.id === selected ? { ...r, start: Math.min(t, r.end - 0.5) } : r));
        }
      } else if (e.key === "o" || e.key === "O") {
        if (selected) {
          updateRallies((rs) => rs.map((r) => r.id === selected ? { ...r, end: Math.max(t, r.start + 0.5) } : r));
        }
      } else if (e.key === "Delete" || e.key === "Backspace") {
        if (selected) {
          updateRallies((rs) => rs.filter((r) => r.id !== selected));
          setSelected(null);
        }
      } else if (e.key === "ArrowLeft") { seekTo(t - (e.shiftKey ? 5 : 1)); }
      else if (e.key === "ArrowRight") { seekTo(t + (e.shiftKey ? 5 : 1)); }
      else if ((e.key === "z" || e.key === "Z") && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); e.shiftKey ? redo() : undo();
      } else if ((e.key === "y" || e.key === "Y") && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); redo();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected, t, rallies, updateRallies]); // eslint-disable-line

  const addRallyAt = () => {
    const dur = 12;
    const newR = {
      id: "r" + Date.now(),
      start: Math.max(0, t - dur / 2),
      end: Math.min(MOCK_DURATION, t + dur / 2),
      fp: false,
    };
    updateRallies((rs) => [...rs, newR].sort((a, b) => a.start - b.start));
    setSelected(newR.id);
  };

  const deleteSelected = () => {
    if (!selected) return;
    updateRallies((rs) => rs.filter((r) => r.id !== selected));
    setSelected(null);
  };

  const currentRally = findRallyAt(t);
  const totalRallyTime = rallies.reduce((acc, r) => acc + (r.end - r.start), 0);

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", background: C.bg, minWidth: 0, minHeight: 0 }}>
      <EditorTopBar
        project={project}
        rallies={rallies}
        totalRallyTime={totalRallyTime}
        onUndo={undo} onRedo={redo}
        canUndo={history.length > 0} canRedo={future.length > 0}
        onExport={onExport}
      />

      <div style={{ flex: 1, display: "flex", minHeight: 0, minWidth: 0 }}>
        {/* Center column: video + timeline */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, minHeight: 0 }}>
          <VideoPanel
            t={t} playing={playing}
            currentRally={currentRally}
            rallyIndex={currentRally ? rallies.findIndex((r) => r.id === currentRally.id) : -1}
            totalRallies={rallies.length}
          />
          <TransportBar
            t={t} playing={playing} setPlaying={setPlaying}
            seekTo={seekTo} rallies={rallies} selected={selected}
            setSelected={setSelected}
            onAdd={addRallyAt} onDelete={deleteSelected}
            zoom={zoom} setZoom={setZoom}
          />
          <Timeline
            t={t} setT={setT}
            rallies={rallies} updateRallies={updateRallies}
            selected={selected} setSelected={setSelected}
            hover={hover} setHover={setHover}
            zoom={zoom}
          />
        </div>

        {/* Right rail: rally list */}
        <RallyList
          rallies={rallies} selected={selected}
          onSelect={(r) => { setSelected(r.id); setT(r.start + 0.5); }}
          onToggleFp={(r) => updateRallies((rs) => rs.map((x) => x.id === r.id ? { ...x, fp: !x.fp } : x))}
          onDelete={(r) => updateRallies((rs) => rs.filter((x) => x.id !== r.id))}
          t={t}
        />
      </div>
    </div>
  );
};

// ---- Editor sub-components ----

const EditorTopBar = ({ project, rallies, totalRallyTime, onUndo, onRedo, canUndo, canRedo, onExport }) => {
  const kept = rallies.filter((r) => !r.fp).length;
  return (
    <div style={{
      height: 56, padding: "0 24px",
      borderBottom: `1px solid ${C.border}`,
      background: C.panelLo,
      display: "flex", alignItems: "center", gap: 16,
      flexShrink: 0,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
        <Icon d={ICONS.scissors} size={16} stroke={C.coral} />
        <div style={{ minWidth: 0 }}>
          <div style={{ fontFamily: FONT_UI, fontSize: 14, fontWeight: 600, color: C.text,
                        overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {project?.name || "Match"}
          </div>
          <div style={{ fontFamily: FONT_MONO, fontSize: 10, color: C.textMute, marginTop: 1 }}>
            {fmt(MOCK_DURATION)} source · {kept} rallies kept · {fmt(totalRallyTime)} active
          </div>
        </div>
      </div>

      <div style={{ flex: 1 }} />

      <div style={{ display: "flex", gap: 4 }}>
        <ToolBtn icon={ICONS.undo} disabled={!canUndo} onClick={onUndo} title="Undo (⌘Z)" />
        <ToolBtn icon={ICONS.redo} disabled={!canRedo} onClick={onRedo} title="Redo (⌘⇧Z)" />
      </div>

      <div style={{ width: 1, height: 24, background: C.border, margin: "0 6px" }} />

      <div style={{
        padding: "5px 10px", borderRadius: 6,
        background: C.panel, border: `1px solid ${C.border}`,
        fontFamily: FONT_MONO, fontSize: 11, color: C.textDim,
        display: "flex", gap: 8, alignItems: "center",
      }}>
        <span style={{ color: C.green }}>●</span>
        <span>auto-save</span>
      </div>

      <button onClick={onExport} style={{
        padding: "8px 16px", borderRadius: 7,
        background: C.coral, border: "none",
        color: "white", fontFamily: FONT_UI, fontSize: 13, fontWeight: 600,
        cursor: "pointer", display: "flex", alignItems: "center", gap: 6,
      }}>
        <Icon d={ICONS.download} size={14} w={2} />
        Export
      </button>
    </div>
  );
};

const ToolBtn = ({ icon, onClick, disabled, title, active }) => (
  <button onClick={onClick} disabled={disabled} title={title} style={{
    width: 32, height: 32, borderRadius: 6,
    background: active ? C.panelHi : "transparent",
    border: `1px solid ${active ? C.borderHi : "transparent"}`,
    color: disabled ? C.textMute : (active ? C.coral : C.textDim),
    cursor: disabled ? "not-allowed" : "pointer",
    display: "flex", alignItems: "center", justifyContent: "center",
    opacity: disabled ? 0.5 : 1,
    transition: "all 0.12s",
  }}
  onMouseEnter={(e) => { if (!disabled && !active) e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
  onMouseLeave={(e) => { if (!disabled && !active) e.currentTarget.style.background = "transparent"; }}>
    <Icon d={icon} size={15} />
  </button>
);

const VideoPanel = ({ t, playing, currentRally, rallyIndex, totalRallies }) => {
  return (
    <div style={{
      flex: 1, minHeight: 0,
      background: "#000",
      position: "relative",
      display: "flex", alignItems: "center", justifyContent: "center",
      overflow: "hidden",
    }}>
      <div style={{
        width: "100%", height: "100%",
        background: `repeating-linear-gradient(135deg, oklch(0.18 0.005 250), oklch(0.18 0.005 250) 12px, oklch(0.14 0.005 250) 12px, oklch(0.14 0.005 250) 24px)`,
        position: "relative",
      }}>
        {/* Court markings hint - centered text label */}
        <div style={{
          position: "absolute", inset: 0,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <div style={{
            fontFamily: FONT_MONO, fontSize: 11, color: C.textMute,
            background: "rgba(0,0,0,0.5)", padding: "5px 12px", borderRadius: 5,
            border: `1px solid ${C.border}`, letterSpacing: 0.6,
          }}>
            match footage · 1920×1080
          </div>
        </div>

        {/* Live overlays */}
        {currentRally && (
          <div style={{
            position: "absolute", top: 16, left: 16,
            display: "flex", gap: 8, alignItems: "center",
            padding: "6px 12px", borderRadius: 999,
            background: "rgba(0,0,0,0.6)",
            backdropFilter: "blur(8px)",
            border: `1px solid ${C.coral}`,
          }}>
            <div style={{ width: 6, height: 6, borderRadius: 3, background: C.coral,
                          animation: "pulse 1.4s ease-in-out infinite" }} />
            <span style={{ fontFamily: FONT_UI, fontSize: 11, color: C.text, fontWeight: 600,
                           letterSpacing: 0.5, textTransform: "uppercase" }}>
              Rally {rallyIndex + 1} of {totalRallies}
            </span>
            <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: C.textDim }}>
              {fmt(t - currentRally.start)} / {fmt(currentRally.end - currentRally.start)}
            </span>
          </div>
        )}
        {!currentRally && (
          <div style={{
            position: "absolute", top: 16, left: 16,
            padding: "6px 12px", borderRadius: 999,
            background: "rgba(0,0,0,0.6)",
            backdropFilter: "blur(8px)",
            border: `1px solid ${C.border}`,
            fontFamily: FONT_UI, fontSize: 11, color: C.textDim, fontWeight: 500,
          }}>
            Between rallies
          </div>
        )}

        {/* Time badge */}
        <div style={{
          position: "absolute", bottom: 16, right: 16,
          padding: "5px 10px", borderRadius: 5,
          background: "rgba(0,0,0,0.7)",
          fontFamily: FONT_MONO, fontSize: 12, color: C.text,
          letterSpacing: 0.5,
        }}>
          {fmtMs(t)}
        </div>
      </div>
    </div>
  );
};

const TransportBar = ({ t, playing, setPlaying, seekTo, rallies, selected, setSelected, onAdd, onDelete, zoom, setZoom }) => {
  const goToRally = (dir) => {
    const sorted = [...rallies].sort((a, b) => a.start - b.start);
    const idx = sorted.findIndex((r) => r.id === selected);
    let target;
    if (dir < 0) {
      target = sorted.slice(0, idx).reverse().find((r) => r.start < t) || sorted[Math.max(0, idx - 1)] || sorted[0];
    } else {
      target = sorted.find((r) => r.start > t) || sorted[Math.min(sorted.length - 1, idx + 1)] || sorted[sorted.length - 1];
    }
    if (target) {
      setSelected(target.id);
      seekTo(target.start + 0.2);
    }
  };

  return (
    <div style={{
      padding: "10px 16px",
      background: C.panel,
      borderTop: `1px solid ${C.border}`,
      borderBottom: `1px solid ${C.border}`,
      display: "flex", alignItems: "center", gap: 10,
      flexShrink: 0,
    }}>
      <div style={{ display: "flex", gap: 2 }}>
        <ToolBtn icon={ICONS.prev} onClick={() => goToRally(-1)} title="Previous rally" />
        <button onClick={() => setPlaying((p) => !p)} style={{
          width: 36, height: 36, borderRadius: 7,
          background: C.coral, border: "none",
          color: "white", cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          {playing ? <Icon d={null} size={14}>{ICONS.pause}</Icon> : <Icon d={ICONS.play} size={14} fill="white" stroke="white" />}
        </button>
        <ToolBtn icon={ICONS.next} onClick={() => goToRally(1)} title="Next rally" />
      </div>

      <div style={{
        padding: "6px 12px", borderRadius: 6,
        background: C.panelLo, border: `1px solid ${C.border}`,
        fontFamily: FONT_MONO, fontSize: 12, color: C.text,
        minWidth: 168, textAlign: "center", letterSpacing: 0.5,
      }}>
        {fmtMs(t)} <span style={{ color: C.textMute }}>/ {fmt(MOCK_DURATION)}</span>
      </div>

      <div style={{ flex: 1 }} />

      <div style={{ display: "flex", gap: 4 }}>
        <button onClick={onAdd} style={{
          padding: "7px 12px", borderRadius: 7,
          background: "transparent", border: `1px solid ${C.borderHi}`,
          color: C.text, fontFamily: FONT_UI, fontSize: 12, fontWeight: 500,
          cursor: "pointer", display: "flex", alignItems: "center", gap: 6,
        }}>
          <Icon d={ICONS.plus} size={13} w={2} />
          Add rally
        </button>
        <button onClick={onDelete} disabled={!selected} style={{
          padding: "7px 12px", borderRadius: 7,
          background: "transparent", border: `1px solid ${selected ? C.borderHi : C.border}`,
          color: selected ? C.text : C.textMute,
          fontFamily: FONT_UI, fontSize: 12, fontWeight: 500,
          cursor: selected ? "pointer" : "not-allowed",
          display: "flex", alignItems: "center", gap: 6,
          opacity: selected ? 1 : 0.5,
        }}>
          <Icon d={ICONS.trash} size={13} />
          Delete
        </button>
      </div>

      <div style={{ width: 1, height: 22, background: C.border, margin: "0 4px" }} />

      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontFamily: FONT_UI, fontSize: 11, color: C.textMute }}>Zoom</span>
        <input type="range" min="1" max="6" step="0.5" value={zoom}
               onChange={(e) => setZoom(parseFloat(e.target.value))}
               style={{ width: 80, accentColor: C.coral }} />
      </div>
    </div>
  );
};

// ---- Timeline ----
const TIMELINE_HEIGHT = 132;
const RULER_HEIGHT = 22;
const TRACK_HEIGHT = 60;

const Timeline = ({ t, setT, rallies, updateRallies, selected, setSelected, hover, setHover, zoom }) => {
  const containerRef = useRef(null);
  const [drag, setDrag] = useState(null); // { type: 'playhead' | 'start' | 'end' | 'block', id?, t0, x0 }
  const [scrollX, setScrollX] = useState(0);
  const [containerW, setContainerW] = useState(1000);

  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      setContainerW(entries[0].contentRect.width);
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  const totalW = containerW * zoom;
  const xToT = (x) => Math.max(0, Math.min(MOCK_DURATION, ((x + scrollX) / totalW) * MOCK_DURATION));
  const tToX = (time) => (time / MOCK_DURATION) * totalW - scrollX;

  // Auto-scroll to keep playhead visible
  useEffect(() => {
    const px = tToX(t);
    if (px < 80) setScrollX((s) => Math.max(0, s - 80));
    else if (px > containerW - 80) setScrollX((s) => Math.min(totalW - containerW, s + 80));
  }, [t]); // eslint-disable-line

  const onPointerDown = (e, info) => {
    e.preventDefault();
    setDrag({ ...info, x0: e.clientX, t0: t, scrollX0: scrollX });
    if (info.type === "rallyStart" || info.type === "rallyEnd" || info.type === "block") {
      setSelected(info.id);
    }
    if (info.type === "scrub") {
      const rect = containerRef.current.getBoundingClientRect();
      const newT = xToT(e.clientX - rect.left);
      setT(newT);
    }
  };

  useEffect(() => {
    if (!drag) return;
    const onMove = (e) => {
      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const newT = xToT(x);
      const dx = e.clientX - drag.x0;
      const dt = (dx / totalW) * MOCK_DURATION;

      if (drag.type === "scrub" || drag.type === "playhead") {
        setT(newT);
      } else if (drag.type === "rallyStart") {
        updateRallies((rs) => rs.map((r) => {
          if (r.id !== drag.id) return r;
          const ns = Math.max(0, Math.min(r.end - 0.5, drag.origStart + dt));
          return { ...r, start: ns };
        }));
      } else if (drag.type === "rallyEnd") {
        updateRallies((rs) => rs.map((r) => {
          if (r.id !== drag.id) return r;
          const ne = Math.max(r.start + 0.5, Math.min(MOCK_DURATION, drag.origEnd + dt));
          return { ...r, end: ne };
        }));
      } else if (drag.type === "block") {
        updateRallies((rs) => rs.map((r) => {
          if (r.id !== drag.id) return r;
          const dur = drag.origEnd - drag.origStart;
          let ns = Math.max(0, Math.min(MOCK_DURATION - dur, drag.origStart + dt));
          return { ...r, start: ns, end: ns + dur };
        }));
      }
    };
    const onUp = () => setDrag(null);
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
  }, [drag, totalW, updateRallies]); // eslint-disable-line

  // Keyboard: arrow on selected rally to move
  // (top-level keyboard handles already)

  // Build minimap segments
  const minimapHeight = 16;

  // Ruler ticks
  const tickEvery = (() => {
    const targetTicks = 14;
    const candidates = [10, 30, 60, 120, 300, 600];
    const visibleSec = MOCK_DURATION;
    for (const c of candidates) {
      if (visibleSec / c <= targetTicks * zoom) return c;
    }
    return 600;
  })();
  const ticks = [];
  for (let s = 0; s <= MOCK_DURATION; s += tickEvery) ticks.push(s);

  return (
    <div style={{
      background: C.panel,
      borderTop: `1px solid ${C.border}`,
      flexShrink: 0,
      paddingBottom: 4,
    }}>
      {/* Minimap */}
      <div style={{
        height: minimapHeight + 8, padding: "4px 16px",
        display: "flex", alignItems: "center", gap: 8,
        borderBottom: `1px solid ${C.panelLo}`,
      }}>
        <div style={{ flex: 1, height: minimapHeight, position: "relative",
                      background: C.panelLo, borderRadius: 3, overflow: "hidden",
                      border: `1px solid ${C.border}` }}>
          {rallies.map((r) => (
            <div key={r.id} style={{
              position: "absolute", top: 0, bottom: 0,
              left: `${(r.start / MOCK_DURATION) * 100}%`,
              width: `${((r.end - r.start) / MOCK_DURATION) * 100}%`,
              background: r.fp ? C.textMute : C.coral, opacity: r.fp ? 0.3 : 0.85,
            }} />
          ))}
          {/* Visible window indicator */}
          {zoom > 1 && (
            <div style={{
              position: "absolute", top: -1, bottom: -1,
              left: `${(scrollX / totalW) * 100}%`,
              width: `${(containerW / totalW) * 100}%`,
              background: "rgba(255,255,255,0.06)",
              border: `1px solid ${C.text}`,
              borderRadius: 2,
              pointerEvents: "none",
            }} />
          )}
          {/* Playhead */}
          <div style={{
            position: "absolute", top: -2, bottom: -2,
            left: `${(t / MOCK_DURATION) * 100}%`,
            width: 1.5, background: C.text, pointerEvents: "none",
          }} />
        </div>
      </div>

      {/* Main timeline */}
      <div ref={containerRef} style={{
        position: "relative",
        height: TIMELINE_HEIGHT,
        overflow: "hidden",
        cursor: drag ? "grabbing" : "default",
        userSelect: "none",
      }}
      onWheel={(e) => {
        if (zoom > 1) {
          e.preventDefault();
          setScrollX((s) => Math.max(0, Math.min(totalW - containerW, s + e.deltaX || e.deltaY)));
        }
      }}>
        {/* Ruler */}
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0, height: RULER_HEIGHT,
          borderBottom: `1px solid ${C.border}`,
          background: C.panelLo,
        }}
        onPointerDown={(e) => onPointerDown(e, { type: "scrub" })}>
          <div style={{ position: "absolute", inset: 0, transform: `translateX(${-scrollX}px)`, width: totalW }}>
            {ticks.map((s) => (
              <div key={s} style={{
                position: "absolute", left: (s / MOCK_DURATION) * totalW,
                top: 0, bottom: 0, paddingLeft: 5,
                fontFamily: FONT_MONO, fontSize: 10, color: C.textMute,
                lineHeight: `${RULER_HEIGHT}px`,
                borderLeft: `1px solid ${C.border}`,
              }}>{fmt(s)}</div>
            ))}
          </div>
        </div>

        {/* Track area */}
        <div style={{
          position: "absolute", top: RULER_HEIGHT, left: 0, right: 0, bottom: 0,
        }}
        onPointerDown={(e) => {
          // click on empty area = scrub
          if (e.target === e.currentTarget) {
            onPointerDown(e, { type: "scrub" });
          }
        }}>
          {/* Track lane */}
          <div style={{ position: "absolute", inset: "16px 0 16px 0",
                        background: C.panelLo, borderTop: `1px solid ${C.border}`,
                        borderBottom: `1px solid ${C.border}` }} />

          {/* Faint grid lines */}
          <div style={{ position: "absolute", inset: 0, transform: `translateX(${-scrollX}px)`, width: totalW, pointerEvents: "none" }}>
            {ticks.map((s) => (
              <div key={s} style={{
                position: "absolute", left: (s / MOCK_DURATION) * totalW,
                top: 0, bottom: 0, width: 1, background: C.border, opacity: 0.4,
              }} />
            ))}
          </div>

          {/* Rally blocks */}
          <div style={{ position: "absolute", inset: 0, transform: `translateX(${-scrollX}px)`, width: totalW }}>
            {rallies.map((r, i) => {
              const x = (r.start / MOCK_DURATION) * totalW;
              const w = ((r.end - r.start) / MOCK_DURATION) * totalW;
              const isSel = selected === r.id;
              const isHover = hover === r.id;
              return (
                <RallyBlock key={r.id}
                  rally={r} index={i + 1}
                  x={x} w={w}
                  selected={isSel} hovered={isHover}
                  onPointerDown={onPointerDown}
                  onMouseEnter={() => setHover(r.id)}
                  onMouseLeave={() => setHover(null)}
                />
              );
            })}
          </div>

          {/* Playhead */}
          <div style={{
            position: "absolute", top: 0, bottom: 0,
            left: tToX(t),
            width: 0, pointerEvents: "none",
            zIndex: 5,
          }}>
            <div style={{
              position: "absolute", top: -RULER_HEIGHT, bottom: 0, width: 2,
              left: -1,
              background: C.text,
              boxShadow: `0 0 8px rgba(255,255,255,0.4)`,
            }} />
            <div style={{
              position: "absolute", top: -RULER_HEIGHT - 2, left: -7, width: 14, height: 14,
              clipPath: "polygon(0 0, 100% 0, 50% 100%)",
              background: C.text,
            }} />
          </div>
        </div>
      </div>
    </div>
  );
};

const RallyBlock = ({ rally, index, x, w, selected, hovered, onPointerDown, onMouseEnter, onMouseLeave }) => {
  const fp = rally.fp;
  const accent = fp ? C.textMute : C.coral;
  const fill = fp
    ? `linear-gradient(180deg, oklch(0.4 0.005 250 / 0.5), oklch(0.34 0.005 250 / 0.5))`
    : selected
      ? `linear-gradient(180deg, ${C.rallySelectedFill}, ${C.coralDim})`
      : hovered
        ? `linear-gradient(180deg, ${C.rallyHover}, ${C.coralDim})`
        : `linear-gradient(180deg, ${C.coral}, ${C.coralDim})`;

  return (
    <div
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onPointerDown={(e) => {
        if (e.target.dataset.handle) return;
        onPointerDown(e, {
          type: "block", id: rally.id,
          origStart: rally.start, origEnd: rally.end,
        });
      }}
      style={{
        position: "absolute",
        left: x, width: Math.max(8, w),
        top: 18, height: TRACK_HEIGHT,
        background: fill,
        borderRadius: 6,
        cursor: "grab",
        boxShadow: selected
          ? `0 0 0 2px ${C.text}, 0 4px 16px -4px ${accent}`
          : (fp ? "none" : `0 2px 8px -2px ${C.coralDim}`),
        opacity: fp ? 0.55 : 1,
        overflow: "hidden",
        display: "flex", alignItems: "center",
        transition: "box-shadow 0.12s",
      }}>
      {/* Resize handles */}
      <div data-handle="start"
        onPointerDown={(e) => { e.stopPropagation(); onPointerDown(e, {
          type: "rallyStart", id: rally.id, origStart: rally.start, origEnd: rally.end }); }}
        style={{
          position: "absolute", left: 0, top: 0, bottom: 0, width: 8,
          cursor: "ew-resize",
          background: selected || hovered ? "rgba(255,255,255,0.25)" : "transparent",
          borderLeft: `2px solid ${selected ? C.text : "transparent"}`,
        }} />
      <div data-handle="end"
        onPointerDown={(e) => { e.stopPropagation(); onPointerDown(e, {
          type: "rallyEnd", id: rally.id, origStart: rally.start, origEnd: rally.end }); }}
        style={{
          position: "absolute", right: 0, top: 0, bottom: 0, width: 8,
          cursor: "ew-resize",
          background: selected || hovered ? "rgba(255,255,255,0.25)" : "transparent",
          borderRight: `2px solid ${selected ? C.text : "transparent"}`,
        }} />

      {/* Mini waveform-ish accent bars to give blocks texture */}
      <div style={{ position: "absolute", left: 8, right: 8, top: 8, bottom: 8,
                    display: "flex", alignItems: "flex-end", gap: 2, opacity: 0.35,
                    pointerEvents: "none" }}>
        {Array.from({ length: Math.max(6, Math.floor(w / 6)) }).map((_, i) => (
          <div key={i} style={{
            flex: 1, background: "white",
            height: `${20 + Math.abs(Math.sin(i * 1.7 + rally.start)) * 60}%`,
            borderRadius: 1,
            minWidth: 1.5,
          }} />
        ))}
      </div>

      {/* Label */}
      {w > 40 && (
        <div style={{
          position: "relative", padding: "0 14px",
          fontFamily: FONT_UI, fontSize: 11, color: "white", fontWeight: 600,
          textShadow: "0 1px 2px rgba(0,0,0,0.4)",
          display: "flex", alignItems: "center", gap: 8,
          pointerEvents: "none",
          letterSpacing: 0.2,
        }}>
          <span>Rally {index}</span>
          {w > 110 && (
            <span style={{ fontFamily: FONT_MONO, fontSize: 10, opacity: 0.85, fontWeight: 500 }}>
              {fmt(rally.end - rally.start)}
            </span>
          )}
          {fp && w > 130 && (
            <span style={{ fontSize: 9, padding: "2px 5px", borderRadius: 3,
                           background: "rgba(0,0,0,0.4)", letterSpacing: 0.5,
                           textTransform: "uppercase" }}>skipped</span>
          )}
        </div>
      )}
    </div>
  );
};

// ---- Rally list ----
const RallyList = ({ rallies, selected, onSelect, onToggleFp, onDelete, t }) => {
  const [filter, setFilter] = useState("all"); // all | kept | skipped
  const filtered = rallies.filter((r) => {
    if (filter === "kept") return !r.fp;
    if (filter === "skipped") return r.fp;
    return true;
  });
  const listRef = useRef(null);
  const itemRefs = useRef({});

  useEffect(() => {
    if (selected && itemRefs.current[selected]) {
      const el = itemRefs.current[selected];
      const parent = listRef.current;
      if (!parent) return;
      const elTop = el.offsetTop;
      const elBot = elTop + el.offsetHeight;
      if (elTop < parent.scrollTop || elBot > parent.scrollTop + parent.clientHeight) {
        parent.scrollTo({ top: elTop - 40, behavior: "smooth" });
      }
    }
  }, [selected]);

  return (
    <div style={{
      width: 320,
      borderLeft: `1px solid ${C.border}`,
      background: C.panelLo,
      display: "flex", flexDirection: "column",
      flexShrink: 0,
    }}>
      <div style={{
        padding: "14px 16px 10px",
        borderBottom: `1px solid ${C.border}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <Icon d={ICONS.flag} size={14} stroke={C.coral} />
          <div style={{ fontFamily: FONT_UI, fontSize: 13, fontWeight: 600, color: C.text }}>
            Rallies
          </div>
          <div style={{
            padding: "2px 7px", borderRadius: 4,
            background: C.panel, fontFamily: FONT_MONO, fontSize: 10, color: C.textDim,
          }}>{rallies.length}</div>
          <div style={{ flex: 1 }} />
        </div>

        <div style={{
          display: "flex",
          background: C.panel, borderRadius: 7, padding: 3,
          border: `1px solid ${C.border}`,
        }}>
          {[
            ["all", "All", rallies.length],
            ["kept", "Kept", rallies.filter((r) => !r.fp).length],
            ["skipped", "Skipped", rallies.filter((r) => r.fp).length],
          ].map(([k, label, n]) => (
            <button key={k} onClick={() => setFilter(k)} style={{
              flex: 1, padding: "5px 8px", borderRadius: 5,
              background: filter === k ? C.panelHi : "transparent",
              border: "none", color: filter === k ? C.text : C.textDim,
              fontFamily: FONT_UI, fontSize: 11, fontWeight: 500, cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center", gap: 5,
            }}>
              {label}
              <span style={{ fontFamily: FONT_MONO, fontSize: 9, color: C.textMute, opacity: 0.8 }}>{n}</span>
            </button>
          ))}
        </div>
      </div>

      <div ref={listRef} style={{ flex: 1, overflowY: "auto", padding: "4px 0" }}>
        {filtered.map((r, i) => {
          const isSel = selected === r.id;
          const isPlaying = t >= r.start && t <= r.end;
          const idx = rallies.findIndex((x) => x.id === r.id) + 1;
          return (
            <div key={r.id}
              ref={(el) => (itemRefs.current[r.id] = el)}
              onClick={() => onSelect(r)}
              style={{
                margin: "2px 8px",
                padding: "10px 12px",
                background: isSel ? C.panelHi : "transparent",
                border: `1px solid ${isSel ? C.borderHi : "transparent"}`,
                borderLeft: `3px solid ${r.fp ? C.textMute : (isPlaying ? C.green : C.coral)}`,
                borderRadius: 7,
                cursor: "pointer",
                opacity: r.fp ? 0.55 : 1,
                transition: "background 0.12s",
              }}
              onMouseEnter={(e) => { if (!isSel) e.currentTarget.style.background = "rgba(255,255,255,0.025)"; }}
              onMouseLeave={(e) => { if (!isSel) e.currentTarget.style.background = "transparent"; }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                  fontFamily: FONT_MONO, fontSize: 11, color: C.textDim,
                  width: 22, textAlign: "right", letterSpacing: 0.5,
                }}>#{String(idx).padStart(2, "0")}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: FONT_UI, fontSize: 12, color: C.text, fontWeight: 500,
                                textDecoration: r.fp ? "line-through" : "none" }}>
                    Rally {idx}
                    {isPlaying && (
                      <span style={{ marginLeft: 8, padding: "1px 6px", borderRadius: 3,
                                     background: C.green, color: "black",
                                     fontSize: 9, fontWeight: 700, letterSpacing: 0.5,
                                     textTransform: "uppercase" }}>now</span>
                    )}
                  </div>
                  <div style={{ display: "flex", gap: 8, marginTop: 2,
                                fontFamily: FONT_MONO, fontSize: 10, color: C.textMute }}>
                    <span>{fmt(r.start)} → {fmt(r.end)}</span>
                    <span style={{ color: C.textDim }}>· {fmt(r.end - r.start)}</span>
                  </div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); onToggleFp(r); }}
                  title={r.fp ? "Restore" : "Skip"}
                  style={{
                    width: 24, height: 24, borderRadius: 5,
                    background: "transparent", border: `1px solid ${C.border}`,
                    color: C.textDim, cursor: "pointer",
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                  <Icon d={r.fp ? ICONS.refresh : ICONS.close} size={11} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ padding: "10px 14px", borderTop: `1px solid ${C.border}`,
                    background: C.panel, fontFamily: FONT_UI, fontSize: 11, color: C.textMute }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 12px", lineHeight: 1.5 }}>
          <span><kbd style={kbdStyle}>Space</kbd> play</span>
          <span><kbd style={kbdStyle}>I</kbd> set in</span>
          <span><kbd style={kbdStyle}>O</kbd> set out</span>
          <span><kbd style={kbdStyle}>⌫</kbd> delete</span>
          <span><kbd style={kbdStyle}>⌘Z</kbd> undo</span>
        </div>
      </div>
    </div>
  );
};

const kbdStyle = {
  fontFamily: FONT_MONO, fontSize: 10,
  padding: "1px 5px", borderRadius: 3,
  background: C.panelHi, border: `1px solid ${C.border}`,
  color: C.textDim,
  marginRight: 2,
};

// ============================================================
// Stats screen — coming soon
// ============================================================
const StatsScreen = () => (
  <div style={{ flex: 1, display: "flex", flexDirection: "column", background: C.bg, overflow: "auto" }}>
    <ScreenHeader
      title="Stats"
      sub="Per-player action counts and ball-contact heatmaps"
      right={<span style={{
        padding: "5px 10px", borderRadius: 999,
        background: C.coralSoft, color: C.coral,
        fontFamily: FONT_UI, fontSize: 10, fontWeight: 700,
        letterSpacing: 1, textTransform: "uppercase",
      }}>Coming soon</span>}
    />
    <div style={{ padding: "8px 36px 36px", display: "grid", gap: 16,
                  gridTemplateColumns: "1.4fr 1fr" }}>
      {/* Heatmap preview */}
      <div style={{
        background: C.panel, border: `1px solid ${C.border}`,
        borderRadius: 12, padding: 20,
      }}>
        <div style={{ fontFamily: FONT_UI, fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 4 }}>
          Ball contact heatmap
        </div>
        <div style={{ fontFamily: FONT_UI, fontSize: 11, color: C.textMute, marginBottom: 16 }}>
          Where on the court the ball is touched. Brighter = more contacts.
        </div>
        <CourtHeatmap />
      </div>

      {/* Action counts table */}
      <div style={{
        background: C.panel, border: `1px solid ${C.border}`,
        borderRadius: 12, padding: 20,
      }}>
        <div style={{ fontFamily: FONT_UI, fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 4 }}>
          Action counts
        </div>
        <div style={{ fontFamily: FONT_UI, fontSize: 11, color: C.textMute, marginBottom: 16 }}>
          Tag track IDs with player names to make this readable.
        </div>
        <div style={{ filter: "blur(2px)", opacity: 0.7, pointerEvents: "none" }}>
          <ActionTable />
        </div>
      </div>

      <div style={{
        gridColumn: "1 / -1",
        background: `linear-gradient(135deg, ${C.panelLo}, ${C.panel})`,
        border: `1px dashed ${C.borderHi}`,
        borderRadius: 12, padding: 22,
        display: "flex", alignItems: "center", gap: 18,
      }}>
        <div style={{ width: 42, height: 42, borderRadius: 10, background: C.panelHi,
                      display: "flex", alignItems: "center", justifyContent: "center", color: C.coral }}>
          <Icon d={ICONS.zap} size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: FONT_UI, fontSize: 14, fontWeight: 600, color: C.text }}>
            Stats land in the next release
          </div>
          <div style={{ fontFamily: FONT_UI, fontSize: 12, color: C.textDim, marginTop: 2 }}>
            We're training a per-player action classifier (serve, receive, set, attack, block).
            Once shipped, every match you process gets a sidecar of stats — no extra steps.
          </div>
        </div>
      </div>
    </div>
  </div>
);

const CourtHeatmap = () => {
  // Soft court diagram + a few heat blobs
  return (
    <div style={{ aspectRatio: "2 / 1", background: C.panelLo, borderRadius: 10,
                  border: `1px solid ${C.border}`, position: "relative", overflow: "hidden" }}>
      {/* Court lines */}
      <svg viewBox="0 0 200 100" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <rect x="10" y="14" width="180" height="72" fill="none" stroke={C.borderHi} strokeWidth="0.6" />
        <line x1="100" y1="14" x2="100" y2="86" stroke={C.borderHi} strokeWidth="0.6" />
        <line x1="70" y1="14" x2="70" y2="86" stroke={C.border} strokeWidth="0.4" strokeDasharray="2 2" />
        <line x1="130" y1="14" x2="130" y2="86" stroke={C.border} strokeWidth="0.4" strokeDasharray="2 2" />
      </svg>
      {/* Heat blobs */}
      {[
        [50, 30, 30, 0.8], [60, 70, 26, 0.6], [140, 35, 32, 0.7], [150, 65, 28, 0.5],
        [80, 50, 22, 0.4], [120, 50, 22, 0.4], [40, 50, 18, 0.3], [160, 50, 18, 0.3],
      ].map(([x, y, r, op], i) => (
        <div key={i} style={{
          position: "absolute",
          left: `calc(${x / 2}% - ${r / 2}px)`,
          top: `calc(${y}% - ${r / 2}px)`,
          width: r, height: r, borderRadius: "50%",
          background: `radial-gradient(circle, ${C.coral} 0%, transparent 70%)`,
          opacity: op, mixBlendMode: "screen",
        }} />
      ))}
    </div>
  );
};

const ActionTable = () => {
  const rows = [
    ["Track 03", 4, 6, 12, 8, 1],
    ["Track 07", 0, 11, 2, 14, 3],
    ["Track 11", 8, 4, 1, 0, 0],
    ["Track 14", 1, 9, 3, 10, 2],
    ["Track 22", 3, 7, 14, 6, 0],
    ["Track 28", 0, 5, 1, 9, 4],
  ];
  return (
    <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: FONT_UI, fontSize: 12 }}>
      <thead>
        <tr style={{ color: C.textMute, fontSize: 10, textTransform: "uppercase", letterSpacing: 0.8 }}>
          <th style={{ textAlign: "left", padding: "8px 6px", fontWeight: 600 }}>Player</th>
          <th style={th}>Serve</th><th style={th}>Receive</th><th style={th}>Set</th><th style={th}>Attack</th><th style={th}>Block</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r[0]} style={{ borderTop: `1px solid ${C.border}` }}>
            <td style={{ padding: "8px 6px", color: C.text }}>{r[0]}</td>
            {r.slice(1).map((v, i) => (
              <td key={i} style={{ padding: "8px 6px", color: v > 8 ? C.coral : C.textDim, textAlign: "right",
                                   fontFamily: FONT_MONO, fontWeight: v > 8 ? 600 : 400 }}>{v}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};
const th = { textAlign: "right", padding: "8px 6px", fontWeight: 600 };

// ============================================================
// Export screen
// ============================================================
const ExportScreen = ({ rallies, project, onBack }) => {
  const [format, setFormat] = useState("mp4");
  const [includeBetween, setIncludeBetween] = useState(false);
  const [crossfade, setCrossfade] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [pct, setPct] = useState(0);
  const [done, setDone] = useState(false);

  const kept = rallies.filter((r) => !r.fp);
  const totalDur = kept.reduce((a, r) => a + (r.end - r.start), 0);

  const startExport = () => {
    setExporting(true);
    setPct(0);
    const t = setInterval(() => {
      setPct((p) => {
        const n = p + 3 + Math.random() * 4;
        if (n >= 100) {
          clearInterval(t);
          setExporting(false);
          setDone(true);
          return 100;
        }
        return n;
      });
    }, 100);
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", background: C.bg, overflow: "auto" }}>
      <ScreenHeader
        title="Export"
        sub={`${kept.length} rallies · ${fmt(totalDur)} of cleaned-up gameplay`}
      />
      <div style={{ padding: "8px 36px 36px", display: "grid", gap: 18, gridTemplateColumns: "1fr 360px", alignItems: "start" }}>
        {/* Left: options */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <Card title="Format">
            <Radio name="fmt" value="mp4" current={format} onChange={setFormat}
                   label="Single MP4 — rallies only" sub="Best for sharing. Stream-copies your source — fast and lossless." />
            <Radio name="fmt" value="folder" current={format} onChange={setFormat}
                   label="Folder of clips" sub="One file per rally. Useful for highlights or per-clip review." />
            <Radio name="fmt" value="markers" current={format} onChange={setFormat}
                   label="Original + chapter markers" sub="Keep your source intact. Open in any modern player to jump rallies." />
          </Card>

          <Card title="Options">
            <Toggle checked={includeBetween} onChange={setIncludeBetween}
                    label="Include 1.5s pre-roll & post-roll" sub="A bit of breathing room around each rally." />
            <Toggle checked={crossfade} onChange={setCrossfade}
                    label="Crossfade between rallies" sub="Smooth dissolves instead of hard cuts." />
            <Toggle checked={false} onChange={() => {}}
                    label="Burn rally numbers into video" sub="Useful for shared clips so timestamps make sense." />
          </Card>

          <Card title="Where to save">
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <div style={{ flex: 1, padding: "10px 12px", background: C.panelLo,
                            border: `1px solid ${C.border}`, borderRadius: 7,
                            fontFamily: FONT_MONO, fontSize: 12, color: C.textDim,
                            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                ~/Videos/DigDeep/{(project?.name || "match").replace(/\s+/g, "_")}_rallies.mp4
              </div>
              <button style={{ ...ghostBtn, padding: "8px 14px" }}>
                <Icon d={ICONS.folder} size={13} />
              </button>
            </div>
          </Card>
        </div>

        {/* Right: summary */}
        <div style={{
          background: C.panel, border: `1px solid ${C.border}`,
          borderRadius: 12, padding: 20,
          position: "sticky", top: 16,
        }}>
          <div style={{ fontFamily: FONT_UI, fontSize: 12, fontWeight: 600, color: C.textMute,
                        letterSpacing: 1, textTransform: "uppercase", marginBottom: 14 }}>Summary</div>

          <Stat label="Source duration" value={fmt(MOCK_DURATION)} />
          <Stat label="Rallies kept" value={`${kept.length} / ${rallies.length}`} />
          <Stat label="Output duration" value={fmt(totalDur)} accent />
          <Stat label="Time saved" value={fmt(MOCK_DURATION - totalDur)} />
          <Stat label="Estimated size" value="≈ 480 MB" />

          {!exporting && !done && (
            <button onClick={startExport} style={{
              width: "100%", marginTop: 16,
              padding: "10px", borderRadius: 8,
              background: C.coral, border: "none", color: "white",
              fontFamily: FONT_UI, fontSize: 13, fontWeight: 600,
              cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
            }}>
              <Icon d={ICONS.download} size={14} w={2} />
              Export {kept.length} rallies
            </button>
          )}
          {exporting && (
            <div style={{ marginTop: 16 }}>
              <div style={{ height: 6, background: C.panelLo, borderRadius: 3, overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${pct}%`, background: C.coral }} />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8,
                            fontFamily: FONT_MONO, fontSize: 11, color: C.textDim }}>
                <span>Cutting clips with ffmpeg…</span>
                <span>{Math.floor(pct)}%</span>
              </div>
            </div>
          )}
          {done && (
            <div style={{ marginTop: 16, padding: 14, borderRadius: 8,
                          background: `oklch(0.78 0.13 165 / 0.1)`,
                          border: `1px solid ${C.green}`,
                          display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ width: 28, height: 28, borderRadius: 14, background: C.green,
                            display: "flex", alignItems: "center", justifyContent: "center", color: "black" }}>
                <Icon d={ICONS.check} size={14} w={2.5} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: FONT_UI, fontSize: 13, fontWeight: 600, color: C.text }}>
                  Export complete
                </div>
                <div style={{ fontFamily: FONT_UI, fontSize: 11, color: C.textDim }}>
                  Saved · click to reveal in Files
                </div>
              </div>
              <button style={{ ...iconBtn, color: C.text }}>
                <Icon d={ICONS.external} size={12} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const Card = ({ title, children }) => (
  <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 12, overflow: "hidden" }}>
    <div style={{ padding: "14px 18px 4px", fontFamily: FONT_UI, fontSize: 12, fontWeight: 600,
                  color: C.textMute, letterSpacing: 1, textTransform: "uppercase" }}>{title}</div>
    <div style={{ padding: "8px 8px 12px" }}>
      {children}
    </div>
  </div>
);

const Radio = ({ name, value, current, onChange, label, sub }) => (
  <label style={{
    display: "flex", gap: 12, alignItems: "flex-start",
    padding: "10px 12px", borderRadius: 8, cursor: "pointer",
    background: current === value ? C.panelHi : "transparent",
    border: `1px solid ${current === value ? C.borderHi : "transparent"}`,
    transition: "background 0.12s",
  }}>
    <input type="radio" name={name} checked={current === value}
           onChange={() => onChange(value)}
           style={{ marginTop: 3, accentColor: C.coral }} />
    <div>
      <div style={{ fontFamily: FONT_UI, fontSize: 13, color: C.text, fontWeight: 500 }}>{label}</div>
      <div style={{ fontFamily: FONT_UI, fontSize: 11, color: C.textDim, marginTop: 1 }}>{sub}</div>
    </div>
  </label>
);

const Toggle = ({ checked, onChange, label, sub }) => (
  <label style={{
    display: "flex", gap: 12, alignItems: "center",
    padding: "10px 12px", cursor: "pointer", borderRadius: 8,
  }}>
    <div style={{ flex: 1 }}>
      <div style={{ fontFamily: FONT_UI, fontSize: 13, color: C.text, fontWeight: 500 }}>{label}</div>
      <div style={{ fontFamily: FONT_UI, fontSize: 11, color: C.textDim, marginTop: 1 }}>{sub}</div>
    </div>
    <div onClick={() => onChange(!checked)} style={{
      width: 32, height: 18, borderRadius: 999,
      background: checked ? C.coral : C.panelHi,
      border: `1px solid ${checked ? C.coral : C.border}`,
      position: "relative", transition: "background 0.15s",
    }}>
      <div style={{
        position: "absolute", top: 1, left: checked ? 15 : 1,
        width: 14, height: 14, borderRadius: 7,
        background: "white",
        transition: "left 0.15s",
      }} />
    </div>
  </label>
);

const Stat = ({ label, value, accent }) => (
  <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between",
                padding: "8px 0", borderBottom: `1px solid ${C.border}` }}>
    <span style={{ fontFamily: FONT_UI, fontSize: 12, color: C.textDim }}>{label}</span>
    <span style={{
      fontFamily: FONT_MONO, fontSize: accent ? 15 : 13,
      color: accent ? C.coral : C.text, fontWeight: accent ? 600 : 500,
    }}>{value}</span>
  </div>
);

// ============================================================
// Settings screen
// ============================================================
const SettingsScreen = () => {
  const [downloading, setDownloading] = useState(false);
  const [pct, setPct] = useState(72);
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", background: C.bg, overflow: "auto" }}>
      <ScreenHeader title="Settings" sub="Preferences and model versions" />
      <div style={{ padding: "8px 36px 36px", display: "flex", flexDirection: "column", gap: 16, maxWidth: 760 }}>

        <Card title="Models">
          <div style={{ padding: "0 8px" }}>
            <ModelRow name="Ball detector" file="VballNetFastV1 · v0.1" size="14 MB"
                      status="installed" />
            <ModelRow name="Player detector" file="RF-DETR Base · v0.1" size="142 MB"
                      status="installed" />
            <ModelRow name="Action classifier" file="VideoMAE-S · pending"
                      size="—" status="pending" note="Ships with v0.2 stats release" />
          </div>
          <div style={{ padding: "12px 12px 4px" }}>
            <button onClick={() => { setDownloading(true); }}
              style={{ ...ghostBtn, color: C.coral, borderColor: C.coral }}>
              <Icon d={ICONS.refresh} size={13} stroke={C.coral} style={{ marginRight: 6, verticalAlign: -2 }} />
              Check for model updates
            </button>
          </div>
        </Card>

        <Card title="Performance">
          <SettingRow label="Compute device" value="CUDA · NVIDIA RTX 4070" badge="auto" />
          <SettingRow label="Inference batch size" value="8 frames" />
          <SettingRow label="Cache directory" value="~/.cache/digdeep/" />
        </Card>

        <Card title="About">
          <SettingRow label="DigDeep" value="v0.1.0" />
          <SettingRow label="License" value="AGPL-3.0" />
          <SettingRow label="Source" value="github.com/yourname/digdeep" link />
        </Card>

      </div>
    </div>
  );
};

const ModelRow = ({ name, file, size, status, note }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 14,
                padding: "12px 8px", borderTop: `1px solid ${C.border}`,
                ":first-child": { borderTop: "none" } }}>
    <div style={{
      width: 32, height: 32, borderRadius: 7,
      background: C.panelLo, border: `1px solid ${C.border}`,
      display: "flex", alignItems: "center", justifyContent: "center",
      color: status === "installed" ? C.green : C.textMute,
    }}>
      <Icon d={status === "installed" ? ICONS.check : ICONS.clock} size={14} w={2.4} />
    </div>
    <div style={{ flex: 1 }}>
      <div style={{ fontFamily: FONT_UI, fontSize: 13, color: C.text, fontWeight: 500 }}>{name}</div>
      <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: C.textDim, marginTop: 1 }}>
        {file} {size !== "—" && <span style={{ color: C.textMute }}>· {size}</span>}
      </div>
      {note && <div style={{ fontFamily: FONT_UI, fontSize: 11, color: C.textMute, marginTop: 2 }}>{note}</div>}
    </div>
    <div style={{
      padding: "3px 8px", borderRadius: 999,
      background: status === "installed" ? `oklch(0.78 0.13 165 / 0.12)` : C.panelLo,
      color: status === "installed" ? C.green : C.textMute,
      fontFamily: FONT_UI, fontSize: 10, fontWeight: 600,
      letterSpacing: 0.6, textTransform: "uppercase",
      border: `1px solid ${status === "installed" ? C.green : C.border}`,
    }}>{status === "installed" ? "Installed" : "Pending"}</div>
  </div>
);

const SettingRow = ({ label, value, badge, link }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 14,
                padding: "10px 12px", borderTop: `1px solid ${C.border}` }}>
    <div style={{ flex: 1, fontFamily: FONT_UI, fontSize: 13, color: C.textDim }}>{label}</div>
    <div style={{ display: "flex", alignItems: "center", gap: 8,
                  fontFamily: FONT_MONO, fontSize: 12,
                  color: link ? C.coral : C.text }}>
      {value}
      {badge && (
        <span style={{ padding: "1px 6px", borderRadius: 3, background: C.panelHi,
                       color: C.textMute, fontSize: 9, fontWeight: 600,
                       letterSpacing: 0.5, textTransform: "uppercase" }}>{badge}</span>
      )}
      {link && <Icon d={ICONS.external} size={11} />}
    </div>
  </div>
);

// ============================================================
// App shell
// ============================================================
const App = () => {
  const [view, setView] = useState("library");
  const [project, setProject] = useState(null);
  const [rallies, setRallies] = useState(SEED_RALLIES);
  const [uploadFile, setUploadFile] = useState(null);

  const projects = [
    { id: "p1", name: "Tuesday Night League · Wk 7", date: "Apr 22, 2026", duration: "1:04:12", rallies: 59, thumbLabel: "match · 1080p" },
    { id: "p2", name: "Sunday Scrimmage", date: "Apr 19, 2026", duration: "0:52:08", rallies: 41, thumbLabel: "match · 720p" },
    { id: "p3", name: "Practice — Coach Ali", date: "Apr 14, 2026", duration: "1:18:34", rallies: 72, thumbLabel: "practice" },
    { id: "p4", name: "Coed B League — Final", date: "Apr 09, 2026", duration: "2:11:22", rallies: 96, thumbLabel: "tournament" },
  ];

  const openProject = (p) => {
    setProject(p);
    setRallies(SEED_RALLIES);
    setView("editor");
  };

  const onUploadDone = (file) => {
    setUploadFile(file);
    setView("processing");
  };

  const onProcessingDone = () => {
    setProject({
      id: "new", name: uploadFile?.name?.replace(/\.[^.]+$/, "") || "New match",
      date: "Today", duration: uploadFile?.duration || "1:04:12", rallies: SEED_RALLIES.length,
    });
    setRallies(SEED_RALLIES);
    setView("editor");
  };

  return (
    <div style={{
      display: "flex", flex: 1, minHeight: 0,
      background: C.bg, color: C.text,
      fontFamily: FONT_UI,
    }}>
      <Sidebar
        project={project}
        current={view}
        onNav={(v) => {
          if (v === "upload") setView("upload");
          else if (v === "library") setView("library");
          else setView(v);
        }}
        onSettings={() => setView("settings")}
      />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, minHeight: 0 }}>
        {view === "library" && (
          <LibraryScreen onNew={() => setView("upload")} onOpen={openProject} projects={projects} />
        )}
        {view === "upload" && (
          <UploadScreen onProcess={onUploadDone} onCancel={() => setView("library")} />
        )}
        {view === "processing" && (
          <ProcessingScreen file={uploadFile} onDone={onProcessingDone} onCancel={() => setView("library")} />
        )}
        {view === "editor" && project && (
          <Editor project={project} rallies={rallies} setRallies={setRallies}
                  onExport={() => setView("export")} />
        )}
        {view === "stats" && project && <StatsScreen />}
        {view === "export" && project && (
          <ExportScreen rallies={rallies} project={project} onBack={() => setView("editor")} />
        )}
        {view === "settings" && <SettingsScreen />}
      </div>
    </div>
  );
};

window.App = App;
window.WindowChrome = WindowChrome;

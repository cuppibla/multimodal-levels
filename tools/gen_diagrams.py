#!/usr/bin/env python3
"""Generate the four multimodal-levels architecture SVGs — image-2 style:
light cream panel · horizontal layer bands · white cards w/ colored strokes ·
mono sub-labels · numbered flow pills (image-1 logic) · auto-sized = no overflow."""
import html

# palette (dashboard/deck)
CREAM = "#FDF9F1"; INK = "#332A4E"; SUB = "#8B8299"; BANDLBL = "#9A93AC"
CORAL = "#FF6A45"; TEAL = "#11C0A4"; AMBER = "#F59B0C"; SKY = "#2FA6F0"; VIOLET = "#7B5CFC"
EDGE = "#B9AFC7"
SANS = "Nunito, -apple-system, 'Segoe UI', sans-serif"
MONO = "'Space Mono', ui-monospace, Menlo, monospace"

TFS, SFS = 22, 15
def sw(text, fs): return len(text) * fs * 0.56   # sans-700 width estimate (generous)
def mw(text, fs): return len(text) * fs * 0.62   # mono width estimate

class D:
    def __init__(s, w, h):
        s.w, s.h = w, h
        s.el = [f'<rect width="{w}" height="{h}" rx="22" fill="{CREAM}"/>']
    def band(s, x, y, w, h, label, tint):
        s.el.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{tint}"/>')
        s.el.append(f'<text x="{x+20}" y="{y+30}" font-family={MONO!r} font-size="16" font-weight="700" letter-spacing="2.5" fill="{BANDLBL}">{html.escape(label)}</text>')
    def card(s, cx, y, title, sub, color, w=None, h=66):
        tw = max(sw(title, TFS), mw(sub, SFS) if sub else 0)
        w = w or max(150, tw + 34)
        x = cx - w/2
        s.el.append(f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="{h}" rx="12" fill="#fff" stroke="{color}" stroke-width="2.5"/>')
        ty = y + (27 if sub else h/2 + 6)
        s.el.append(f'<text x="{cx:.0f}" y="{ty:.0f}" text-anchor="middle" font-family={SANS!r} font-size="{TFS}" font-weight="700" fill="{INK}">{html.escape(title)}</text>')
        if sub:
            s.el.append(f'<text x="{cx:.0f}" y="{y+49}" text-anchor="middle" font-family={MONO!r} font-size="{SFS}" fill="{SUB}">{html.escape(sub)}</text>')
        return (x, y, w, h)
    def frame(s, x, y, w, h, label, color):
        s.el.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="7 6"/>')
        s.el.append(f'<text x="{x+18}" y="{y+24}" font-family={MONO!r} font-size="15" font-weight="700" fill="{color}">{html.escape(label)}</text>')
    def arrow(s, x1, y1, x2, y2, color=EDGE, label=None, dash=None, lox=10, loy=0):
        import math
        ang = math.atan2(y2-y1, x2-x1)
        ax, ay = x2 - 10*math.cos(ang), y2 - 10*math.sin(ang)
        d = f' stroke-dasharray="{dash}"' if dash else ''
        s.el.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{ax:.0f}" y2="{ay:.0f}" stroke="{color}" stroke-width="2.2"{d} stroke-linecap="round"/>')
        p1 = (x2 - 13*math.cos(ang-0.45), y2 - 13*math.sin(ang-0.45))
        p2 = (x2 - 13*math.cos(ang+0.45), y2 - 13*math.sin(ang+0.45))
        s.el.append(f'<path d="M {x2:.0f} {y2:.0f} L {p1[0]:.0f} {p1[1]:.0f} L {p2[0]:.0f} {p2[1]:.0f} Z" fill="{color}"/>')
        if label:
            mx, my = (x1+x2)/2 + lox, (y1+y2)/2 + loy
            s.el.append(f'<text x="{mx:.0f}" y="{my:.0f}" font-family={MONO!r} font-size="14.5" font-weight="700" fill="{color if color!=EDGE else SUB}">{html.escape(label)}</text>')
    def curve(s, x1, y1, x2, y2, cx, cy, color, label=None, lx=0, ly=0):
        s.el.append(f'<path d="M {x1} {y1} Q {cx} {cy} {x2} {y2}" fill="none" stroke="{color}" stroke-width="2.2" stroke-dasharray="6 6"/>')
        import math
        ang = math.atan2(y2-cy, x2-cx)
        p1 = (x2 - 13*math.cos(ang-0.45), y2 - 13*math.sin(ang-0.45))
        p2 = (x2 - 13*math.cos(ang+0.45), y2 - 13*math.sin(ang+0.45))
        s.el.append(f'<path d="M {x2} {y2} L {p1[0]:.0f} {p1[1]:.0f} L {p2[0]:.0f} {p2[1]:.0f} Z" fill="{color}"/>')
        if label:
            s.el.append(f'<text x="{lx}" y="{ly}" font-family={MONO!r} font-size="14.5" font-weight="700" fill="{color}">{html.escape(label)}</text>')
    def pill(s, x, y, num, text, color=VIOLET):
        w = 34 + sw(text, 17)*0.95 + 26
        s.el.append(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="38" rx="19" fill="#fff" stroke="#E7DECD" stroke-width="1.5"/>')
        s.el.append(f'<circle cx="{x+19}" cy="{y+19}" r="12.5" fill="{color}"/>')
        s.el.append(f'<text x="{x+19}" y="{y+24}" text-anchor="middle" font-family={SANS!r} font-size="16" font-weight="800" fill="#fff">{num}</text>')
        s.el.append(f'<text x="{x+37}" y="{y+24}" font-family={SANS!r} font-size="17" font-weight="700" fill="{INK}">{html.escape(text)}</text>')
        return w
    def text(s, x, y, t, fs=18, c=SUB, mono=True, anchor="start", weight=700):
        f = MONO if mono else SANS
        s.el.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family={f!r} font-size="{fs}" font-weight="{weight}" fill="{c}">{html.escape(t)}</text>')
    def row(s, y, cards, x0=44, x1=1196, h=66):
        """Place cards [(title, sub, color), ...] evenly in [x0,x1] with auto font shrink. Returns center xs."""
        fs_t, fs_s = TFS, SFS
        def widths(ft, fs):
            return [max(150, max(sw(t, ft), mw(sub or "", fs)) + 30) for t, sub, _ in cards]
        ws = widths(fs_t, fs_s)
        while sum(ws) + 24*(len(cards)-1) > (x1-x0) and fs_t > 15:
            fs_t -= 0.5; fs_s -= 0.25
            ws = widths(fs_t, fs_s)
        gap = ((x1-x0) - sum(ws)) / (len(cards)-1) if len(cards) > 1 else 0
        centers = []
        x = x0
        for (title, sub, color), w in zip(cards, ws):
            cx = x + w/2
            s.el.append(f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="{h}" rx="12" fill="#fff" stroke="{color}" stroke-width="2.5"/>')
            ty = y + (27 if sub else h/2 + 6)
            s.el.append(f'<text x="{cx:.0f}" y="{ty:.0f}" text-anchor="middle" font-family={SANS!r} font-size="{fs_t}" font-weight="700" fill="{INK}">{html.escape(title)}</text>')
            if sub:
                s.el.append(f'<text x="{cx:.0f}" y="{y+49}" text-anchor="middle" font-family={MONO!r} font-size="{fs_s}" fill="{SUB}">{html.escape(sub)}</text>')
            centers.append(cx)
            x += w + gap
        return centers

    def save(s, path):
        svg = f'<svg viewBox="0 0 {s.w} {s.h}" xmlns="http://www.w3.org/2000/svg">\n' + "\n".join(s.el) + "\n</svg>\n"
        open(path, "w").write(svg)
        print("wrote", path, f"({len(svg)//1024} KB)")

BASE = "/Users/annie/Documents/multimodal-levels"

# ═══════════════ LEVEL 2 ═══════════════
d = D(1240, 900)
d.text(28, 40, "ARCHITECTURE — the multi-agent system (02-perceive)", fs=18, c=VIOLET)
# bands
d.band(24, 58, 1192, 360, "AGENT LAYER", "#F3F0FB")
d.band(24, 434, 1192, 170, "TOOL LAYER", "#EDF6F1")
d.band(24, 620, 1192, 160, "DATA LAYER", "#FAF1E4")
# agent layer — root
rx, ry, rw, rh = d.card(620, 96, "MissionAnalysisAI", "root · SequentialAgent — synthesizes + votes 2-of-3", CORAL)
# crew frame
d.frame(140, 236, 960, 150, "EvidenceAnalysisCrew · ParallelAgent — runs concurrently", VIOLET)
g = d.card(310, 286, "GeologicalAnalyst", "reads {soil_url}", TEAL)
b = d.card(620, 286, "BotanicalAnalyst", "reads {flora_url} · video + audio", AMBER)
a = d.card(930, 286, "AstronomicalAnalyst", "reads {stars_url}", SKY)
# root ⇄ crew arrows
d.arrow(560, 162, 560, 232, label="delegates", lox=-92)
d.arrow(680, 232, 680, 162, label="3 reports → state (output_key)", lox=12)
# analysts → tools (drawn after tool row; see below)
# tool layer cards — row layout, guaranteed no overlap
tc = d.row(476, [
    ("confirm_location", "ground-truths the vote", CORAL),
    ("analyze_geological", "Custom MCP", TEAL),
    ("analyze_botanical", "Custom MCP · audio too", AMBER),
    ("extract_star_features", "FunctionTool", SKY),
    ("BigQuery MCP", "Google-managed", VIOLET),
])
# analysts → tools
d.arrow(310, 352, tc[1], 472)
d.arrow(620, 352, tc[2], 472)
d.arrow(905, 352, tc[3], 472)
d.arrow(955, 352, tc[4]-20, 472, label="two tools", lox=8, loy=-14)
# verify curve: root → confirm_location (down-left, dashed coral)
d.curve(rx, ry+40, tc[0], 472, 60, 210, CORAL, label="verify ↓", lx=52, ly=300)
# data layer cards — row layout
dc = d.row(664, [
    ("beacon.json", "BEACON ACTIVE — written by code", CORAL),
    ("Cloud Storage", "evidence: soil .png · flora .mp4 · stars .png", SKY),
    ("BigQuery", "star_catalog · exact match", VIOLET),
])
# tool → data
d.arrow(tc[4], 542, dc[2], 660, label="execute_sql", lox=10)
d.arrow(tc[0], 542, dc[0], 660)
d.arrow(dc[1]-40, 660, tc[1]+30, 546, EDGE, dash="4 5")
d.arrow(dc[1]+40, 660, tc[2]-30, 546, EDGE, dash="4 5", label="Part.from_uri(gs://…)", lox=-280, loy=6)
# numbered flow pills (image-1 logic)
px = 28; py = 812
px = 24
px += d.pill(px, py, 1, "callback hydrates state") + 10
px += d.pill(px, py, 2, "crew fans out in parallel") + 10
px += d.pill(px, py, 3, "each analyst calls its tool") + 10
px += d.pill(px, py, 4, "synthesizer votes 2-of-3") + 10
d.pill(px, py, 5, "code verifies → beacon", CORAL)
d.text(28, 878, "verified run: 3/3 VERDANT · the astronomer's quadrant came out of BigQuery · the botanist heard \"water dripping, insect calls\"", fs=13)
d.save(f"{BASE}/02-perceive/diagrams/architecture.svg")

# ═══════════════ LEVEL 1 ═══════════════
d = D(1240, 900)
d.text(28, 40, "ARCHITECTURE — identity & generation (01-beacon)", fs=18, c=CORAL)
d.band(24, 58, 1192, 200, "① ONE CHAT SESSION — generator.py", "#FBEFE9")
d.band(24, 274, 1192, 230, "② ADK CONSISTENCY ENGINE — agent/agent.py", "#F3F0FB")
d.band(24, 520, 1192, 200, "③ ASYNC VIDEO — video.py", "#FAF1E4")
# band 1 — row layout
b1 = d.row(130, [
    ("4-layer prompt", "anchor · style · spec · SAME", INK),
    ("turn 1 · portrait", "gemini-*-image", CORAL),
    ("turn 2 · map icon", "SEES turn 1 → same face", CORAL),
    ("verify.py", "code judges ✓", TEAL),
])
d.arrow(b1[0]+130, 163, b1[1]-120, 163)
d.arrow(b1[1]+110, 163, b1[2]-130, 163, CORAL, label="same session", loy=-12, lox=-52)
d.arrow(b1[2]+130, 163, b1[3]-90, 163, TEAL)
d.pill(390, 216, 1, "stateless calls = two strangers — a session holds ONE face", CORAL)
# band 2
b2 = d.row(330, [
    ("before_agent_callback", "locks identity once", VIOLET),
    ("session.state", "identity · style · ref image", VIOLET),
    ("generate_explorer_image", "re-reads state EVERY call", INK),
    ("scene 1…N", "same face, any scene", TEAL),
])
d.arrow(b2[0]+125, 363, b2[1]-105, 363, VIOLET, label="seeds", loy=-10, lox=-30)
d.arrow(b2[1]+105, 363, b2[2]-135, 363)
d.arrow(b2[2]+135, 363, b2[3]-95, 363, TEAL)
d.curve(b2[2], 396, b2[1]+40, 404, 700, 456, VIOLET, label="first render → pinned back as the model sheet", lx=470, ly=456)
d.pill(390, 462, 2, "state + callback = the identity re-applied to every call", VIOLET)
# band 3
b3 = d.row(590, [
    ("generate_videos()", "veo-3.x", INK),
    ("operation", "a ticket, not a file", AMBER),
    ("poll op.done", "every 10 s · ~1 min", INK),
    ("beacon_video.mp4", "720p · native audio", TEAL),
])
d.arrow(b3[0]+115, 623, b3[1]-95, 623)
d.arrow(b3[1]+95, 623, b3[2]-100, 623, AMBER)
d.arrow(b3[2]+100, 623, b3[3]-115, 623, TEAL)
d.pill(390, 672, 3, "async — it didn't fail, it's working", AMBER)
d.text(28, 764, "models create · code judges — the gate on progress is deterministic, never an LLM grading itself", fs=13)
px = 28; py = 800
px += d.pill(px, py, 1, "run: uv run python generator.py") + 12
px += d.pill(px, py, 2, "uv run python run_agent.py") + 12
px += d.pill(px, py, 3, "uv run python video.py") + 12
d.pill(px, py, 4, "uv run python verify.py", TEAL)
d.save(f"{BASE}/01-beacon/diagrams/architecture.svg")

# ═══════════════ LEVEL 5 ═══════════════
d = D(1240, 900)
d.text(28, 40, "ARCHITECTURE — the NOVA live console (05-live)", fs=18, c=TEAL)
d.band(24, 58, 1192, 200, "BROWSER — THE HUD", "#F3F0FB")
d.band(24, 340, 1192, 200, "SERVER — FASTAPI · CLOUD RUN", "#EDF6F1")
d.band(24, 622, 1192, 160, "MODEL — GEMINI LIVE (NATIVE AUDIO)", "#FBEFE9")
# browser cards
br = d.row(110, [
    ("mic → AudioWorklet", "16 kHz PCM · 50 ms chunks", VIOLET),
    ("camera → canvas", "JPEG · ~1 fps", VIOLET),
    ("speaker ← 24 kHz", "gapless playback", VIOLET),
    ("barge-in + lock", "RMS → cut playback", CORAL),
])
d.pill(330, 196, 1, "you speak & show fingers — everything streams, nothing waits", VIOLET)
# ws arrows between browser and server
d.arrow(300, 258, 300, 336, label="binary PCM ↓", lox=12)
d.arrow(480, 258, 480, 336, label="{type:\"image\"} ↓", lox=12)
d.arrow(800, 336, 800, 258, label="ADK events (JSON) ↑", lox=12)
d.text(620, 331, "wss://…/ws — one origin, SPA + WebSocket", fs=16, c=INK, anchor="middle")
# server cards
sr = d.row(396, [
    ("LiveRequestQueue", "send_realtime · send_content", TEAL),
    ("runner.run_live()", "BIDI · AUDIO · transcripts", TEAL),
    ("⚡ report_digit(count)", "fires mid-sentence", AMBER),
])
d.arrow(sr[0]+150, 429, sr[1]-140, 429, TEAL)
d.arrow(sr[1]+140, 429, sr[2]-130, 429, AMBER, label="tool call", loy=-10, lox=-42)
d.pill(330, 486, 2, "credentials stay here — the browser never talks to Gemini", TEAL)
# server ⇄ model
d.arrow(600, 540, 600, 618, label="audio + frames ↓", lox=12)
d.arrow(760, 618, 760, 540, label="voice · transcripts · interrupted ↑", lox=12)
# model card
d.card(620, 664, "Gemini Live — hears · sees · speaks · detects interruption", "gemini-live-2.5-flash-native-audio", CORAL, h=70)
d.pill(330, 754, 3, "she answers in VOICE — speak over her and playback cuts instantly", CORAL)
px = 28; py = 812
px += d.pill(px, py, 1, "uv sync · npm run build (frontend)") + 12
px += d.pill(px, py, 2, "uv run --directory backend python main.py → :8500") + 12
d.pill(px, py, 3, "or live: nova-live-….run.app", TEAL)
d.text(28, 878, "biometric lock: a random 4-digit finger sequence · 65 s — NOVA sees your hand, calls report_digit, the lock advances", fs=13)
d.save(f"{BASE}/05-live/diagrams/architecture.svg")

# ═══════════════ LEVEL 6 ═══════════════
d = D(1240, 900)
d.text(28, 40, "ARCHITECTURE — real cross-session memory (06-memory)", fs=18, c=AMBER)
d.band(24, 58, 1192, 210, "AGENT — RESCUE OPS · CLOUD RUN", "#FBEFE9")
d.band(24, 348, 1192, 230, "ONE VERTEX AI AGENT ENGINE — MANAGED", "#F3F0FB")
d.band(24, 662, 1192, 130, "THE PAYOFF — TWO SEPARATE PROCESSES, ZERO COPYING", "#EDF6F1")
# agent cards
ag = d.row(116, [
    ("PreloadMemoryTool()", "READ — injected pre-turn", TEAL),
    ("save_exact_fact", 'state["user:callsign"]', SKY),
    ("add_session_to_memory", "WRITE — at session end", AMBER),
])
d.pill(330, 206, 1, "route by shape — exact values → state · meaning → Memory Bank", AMBER)
# engine cards
mb = d.card(400, 420, "Memory Bank — patterns, by meaning", "GENERATE: Gemini curates · RETRIEVE: similarity, scoped per user", TEAL, h=70)
ss = d.card(400, 505, "Sessions + user: state — exact facts", "VertexAiSessionService · durable · looked up EXACTLY", SKY, h=66)
d.text(950, 448, "custom topics:", fs=15, c=SUB)
d.text(950, 468, "survivor_context · comms_style", fs=15, c=TEAL)
d.text(950, 520, "user:callsign = Vega-7", fs=15, c=SKY)
d.text(950, 540, "user:recycler_error = 42", fs=15, c=SKY)
# arrows agent → engine
d.arrow(ag[0], 182, 320, 416, TEAL, label="retrieve", lox=-88, loy=0)
d.arrow(ag[2], 182, 520, 416, AMBER, dash="6 6", label="generate", lox=6, loy=-8)
d.curve(ag[1], 182, 655, 538, 800, 400, SKY, label="user: r/w", lx=728, ly=372)
# payoff strip
po = d.row(712, [
    ("SESSION A — “I’m Vega-7…”", "facts told → flush", INK),
    ("consolidation", "Gemini curates · ~seconds", TEAL),
    ("SESSION B — already knows you", "both stores, unprompted", VIOLET),
])
d.arrow(po[0]+165, 745, po[1]-125, 745)
d.arrow(po[1]+125, 745, po[2]-185, 745, TEAL)
px = 28; py = 812
px += d.pill(px, py, 1, "uv run python setup_engine.py (one-time)") + 12
px += d.pill(px, py, 2, "uv run python chat.py session-a") + 12
px += d.pill(px, py, 3, "uv run python chat.py session-b", VIOLET)
d.text(28, 878, "hosting proof: the agent runs on Cloud Run — Memory Bank does NOT require Agent Engine hosting (memory-agent-….run.app/chat)", fs=13)
d.save(f"{BASE}/06-memory/diagrams/architecture.svg")

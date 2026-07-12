#!/usr/bin/env python3
"""Concept diagrams for the deck — same light-panel language as the architecture SVGs.
callbacks · half/full duplex · LiveRequestQueue · execution logic · crew blackboard"""
import html, math

CREAM = "#FDF9F1"; INK = "#332A4E"; SUB = "#8B8299"; BANDLBL = "#9A93AC"
CORAL = "#FF6A45"; TEAL = "#11C0A4"; AMBER = "#F59B0C"; SKY = "#2FA6F0"; VIOLET = "#7B5CFC"
EDGE = "#8F86A0"
SANS = "Nunito, -apple-system, 'Segoe UI', sans-serif"
MONO = "'Space Mono', ui-monospace, Menlo, monospace"

TFS, SFS = 22, 15
def sw(t, fs): return len(t) * fs * 0.56
def mw(t, fs): return len(t) * fs * 0.62

class D:
    def __init__(s, w, h):
        s.w, s.h = w, h
        s.el = [f'<rect width="{w}" height="{h}" rx="22" fill="{CREAM}"/>']
    def rect(s, x, y, w, h, fill, stroke=None, swidth=2, rx=14, dash=None):
        st = f' stroke="{stroke}" stroke-width="{swidth}"' if stroke else ''
        dd = f' stroke-dasharray="{dash}"' if dash else ''
        s.el.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{st}{dd}/>')
    def card(s, cx, y, title, sub, color, w=None, h=66, fill="#fff", tfs=None):
        tfs = tfs or TFS
        tw = max(sw(title, tfs), mw(sub, SFS) if sub else 0)
        w = w or max(150, tw + 34)
        x = cx - w/2
        s.rect(x, y, w, h, fill, color, 2.5, 12)
        ty = y + (27 if sub else h/2 + 6.5)
        s.el.append(f'<text x="{cx:.0f}" y="{ty:.0f}" text-anchor="middle" font-family={SANS!r} font-size="{tfs}" font-weight="700" fill="{INK}">{html.escape(title)}</text>')
        if sub:
            s.el.append(f'<text x="{cx:.0f}" y="{y+49}" text-anchor="middle" font-family={MONO!r} font-size="{SFS}" fill="{SUB}">{html.escape(sub)}</text>')
        return (x, y, w, h)
    def arrow(s, x1, y1, x2, y2, color=EDGE, label=None, dash=None, lox=10, loy=0, width=2.4):
        ang = math.atan2(y2-y1, x2-x1)
        ax, ay = x2 - 10*math.cos(ang), y2 - 10*math.sin(ang)
        dd = f' stroke-dasharray="{dash}"' if dash else ''
        s.el.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{ax:.0f}" y2="{ay:.0f}" stroke="{color}" stroke-width="{width}"{dd} stroke-linecap="round"/>')
        p1 = (x2 - 14*math.cos(ang-0.45), y2 - 14*math.sin(ang-0.45))
        p2 = (x2 - 14*math.cos(ang+0.45), y2 - 14*math.sin(ang+0.45))
        s.el.append(f'<path d="M {x2:.0f} {y2:.0f} L {p1[0]:.0f} {p1[1]:.0f} L {p2[0]:.0f} {p2[1]:.0f} Z" fill="{color}"/>')
        if label:
            s.el.append(f'<text x="{(x1+x2)/2+lox:.0f}" y="{(y1+y2)/2+loy:.0f}" font-family={MONO!r} font-size="14.5" font-weight="700" fill="{color if color!=EDGE else SUB}">{html.escape(label)}</text>')
    def elbow(s, x1, y1, x2, y2, color=EDGE):
        """vertical-then-horizontal-then-vertical elbow with arrowhead at end (downward)."""
        my = (y1+y2)/2
        s.el.append(f'<path d="M {x1} {y1} L {x1} {my} L {x2} {my} L {x2} {y2-10}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linecap="round"/>')
        s.el.append(f'<path d="M {x2} {y2} L {x2-6} {y2-12} L {x2+6} {y2-12} Z" fill="{color}"/>')
    def pill(s, x, y, num, text, color=VIOLET):
        w = 34 + sw(text, 17)*0.95 + 26
        s.rect(x, y, w, 32, "#fff", "#E7DECD", 1.5, 16)
        s.el.append(f'<circle cx="{x+19}" cy="{y+19}" r="12.5" fill="{color}"/>')
        s.el.append(f'<text x="{x+19}" y="{y+24}" text-anchor="middle" font-family={SANS!r} font-size="16" font-weight="800" fill="#fff">{num}</text>')
        s.el.append(f'<text x="{x+37}" y="{y+24}" font-family={SANS!r} font-size="17" font-weight="700" fill="{INK}">{html.escape(text)}</text>')
        return w
    def text(s, x, y, t, fs=18, c=SUB, mono=True, anchor="start", weight=700):
        f = MONO if mono else SANS
        s.el.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family={f!r} font-size="{fs}" font-weight="{weight}" fill="{c}">{html.escape(t)}</text>')
    def row(s, y, cards, x0=44, x1=1196, h=66):
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
            ty = y + (27 if sub else h/2 + 6.5)
            s.el.append(f'<text x="{cx:.0f}" y="{ty:.0f}" text-anchor="middle" font-family={SANS!r} font-size="{fs_t}" font-weight="700" fill="{INK}">{html.escape(title)}</text>')
            if sub:
                s.el.append(f'<text x="{cx:.0f}" y="{y+49}" text-anchor="middle" font-family={MONO!r} font-size="{fs_s}" fill="{SUB}">{html.escape(sub)}</text>')
            centers.append(cx)
            x += w + gap
        return centers

    def save(s, *paths):
        svg = f'<svg viewBox="0 0 {s.w} {s.h}" xmlns="http://www.w3.org/2000/svg">\n' + "\n".join(s.el) + "\n</svg>\n"
        for p in paths:
            open(p, "w").write(svg)
            print("wrote", p)

DECK = "/tmp/deck-improvements/src/assets"

# ═══════ 1 · CALLBACKS — her reference layout ═══════
d = D(1240, 720)
d.text(28, 40, "ADK CALLBACKS — six deterministic hooks around every non-deterministic step", fs=18, c=CORAL)
# top row
b_ag = d.card(210, 80, "before_agent_callback", "gate the whole turn", AMBER)
agent = d.card(620, 80, "🤖  Agent", "one turn of the loop", SKY, w=300, h=70)
a_ag = d.card(1030, 80, "after_agent_callback", "inspect · rewrite the reply", AMBER)
d.arrow(360, 115, 468, 115, AMBER)
d.arrow(772, 115, 878, 115, AMBER)
# agent → model / tools (elbows)
d.elbow(560, 150, 380, 330, EDGE)
d.elbow(680, 150, 860, 330, EDGE)
model = d.card(380, 330, "Model", "reason · draft a tool call", TEAL, w=320, h=70)
tools = d.card(860, 330, "Tools", "act — fetch · compute · generate", CORAL, w=340, h=70)
# four hooks in one symmetric row (reference layout)
bm = d.card(198, 560, "before_model_callback", "block a jailbreak · inject identity", AMBER)
am = d.card(515, 560, "after_model_callback", "log tokens · rewrite output", "#E0B45C")
bt = d.card(800, 560, "before_tool_callback", "cached? → skip the call", AMBER)
at = d.card(1078, 560, "after_tool_callback", "redact PII from the result", "#E0B45C")
d.arrow(230, 556, 330, 404, AMBER)
d.arrow(440, 404, 505, 556, "#C9A75C")
d.arrow(806, 556, 838, 404, AMBER)
d.arrow(918, 404, 1040, 556, "#C9A75C")
d.text(28, 700, "return a value from any before_* hook → the step is SHORT-CIRCUITED (guard · redact · cache · trace, without touching the SDK)", fs=13.5)
d.save(f"{DECK}/dg-callbacks.svg")

# ═══════ 2 · HALF vs FULL DUPLEX ═══════
d = D(1240, 660)
d.text(28, 40, "REAL-TIME — a different shape of connection, not a faster request", fs=18, c=TEAL)
# left panel: half duplex
d.rect(36, 60, 570, 520, "#FBEFE9")
d.text(60, 92, "HALF-DUPLEX — HTTP · walkie-talkie", fs=16, c=CORAL)
for x, lbl in ((150, "client"), (500, "server")):
    d.el.append(f'<line x1="{x}" y1="130" x2="{x}" y2="520" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')
    d.text(x, 118, lbl, fs=15, c=INK, anchor="middle")
d.arrow(150, 170, 500, 200, CORAL, label="request", lox=-60, loy=-14)
d.arrow(500, 240, 150, 270, EDGE, label="response", lox=-40, loy=-14)
d.arrow(150, 320, 500, 350, CORAL, label="request", lox=-60, loy=-14)
d.arrow(500, 390, 150, 420, EDGE, label="response", lox=-40, loy=-14)
d.text(325, 478, "“over.”  one direction at a time —", fs=15.5, c=SUB, anchor="middle")
d.text(325, 500, "its turn must END before yours can begin", fs=15.5, c=SUB, anchor="middle")
# right panel: full duplex
d.rect(636, 60, 570, 520, "#EDF6F1")
d.text(660, 92, "FULL-DUPLEX — WebSocket · phone call", fs=16, c=TEAL)
for x, lbl in ((750, "client"), (1100, "server")):
    d.el.append(f'<line x1="{x}" y1="130" x2="{x}" y2="520" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')
    d.text(x, 118, lbl, fs=15, c=INK, anchor="middle")
d.arrow(750, 160, 1100, 175, EDGE, dash="5 5", label="handshake — once", lox=-90, loy=-12)
for i, (y1, y2, ltr) in enumerate(((215, 232, 1), (250, 262, 0), (280, 297, 1), (312, 325, 0), (342, 356, 1), (372, 384, 0))):
    if ltr: d.arrow(750, y1, 1100, y2, TEAL, width=2.2)
    else:   d.arrow(1100, y1, 750, y2, VIOLET, width=2.2)
d.text(925, 416, "bi-directional traffic — BOTH talk at once", fs=15.5, c=TEAL, anchor="middle")
d.arrow(750, 450, 1100, 465, EDGE, label="bye", lox=-30, loy=-12)
d.text(925, 500, "you can cut in mid-sentence → barge-in", fs=15.5, c=SUB, anchor="middle")
d.text(28, 620, "a fast voice bot on HTTP is still a walkie-talkie — Live is a phone call: the channel is OPEN in both directions the whole time", fs=13.5)
d.save(f"{DECK}/dg-duplex.svg")

# ═══════ 3 · LIVEREQUESTQUEUE ═══════
d = D(1240, 700)
d.text(28, 40, "LIVEREQUESTQUEUE — five ways in, one ordered stream out", fs=18, c=VIOLET)
inputs = [("send_content(text)", "a COMPLETE turn → respond now", SKY),
          ("send_realtime(audio)", "16 kHz chunks · 50–100 ms", TEAL),
          ("send_realtime(video)", "JPEG frames · a stream", TEAL),
          ("activity signals", "start / end of user activity", AMBER),
          ("close()", "hang up the channel", CORAL)]
ys = [86, 186, 286, 386, 486]
for (t, subt, c), y in zip(inputs, ys):
    d.card(230, y, t, subt, c, w=380)
    d.arrow(420, y+33, 520, 300, c, width=2)
q = d.card(650, 262, "LiveRequestQueue", "async FIFO — thread-safe, ordered", VIOLET, w=300, h=76)
d.arrow(800, 300, 880, 300, VIOLET)
r = d.card(970, 262, "ADK Runner", "run_live(queue, config)", TEAL, w=210, h=76)
d.arrow(1075, 338, 1075, 400, TEAL)
g = d.card(1000, 404, "Gemini Live", "one bidi session", CORAL, w=230, h=70)
d.arrow(880, 440, 560, 440, CORAL, label="events flow back — voice · transcripts · tool calls", lox=-160, loy=28)
d.rect(560, 540, 650, 110, "#fff", "#E7DECD", 1.5, 14)
d.text(584, 570, "KEY INSIGHT", fs=15, c=VIOLET)
d.text(584, 596, "once the loop is running, send and receive happen CONCURRENTLY —", fs=15.5, c=INK)
d.text(584, 618, "that is bidi streaming. remove the queue and you are back to turn-taking.", fs=15.5, c=INK)
d.pill(36, 585, 1, "content = a deliberate turn (pressing Enter)", SKY)
d.pill(36, 625, 2, "realtime = an open mic — VAD finds the edges", TEAL)
d.save(f"{DECK}/dg-liverequestqueue.svg")

# ═══════ 4 · EXECUTION LOGIC ═══════
d = D(1240, 660)
d.text(28, 40, "THE EXECUTION LOGIC — two coroutines, one loop (backend/main.py)", fs=18, c=TEAL)
# websocket lane
d.rect(40, 70, 230, 520, "#F1EEE6", "#C9BFA9", 2, 14, dash="7 6")
d.text(155, 100, "WebSocket", fs=16, c=INK, anchor="middle")
d.card(155, 130, "receive()", "binary PCM · JSON frames", INK, w=200)
d.arrow(270, 300, 350, 300, TEAL, width=3)
# runner frame
d.rect(330, 70, 870, 520, "#EAF3FB", SKY, 2, 16)
d.text(1120, 100, "Runner", fs=16, c=SKY, anchor="end")
d.pill(360, 96, 1, "runner initiation — streaming_mode = BIDI · point the runner at the queue", SKY)
d.pill(360, 140, 2, "convert to LiveRequest — send_content() for text · send_realtime() for blobs", TEAL)
# the queue cylinder
d.rect(420, 220, 560, 150, "#FBE9E4", CORAL, 2.5, 70)
d.el.append(f'<ellipse cx="930" cy="295" rx="46" ry="73" fill="#F7DDD6" stroke="{CORAL}" stroke-width="2.5"/>')
d.text(700, 210, "LiveRequestQueue — async FIFO", fs=18, c=CORAL, anchor="middle")
for i, x in enumerate((510, 610, 710, 800)):
    d.rect(x, 265, 74, 58, "#fff", CORAL, 1.5, 10)
    d.text(x+37, 299, "LiveRequest", fs=11.5, c=SUB, anchor="middle")
d.arrow(980, 295, 990, 295, CORAL)
d.card(1095, 262, "Event", "run_live event stream", TEAL, h=66, tfs=16)
d.text(660, 420, "asyncio.gather( send_task , receive_task )", fs=18, c=INK, anchor="middle")
d.text(660, 446, "neither waits for the other — remove gather and you are back to walkie-talkie turns", fs=15, c=SUB, anchor="middle")
d.pill(360, 520, 3, "events flow back the whole time — voice chunks · transcripts · interrupted · tool calls", CORAL)
d.text(28, 630, "the queue DECOUPLES the two directions: the websocket producer never blocks the model consumer", fs=13.5)
d.save(f"{DECK}/dg-execution.svg")

# ═══════ 5 · CREW BLACKBOARD (bigger, clearer) ═══════
d = D(1240, 660)
d.text(28, 40, "THE BLACKBOARD — no agent calls another; they share state", fs=18, c=VIOLET)
orch = d.card(160, 280, "Orchestrator", "root — fans out, in parallel", SKY, w=250, h=76)
specs = [("Geologist", "writes state['geology']", AMBER, 120),
         ("Botanist", "writes state['flora']", TEAL, 280),
         ("Astronomer", "writes state['stars']", VIOLET, 440)]
for t, subt, c, y in specs:
    d.card(480, y, t, subt, c, w=270)
    d.arrow(285, 310, 345, y+33, SKY, width=2.2)
    d.arrow(615, y+33, 700, 300, c, width=2.2)
# blackboard
d.rect(700, 120, 260, 400, "#fff", VIOLET, 2.5, 16)
d.text(830, 152, "the blackboard", fs=16, c=VIOLET, anchor="middle")
d.text(830, 176, "session.state", fs=18, c=INK, anchor="middle")
for k, c, y in (("geology: ✓", AMBER, 210), ("flora: ✓", TEAL, 280), ("stars: ✓", VIOLET, 350)):
    d.rect(730, y, 200, 48, "#FBF7F0", c, 1.8, 10)
    d.text(830, y+30, k, fs=18, c=INK, anchor="middle")
d.text(830, 452, "each specialist writes ONE key", fs=14, c=SUB, anchor="middle")
d.text(830, 472, "{key} templating reads them", fs=14, c=SUB, anchor="middle")
dec = d.card(1090, 280, "Decision agent", "reads ALL → votes 2-of-3", CORAL, w=230, h=76)
d.arrow(960, 318, 975, 318, CORAL)
d.pill(36, 585, 1, "fan-out — the three run AT ONCE (ParallelAgent)", SKY)
d.pill(500, 585, 2, "distinct output_key per agent — no race", VIOLET)
d.pill(920, 585, 3, "code tallies the vote", CORAL)
d.save(f"{DECK}/dg-blackboard.svg")
print("done")

# ═══════ 6 · ADK RUNTIME — "Everything is an Event" (her reference #1) ═══════
d = D(1240, 740)
d.text(28, 42, "THE ADK RUNTIME — how it's wired, and where memory lives", fs=18, c=VIOLET)
# user
d.el.append(f'<circle cx="110" cy="290" r="44" fill="#fff" stroke="{SKY}" stroke-width="2.5"/>')
d.text(110, 302, "🙂", fs=34, anchor="middle")
d.text(110, 362, "user", fs=16, c=INK, anchor="middle")
# dashed system frame
d.rect(230, 80, 760, 545, "none", "#B9AFC7", 2, 18, dash="8 7")
# runner
d.card(430, 120, "Runner", None, SKY, w=340, h=54)
d.card(430, 186, "event processor", "commits every Event, in order", INK, w=300)
d.rect(260, 106, 340, 160, "none", SKY, 2, 14)
# user arrows
d.arrow(158, 268, 256, 180, SKY, label="user input", lox=-108, loy=-16)
d.arrow(256, 380, 158, 312, EDGE)
d.text(140, 402, "event stream", fs=15, c=SUB)
# event loop down to agent execution
d.arrow(380, 268, 380, 356, EDGE)
d.arrow(480, 356, 480, 268, EDGE, label="event loop", lox=14)
d.card(430, 360, "Agent Execution", "does the work, yielding Events", AMBER, w=340, h=70)
d.arrow(360, 430, 320, 500, EDGE)
d.arrow(500, 430, 540, 500, EDGE)
d.card(320, 504, "Model", "reason", CORAL, w=170)
d.card(545, 504, "Tools", "act", TEAL, w=170)
# ADK services
d.rect(680, 130, 290, 330, "#F3F0FB", VIOLET, 2, 16)
d.text(825, 162, "ADK Services", fs=17, c=INK, anchor="middle", mono=False)
d.card(825, 190, "session", "short-term — THIS conversation", SKY, w=250)
d.card(825, 290, "memory", "long-term — across sessions", CORAL, w=250)
d.arrow(600, 210, 676, 230, EDGE)
d.arrow(676, 300, 600, 250, EDGE)
# storage
for cy, c in ((235, SKY), (345, CORAL)):
    d.el.append(f'<path d="M 1050 {cy-24} a 45 14 0 0 0 90 0 v 48 a 45 14 0 0 1 -90 0 z" fill="#fff" stroke="{c}" stroke-width="2"/>')
    d.el.append(f'<ellipse cx="1095" cy="{cy-24}" rx="45" ry="14" fill="#fff" stroke="{c}" stroke-width="2"/>')
    d.arrow(952 if cy==235 else 952, cy-10, 1044, cy, c, width=2)
d.text(1095, 415, "session & memory", fs=13.5, c=SUB, anchor="middle")
d.text(1095, 435, "storage", fs=13.5, c=SUB, anchor="middle")
px = 28; py = 655
px += d.pill(px, py, 1, "the Runner drives the loop") + 12
px += d.pill(px, py, 2, "the agent yields Events", AMBER) + 12
px += d.pill(px, py, 3, "every Event flows through Services → storage", TEAL)
d.text(28, 726, "everything the app remembers lives on the RIGHT — session (short-term) and memory (long-term), never inside the agent", fs=15)
d.save(f"{DECK}/dg-runtime.svg")

# ═══════ 7 · A2A — a peer, not a tool (her reference #2) ═══════
d = D(1240, 700)
d.text(28, 42, "A2A — agents calling AGENTS, across frameworks and organizations", fs=18, c=VIOLET)
for x0, brain, fw in ((70, "Vertex AI (Gemini)", "Agent Development Kit"), (700, "any LLM", "any agent framework")):
    d.rect(x0, 80, 470, 430, "#fff", SKY, 2.5, 20)
    d.text(x0+235, 118, "🤖  Agent", fs=20, c=INK, anchor="middle", mono=False)
    d.rect(x0+40, 140, 390, 74, "#F3F0FB", VIOLET, 2, 12)
    d.text(x0+235, 172, "Local Agents  ● ● ●", fs=16, c=INK, anchor="middle", mono=False)
    d.text(x0+235, 196, "an in-process crew (sub_agents)", fs=13, c=SUB, anchor="middle")
    d.card(x0+235, 244, brain, "the brain", TEAL, w=390)
    d.card(x0+235, 330, fw, "the harness", AMBER, w=390)
    # MCP chip + APIs below
    d.rect(x0+180, 424, 110, 40, "#fff", SKY, 2, 10, dash="6 5")
    d.text(x0+235, 450, "MCP", fs=15, c=SKY, anchor="middle")
    d.arrow(x0+235, 464, x0+235, 528, SKY, dash="6 5", width=2)
    d.card(x0+235, 532, "APIs & enterprise apps", "tools — MCP wires these", INK, w=330, h=60)
# boundary + A2A
d.el.append(f'<line x1="620" y1="90" x2="620" y2="600" stroke="#C9BFA9" stroke-width="2.5" stroke-dasharray="3 7"/>')
d.text(620, 626, "organizational / technological boundary", fs=13.5, c=SUB, anchor="middle")
d.rect(510, 268, 220, 44, "#fff", VIOLET, 2.5, 22)
d.text(620, 296, "A2A protocol", fs=16, c=VIOLET, anchor="middle")
d.arrow(508, 290, 480, 290, VIOLET, dash="7 5")
d.arrow(732, 290, 760, 290, VIOLET, dash="7 5")
d.text(28, 682, "MCP wires an agent to TOOLS · A2A wires it to a PEER that reasons — discovered by Agent Card, not a URL", fs=15)
d.save(f"{DECK}/dg-a2a.svg")

# ═══════ 8 · MEMORY BANK — two calls (her reference #3) ═══════
d = D(1240, 660)
d.text(28, 42, "HOW VERTEX AI MEMORY BANK WORKS — two calls, Gemini does the thinking", fs=18, c=TEAL)
d.card(230, 110, "Your agent", "Runner · event processor", INK, w=300, h=76)
d.arrow(382, 138, 470, 138, EDGE, label="calls", loy=-12, lox=-24)
d.card(700, 100, "VertexAiMemoryBankService", "the ADK wrapper your code calls", TEAL, w=460, h=90)
# cylinder
d.el.append(f'<path d="M 560 300 a 140 34 0 0 0 280 0 v 130 a 140 34 0 0 1 -280 0 z" fill="#fff" stroke="{TEAL}" stroke-width="2.5"/>')
d.el.append(f'<ellipse cx="700" cy="300" rx="140" ry="34" fill="#EDF6F1" stroke="{TEAL}" stroke-width="2.5"/>')
d.text(700, 388, "Memory Bank", fs=19, c=INK, anchor="middle", mono=False)
d.arrow(660, 194, 660, 262, TEAL)
d.arrow(740, 262, 740, 194, TEAL)
# gemini
d.card(1060, 320, "Gemini", "extracts + consolidates", VIOLET, w=250, h=76)
d.arrow(844, 340, 931, 348, VIOLET, label="consolidate", lox=-90, loy=-14)
d.arrow(931, 372, 844, 366, VIOLET)
# the two calls
d.rect(60, 500, 560, 64, "#FBF3E3", AMBER, 2, 12)
d.text(84, 527, "① GENERATE · write", fs=16, c=AMBER)
d.text(84, 550, "Gemini turns raw session data into clean, consolidated memories", fs=14, c=INK)
d.rect(660, 500, 520, 64, "#EAF3FB", SKY, 2, 12)
d.text(684, 527, "② RETRIEVE · read", fs=16, c=SKY)
d.text(684, 550, "a similarity search in the bank, scoped to this user", fs=14, c=INK)
d.text(28, 630, "you never touch the raw API — and the bank keeps only the ESSENTIAL memories, so your context stays lean", fs=15)
d.save(f"{DECK}/dg-memorybank.svg")

# ═══════ 9 · ASYNC VIDEO — a ticket, not a file ═══════
d = D(1240, 500)
d.text(28, 42, "ASYNC VIDEO (VEO) — you get a ticket, not a file", fs=18, c=AMBER)
d.rect(40, 70, 560, 90, "#EDF6F1", TEAL, 2, 14)
d.text(64, 102, "IMAGE — SYNCHRONOUS", fs=15, c=TEAL)
d.text(64, 130, "pixels come back inline, in the SAME response — read the parts, done", fs=14, c=INK)
d.rect(640, 70, 560, 90, "#FBF3E3", AMBER, 2, 14)
d.text(664, 102, "VIDEO — ASYNCHRONOUS", fs=15, c=AMBER)
d.text(664, 130, "rendering takes ~a minute — the call returns a long-running OPERATION", fs=14, c=INK)
b = d.row(220, [
    ("generate_videos()", "veo-3.x · returns immediately", INK),
    ("operation", "the TICKET — not the video", AMBER),
    ("poll op.done", "every 10 s — it's working, not broken", INK),
    ("beacon_video.mp4", "~1 min · 720p · native audio", TEAL),
], h=76)
d.arrow(b[0]+140, 258, b[1]-115, 258)
d.arrow(b[1]+115, 258, b[2]-155, 258, AMBER)
d.arrow(b[2]+155, 258, b[3]-140, 258, TEAL)
# self-loop on poll
d.el.append(f'<path d="M {b[2]-40} 220 Q {b[2]} 168 {b[2]+40} 220" fill="none" stroke="{AMBER}" stroke-width="2.2" stroke-dasharray="6 5"/>')
d.el.append(f'<path d="M {b[2]+40} 220 L {b[2]+30} 206 L {b[2]+46} 204 Z" fill="{AMBER}"/>')
d.text(b[2], 158, "sleep(10) · ask again", fs=13, c=AMBER, anchor="middle")
px = 40; py = 360
px += d.pill(px, py, 1, "request — the call returns a ticket immediately", AMBER) + 14
px += d.pill(px, py, 2, "poll — “did it fail?” no, it's async", INK) + 14
d.pill(px, py, 3, "collect — save the mp4", TEAL)
d.text(28, 460, "the room panics ~3 seconds in — pre-empt it: you got a ticket at the counter, the kitchen is cooking", fs=15)
d.save(f"{DECK}/dg-asyncvideo.svg")
print("new diagrams done")

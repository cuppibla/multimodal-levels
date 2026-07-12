import { useEffect, useRef, useState } from "react";
import { createStreamer, getAudioContext, startRecorder } from "./audio.js";

// NOVA · NEURAL SYNC — a biometric-lock console over a real Gemini Live channel.
// Camera feed sits inside the scanner rings; NOVA sees your fingers, calls report_digit
// server-side, and the lock advances. 4 matches before the timer dies → access granted.

const SEQ_LEN = 4;
const TIME_LIMIT = 65; // seconds — same contract as the gca level_3 lock

const randomSequence = () => {
  const pool = [1, 2, 3, 4, 5];
  const seq = [];
  for (let i = 0; i < SEQ_LEN; i++) seq.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0]);
  return seq;
};

export default function App() {
  const [status, setStatus] = useState("boot"); // boot | syncing | scanning | granted | lockout | lost
  const [speaking, setSpeaking] = useState(false);
  const [sequence, setSequence] = useState([]);
  const [progress, setProgress] = useState(0);
  const [lastDigit, setLastDigit] = useState(null);
  const [flash, setFlash] = useState(null); // "hit" | "miss"
  const [timeLeft, setTimeLeft] = useState(TIME_LIMIT);
  const [feed, setFeed] = useState([]); // {who, text}
  const [bars, setBars] = useState(new Array(24).fill(0));
  const [micLevel, setMicLevel] = useState(0);

  const wsRef = useRef(null);
  const streamerRef = useRef(null);
  const stopRecRef = useRef(null);
  const videoRef = useRef(null);
  const frameTimerRef = useRef(null);
  const speakTimerRef = useRef(null);
  const rafRef = useRef(null);
  const gameRef = useRef({ sequence: [], progress: 0, status: "boot" });

  const pushLine = (who, text) => setFeed((t) => [...t.slice(-30), { who, text }]);

  // ── the lock ────────────────────────────────────────────────────────────────
  function onDigit(count) {
    const g = gameRef.current;
    setLastDigit(count);
    if (g.status !== "scanning") return;
    if (count === g.sequence[g.progress]) {
      g.progress += 1;
      setProgress(g.progress);
      setFlash("hit");
      if (g.progress >= SEQ_LEN) {
        g.status = "granted";
        setStatus("granted");
      }
    } else {
      setFlash("miss");
    }
    setTimeout(() => setFlash(null), 650);
  }

  // countdown
  useEffect(() => {
    if (status !== "scanning") return;
    const t = setInterval(() => {
      setTimeLeft((s) => {
        if (s <= 1) {
          clearInterval(t);
          gameRef.current.status = "lockout";
          setStatus("lockout");
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [status === "scanning"]); // eslint-disable-line react-hooks/exhaustive-deps

  // waveform loop
  useEffect(() => {
    const tick = () => {
      if (streamerRef.current) setBars(streamerRef.current.levels(24));
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  // ── channel ─────────────────────────────────────────────────────────────────
  async function initiate() {
    setStatus("syncing");
    const seq = randomSequence();
    setSequence(seq);
    setProgress(0);
    setTimeLeft(TIME_LIMIT);
    gameRef.current = { sequence: seq, progress: 0, status: "syncing" };

    await getAudioContext().resume();
    streamerRef.current = createStreamer();

    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const session = Math.random().toString(36).slice(2, 9);
    const ws = new WebSocket(`${proto}//${location.host}/ws/operator/${session}`);
    wsRef.current = ws;

    ws.onopen = async () => {
      gameRef.current.status = "scanning";
      setStatus("scanning");
      stopRecRef.current = await startRecorder({
        onChunk: (buf) => {
          if (ws.readyState === 1) ws.send(buf);
          const v = new Int16Array(buf);
          let s = 0;
          for (let i = 0; i < v.length; i += 16) s += Math.abs(v[i]);
          setMicLevel(Math.min(1, s / (v.length / 16) / 8000));
        },
        onSpeechStart: () => streamerRef.current?.stop(),
      });
      await startCamera(ws);
    };

    ws.onmessage = (e) => {
      let msg;
      try { msg = JSON.parse(e.data); } catch { return; }
      if (msg.type === "ping") return;
      const sc = msg.serverContent || {};
      if (sc.interrupted) streamerRef.current?.stop();
      const parts = msg.content?.parts || sc.modelTurn?.parts || [];
      for (const p of parts) {
        const inline = p.inlineData || p.inline_data;
        if (inline?.data && (inline.mimeType || inline.mime_type || "").startsWith("audio/")) {
          streamerRef.current?.enqueue(inline.data);
          setSpeaking(true);
          clearTimeout(speakTimerRef.current);
          speakTimerRef.current = setTimeout(() => setSpeaking(false), 500);
        }
        const fc = p.functionCall || p.function_call;
        if (fc?.name === "report_digit") {
          onDigit(Number(fc.args?.count));
          pushLine("tool", `⚡ report_digit(${fc.args?.count})`);
        }
      }
      const inT = msg.inputTranscription || sc.inputTranscription;
      const outT = msg.outputTranscription || sc.outputTranscription;
      if (inT?.text) pushLine("you", inT.text);
      if (outT?.text) pushLine("nova", outT.text);
    };
    ws.onclose = () => { if (gameRef.current.status === "scanning") setStatus("lost"); cleanup(); };
    ws.onerror = () => { setStatus("lost"); cleanup(); };
  }

  async function startCamera(ws) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
      const canvas = document.createElement("canvas");
      canvas.width = 640; canvas.height = 480;
      frameTimerRef.current = setInterval(() => {
        if (ws.readyState !== 1) return;
        canvas.getContext("2d").drawImage(videoRef.current, 0, 0, 640, 480);
        ws.send(JSON.stringify({ type: "image", mimeType: "image/jpeg",
          data: canvas.toDataURL("image/jpeg", 0.6).split(",")[1] }));
      }, 900);
    } catch { pushLine("sys", "camera unavailable — voice only"); }
  }

  function cleanup() {
    stopRecRef.current?.();
    clearInterval(frameTimerRef.current);
    streamerRef.current?.stop();
  }
  useEffect(() => () => { cleanup(); wsRef.current?.close(); }, []);

  const scanning = status === "scanning";
  const pct = (timeLeft / TIME_LIMIT) * 100;

  return (
    <div className={`hud ${flash === "hit" ? "flash-hit" : ""} ${flash === "miss" ? "flash-miss" : ""}`}>
      <div className="grid-bg" />
      <div className="scanlines" />

      <header className="bar">
        <span className="brand">WAY BACK HOME · DRONE FLEET</span>
        <span className={`chip chip-${status}`}>
          {{ boot: "STANDBY", syncing: "SYNCING…", scanning: "◉ NEURAL SYNC ACTIVE", granted: "ACCESS GRANTED", lockout: "LOCKOUT", lost: "LINK LOST" }[status]}
        </span>
        <span className="brand right">NOVA · BIOMETRIC SCANNER</span>
      </header>

      {/* sequence slots */}
      <div className="seq">
        {sequence.map((d, i) => (
          <div key={i} className={`slot ${i < progress ? "done" : i === progress && scanning ? "active" : ""}`}>
            <span className="slot-digit">{i < progress ? "✓" : d}</span>
            <span className="slot-label">{i < progress ? "LOCKED" : i === progress && scanning ? "SHOW FINGERS" : "PENDING"}</span>
          </div>
        ))}
        {sequence.length === 0 && <div className="seq-hint">a 4-digit finger sequence will be generated</div>}
      </div>

      {/* the scanner — camera inside the rings */}
      <div className={`scanner ${speaking ? "nova-speaking" : ""} ${scanning ? "scanning" : ""}`}>
        <div className="ring r1" /><div className="ring r2" /><div className="ring r3" />
        <div className="cam-port">
          <video ref={videoRef} muted playsInline />
          {status === "boot" && <div className="cam-idle">CAMERA OFFLINE</div>}
          {scanning && <div className="sweep" />}
        </div>
        {lastDigit != null && <div className="digit-pop" key={lastDigit + ":" + progress}>{lastDigit}</div>}
      </div>

      {/* waveform — NOVA's real output spectrum */}
      <div className="wave">
        {bars.map((v, i) => <span key={i} style={{ height: `${8 + v * 72}px`, opacity: 0.35 + v * 0.65 }} />)}
      </div>
      <div className="mic-meter"><span style={{ width: `${micLevel * 100}%` }} /></div>

      {/* timer */}
      {scanning && (
        <div className="timer">
          <div className="timer-fill" style={{ width: `${pct}%`, background: pct < 25 ? "#fb7185" : pct < 55 ? "#fbbf24" : "#5ed7a6" }} />
          <span className="timer-num">{timeLeft}s</span>
        </div>
      )}

      {/* center CTA / verdict */}
      {status === "boot" && (
        <button className="cta" onClick={initiate}>▶ INITIATE NEURAL SYNC</button>
      )}
      {status === "granted" && (
        <div className="verdict granted">
          <div className="verdict-big">ACCESS GRANTED</div>
          <div className="verdict-sub">biometric identity confirmed — welcome back aboard, operator</div>
        </div>
      )}
      {(status === "lockout" || status === "lost") && (
        <div className="verdict lockout">
          <div className="verdict-big">{status === "lockout" ? "LOCKOUT" : "LINK LOST"}</div>
          <button className="cta small" onClick={initiate}>RETRY SYNC</button>
        </div>
      )}
      {scanning && <p className="hint">hold up <b>{sequence[progress]}</b> finger{sequence[progress] > 1 ? "s" : ""} · speak to NOVA anytime · speaking over her cuts her off</p>}

      {/* comms feed */}
      <div className="feed">
        {feed.slice(-6).map((l, i) => (
          <div key={i} className={`line who-${l.who}`}><span className="who">{l.who}</span>{l.text}</div>
        ))}
      </div>

      <footer className="bar foot">
        <span>gemini live · native audio · adk run_live</span>
        <span>mic 16 kHz ↑ · voice 24 kHz ↓ · frames 0.9 s ↑ · barge-in rms</span>
      </footer>
    </div>
  );
}

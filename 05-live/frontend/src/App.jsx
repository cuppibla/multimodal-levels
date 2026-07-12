import { useEffect, useRef, useState } from "react";
import { createStreamer, getAudioContext, startRecorder } from "./audio.js";

// NOVA live console — mic in, voice out, camera frames in, tool calls surfacing live.
export default function App() {
  const [status, setStatus] = useState("idle"); // idle | connecting | live | closed
  const [speaking, setSpeaking] = useState(false);
  const [digit, setDigit] = useState(null);
  const [transcript, setTranscript] = useState([]); // {who, text}
  const wsRef = useRef(null);
  const streamerRef = useRef(null);
  const stopRecRef = useRef(null);
  const videoRef = useRef(null);
  const frameTimerRef = useRef(null);
  const speakTimerRef = useRef(null);

  const pushLine = (who, text) =>
    setTranscript((t) => [...t.slice(-40), { who, text }]);

  async function openChannel() {
    setStatus("connecting");
    await getAudioContext().resume(); // unlock audio inside the user gesture
    streamerRef.current = createStreamer();

    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const session = Math.random().toString(36).slice(2, 9);
    const ws = new WebSocket(`${proto}//${location.host}/ws/operator/${session}`);
    wsRef.current = ws;

    ws.onopen = async () => {
      setStatus("live");
      // mic → 16k PCM binary frames; speech onset cuts NOVA (barge-in)
      stopRecRef.current = await startRecorder({
        onChunk: (buf) => { if (ws.readyState === 1) ws.send(buf); },
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
          speakTimerRef.current = setTimeout(() => setSpeaking(false), 600);
        }
        const fc = p.functionCall || p.function_call;
        if (fc?.name === "report_digit") {
          setDigit(fc.args?.count);
          pushLine("tool", `⚡ report_digit(${fc.args?.count})`);
        }
      }
      const inT = msg.inputTranscription || sc.inputTranscription;
      const outT = msg.outputTranscription || sc.outputTranscription;
      if (inT?.text) pushLine("you", inT.text);
      if (outT?.text) pushLine("nova", outT.text);
    };

    ws.onclose = () => { setStatus("closed"); cleanup(); };
    ws.onerror = () => { setStatus("closed"); cleanup(); };
  }

  async function startCamera(ws) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
      const canvas = document.createElement("canvas");
      canvas.width = 640; canvas.height = 480;
      frameTimerRef.current = setInterval(() => { // 1 fps is plenty for the handshake
        if (ws.readyState !== 1) return;
        canvas.getContext("2d").drawImage(videoRef.current, 0, 0, 640, 480);
        const b64 = canvas.toDataURL("image/jpeg", 0.6).split(",")[1];
        ws.send(JSON.stringify({ type: "image", mimeType: "image/jpeg", data: b64 }));
      }, 1000);
    } catch { pushLine("sys", "camera unavailable — voice-only mode"); }
  }

  function cleanup() {
    stopRecRef.current?.();
    clearInterval(frameTimerRef.current);
    streamerRef.current?.stop();
  }
  useEffect(() => () => { cleanup(); wsRef.current?.close(); }, []);

  return (
    <div className="console">
      <header>
        <span className="brand">WAY BACK HOME</span>
        <span className={`status s-${status}`}>{{ idle: "CHANNEL CLOSED", connecting: "SYNCING…", live: "◉ LIVE", closed: "LINK LOST" }[status]}</span>
      </header>

      <div className={`orb ${speaking ? "orb-speaking" : ""} ${status === "live" ? "orb-live" : ""}`} />
      <div className="nova-label">NOVA {speaking ? "· speaking" : status === "live" ? "· listening" : ""}</div>

      {digit != null && <div className="digit">BIOMETRIC MATCH — <b>{digit}</b> fingers</div>}

      {status === "idle" || status === "closed" ? (
        <button className="cta" onClick={openChannel}>
          {status === "closed" ? "RECONNECT" : "▶ OPEN LIVE CHANNEL"}
        </button>
      ) : (
        <p className="hint">speak naturally · hold up fingers for the neural sync · speak over NOVA to interrupt</p>
      )}

      <div className="stage">
        <video ref={videoRef} muted playsInline className="cam" />
        <div className="feed">
          {transcript.map((l, i) => (
            <div key={i} className={`line who-${l.who}`}>
              <span className="who">{l.who}</span> {l.text}
            </div>
          ))}
        </div>
      </div>

      <footer>Gemini Live · native audio · ADK run_live — mic 16 kHz ↑ · voice 24 kHz ↓ · frames 1 fps ↑</footer>
    </div>
  );
}

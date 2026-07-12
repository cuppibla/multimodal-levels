// The two halves of the voice loop (patterns from FashionMind):
//   Recorder — one shared 24 kHz AudioContext, worklet resamples → 16 kHz Int16 chunks,
//              RMS gate fires onSpeechStart (the barge-in trigger).
//   Streamer — 24 kHz PCM chunks scheduled GAPLESSLY at nextPlayTime; stop() = the cut.

const SILENCE_RMS_THRESHOLD = 0.012;

export function getAudioContext() {
  if (!window.__novaCtx) {
    window.__novaCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
  }
  return window.__novaCtx;
}

export async function startRecorder({ onChunk, onSpeechStart }) {
  const ctx = getAudioContext();
  if (ctx.state === "suspended") await ctx.resume();
  await ctx.audioWorklet.addModule("/pcm-processor.js");

  const stream = await navigator.mediaDevices.getUserMedia({
    audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
  });
  const source = ctx.createMediaStreamSource(stream);
  const node = new AudioWorkletNode(ctx, "pcm-processor", {
    processorOptions: { inputSampleRate: ctx.sampleRate },
  });

  let speaking = false;
  node.port.onmessage = (e) => {
    const { pcm, rms } = e.data;
    if (rms >= SILENCE_RMS_THRESHOLD) {
      if (!speaking) { speaking = true; onSpeechStart?.(); } // user spoke → cut NOVA instantly
    } else if (speaking && rms < SILENCE_RMS_THRESHOLD / 2) {
      speaking = false;
    }
    onChunk?.(pcm); // ArrayBuffer of Int16 s16le @16k — send as binary WS frame
  };

  source.connect(node); // worklet is a sink; nothing routes to speakers
  return () => { node.disconnect(); source.disconnect(); stream.getTracks().forEach((t) => t.stop()); };
}

export function createStreamer() {
  const ctx = getAudioContext();
  let nextPlayTime = 0;
  let active = [];

  // real spectrum for the HUD waveform — everything routes through one analyser
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 128;
  analyser.smoothingTimeConstant = 0.75;
  analyser.connect(ctx.destination);
  const bins = new Uint8Array(analyser.frequencyBinCount);

  return {
    analyser,
    /** 0..1 levels for n bars, straight off the live output spectrum */
    levels(n = 24) {
      analyser.getByteFrequencyData(bins);
      const out = new Array(n);
      const step = Math.floor(bins.length / n) || 1;
      for (let i = 0; i < n; i++) out[i] = (bins[i * step] || 0) / 255;
      return out;
    },
    // base64 24 kHz s16le PCM → schedule right after the previous chunk (no gaps)
    enqueue(b64) {
      const raw = atob(b64.replace(/-/g, "+").replace(/_/g, "/"));
      const n = raw.length / 2;
      const f32 = new Float32Array(n);
      for (let i = 0; i < n; i++) {
        let v = raw.charCodeAt(2 * i) | (raw.charCodeAt(2 * i + 1) << 8);
        if (v & 0x8000) v -= 0x10000;
        f32[i] = v / 32768;
      }
      const buf = ctx.createBuffer(1, n, 24000);
      buf.getChannelData(0).set(f32);
      const src = ctx.createBufferSource();
      src.buffer = buf;
      src.connect(analyser); // → analyser → destination (feeds the HUD waveform)
      const t = Math.max(ctx.currentTime, nextPlayTime);
      src.start(t);
      nextPlayTime = t + buf.duration;
      active.push(src);
      src.onended = () => { active = active.filter((s) => s !== src); };
    },
    // barge-in: kill everything scheduled, reset the clock
    stop() {
      active.forEach((s) => { try { s.stop(); } catch { /* already done */ } });
      active = [];
      nextPlayTime = getAudioContext().currentTime;
    },
    get speaking() { return active.length > 0; },
  };
}

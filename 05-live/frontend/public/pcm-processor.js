// AudioWorklet: capture mic audio, resample to 16 kHz, emit ~50 ms Int16 chunks.
// Gemini Live wants 16 kHz mono s16le PCM in 50–100 ms chunks; the context runs at the
// player's 24 kHz (shared context), so we linear-resample 24k → 16k here, off the main thread.
class PCMProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    this.inputRate = options.processorOptions?.inputSampleRate || sampleRate;
    this.targetRate = 16000;
    this.buffer = [];
    this.CHUNK = 800; // 800 samples @16k = 50 ms = 1600 bytes
  }

  process(inputs) {
    const input = inputs[0]?.[0];
    if (!input) return true;

    // linear resample inputRate → 16k
    const ratio = this.inputRate / this.targetRate;
    const outLen = Math.floor(input.length / ratio);
    for (let i = 0; i < outLen; i++) {
      const pos = i * ratio;
      const i0 = Math.floor(pos);
      const i1 = Math.min(i0 + 1, input.length - 1);
      const frac = pos - i0;
      this.buffer.push(input[i0] * (1 - frac) + input[i1] * frac);
    }

    while (this.buffer.length >= this.CHUNK) {
      const frame = this.buffer.splice(0, this.CHUNK);
      // RMS for client-side speech detection (barge-in)
      let sum = 0;
      for (const s of frame) sum += s * s;
      const rms = Math.sqrt(sum / frame.length);
      // Float32 [-1,1] → Int16
      const pcm16 = new Int16Array(this.CHUNK);
      for (let i = 0; i < this.CHUNK; i++) {
        const s = Math.max(-1, Math.min(1, frame[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      this.port.postMessage({ pcm: pcm16.buffer, rms }, [pcm16.buffer]);
    }
    return true;
  }
}
registerProcessor("pcm-processor", PCMProcessor);

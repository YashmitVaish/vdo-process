import { useState, useRef, useEffect } from "react";
import Hls from "hls.js";

const API = "http://localhost:8000";
const HLS_BASE = "http://localhost:8888/live";

// ─── HLS Video Player ────────────────────────────────────────────
function LivePlayer({ streamId }) {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [error, setError] = useState(null);
  const [buffering, setBuffering] = useState(true);

  useEffect(() => {
    if (!streamId || !videoRef.current) return;

    const url = `${HLS_BASE}/${streamId}/index.m3u8`;

    if (Hls.isSupported()) {
      const hls = new Hls({
        lowLatencyMode: true,
        liveSyncDurationCount: 2,
        liveMaxLatencyDurationCount: 4,
      });
      hlsRef.current = hls;
      hls.loadSource(url);
      hls.attachMedia(videoRef.current);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        videoRef.current.play().catch(() => {});
        setBuffering(false);
      });
      hls.on(Hls.Events.ERROR, (_, data) => {
        if (data.fatal) setError("Stream unavailable");
      });
    } else if (videoRef.current.canPlayType("application/vnd.apple.mpegurl")) {
      // Safari native HLS
      videoRef.current.src = url;
      videoRef.current.play().catch(() => {});
      setBuffering(false);
    } else {
      setError("HLS not supported in this browser");
    }

    return () => {
      hlsRef.current?.destroy();
    };
  }, [streamId]);

  return (
    <div className="player-wrap">
      {buffering && !error && (
        <div className="player-overlay">
          <div className="spinner" />
          <span>Connecting to stream...</span>
        </div>
      )}
      {error && (
        <div className="player-overlay error">
          <span className="error-icon">⚠</span>
          <span>{error}</span>
        </div>
      )}
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        controls
        className="video-el"
        style={{ opacity: buffering || error ? 0 : 1 }}
      />
    </div>
  );
}

// ─── Status Badge ─────────────────────────────────────────────────
function StatusBadge({ status }) {
  const map = {
    live: { label: "LIVE", cls: "live" },
    reconnecting: { label: "RECONNECTING", cls: "reconnecting" },
    stopped: { label: "STOPPED", cls: "stopped" },
    failed: { label: "FAILED", cls: "failed" },
  };
  const s = map[status] || { label: status?.toUpperCase() || "—", cls: "idle" };
  return <span className={`badge badge-${s.cls}`}>{s.label}</span>;
}

// ─── Main App ─────────────────────────────────────────────────────
export default function LiveStream() {
  const [rtspUrl, setRtspUrl] = useState("rtmp://localhost:1935/live/webcam");
  const [streamId, setStreamId] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  const pollStatus = (id) => {
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/streams/${id}/status`);
        if (res.ok) {
          const data = await res.json();
          setStatus(data.status);
          if (data.status === "stopped" || data.status === "failed") {
            clearInterval(pollRef.current);
          }
        }
      } catch {}
    }, 3000);
  };

  const startStream = async () => {
    if (!rtspUrl.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/streams/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rtsp_url: rtspUrl }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to start stream");
      setStreamId(data.stream_id);
      setStatus("live");
      pollStatus(data.stream_id);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const stopStream = async () => {
    if (!streamId) return;
    clearInterval(pollRef.current);
    try {
      await fetch(`${API}/streams/${streamId}/stop`, { method: "POST" });
    } catch {}
    setStatus("stopped");
    setStreamId(null);
  };

  useEffect(() => () => clearInterval(pollRef.current), []);

  return (
    <>
      <style>{CSS}</style>
      <div className="app">
        {/* Header */}
        <header className="header">
          <div className="header-left">
            <div className="logo-dot" />
            <span className="logo-text">STREAMFLOW</span>
          </div>
          {status && <StatusBadge status={status} />}
        </header>

        {/* Main */}
        <main className="main">
          {/* Player */}
          <section className="player-section">
            {streamId ? (
              <LivePlayer streamId={streamId} />
            ) : (
              <div className="player-empty">
                <div className="empty-icon">▶</div>
                <p>No active stream</p>
                <p className="empty-sub">Enter a source URL below and click Start</p>
              </div>
            )}
          </section>

          {/* Controls */}
          <section className="controls">
            <div className="input-row">
              <label className="input-label">SOURCE URL</label>
              <div className="input-group">
                <input
                  className="url-input"
                  value={rtspUrl}
                  onChange={(e) => setRtspUrl(e.target.value)}
                  placeholder="rtsp:// or rtmp://"
                  disabled={!!streamId || loading}
                />
                {!streamId ? (
                  <button
                    className="btn btn-start"
                    onClick={startStream}
                    disabled={loading || !rtspUrl.trim()}
                  >
                    {loading ? <span className="btn-spinner" /> : "START"}
                  </button>
                ) : (
                  <button className="btn btn-stop" onClick={stopStream}>
                    STOP
                  </button>
                )}
              </div>
              {error && <p className="error-msg">⚠ {error}</p>}
            </div>

            {/* Stream info */}
            {streamId && (
              <div className="stream-info">
                <div className="info-row">
                  <span className="info-label">STREAM ID</span>
                  <span className="info-val mono">{streamId}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">HLS URL</span>
                  <span className="info-val mono">
                    {HLS_BASE}/{streamId}/index.m3u8
                  </span>
                </div>
                <div className="info-row">
                  <span className="info-label">RTMP OUT</span>
                  <span className="info-val mono">
                    rtmp://localhost:1935/live/{streamId}
                  </span>
                </div>
              </div>
            )}
          </section>
        </main>
      </div>
    </>
  );
}

// ─── Styles ───────────────────────────────────────────────────────
const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0a0a0a;
    --surface: #111111;
    --border: #222222;
    --accent: #00ff87;
    --accent-dim: rgba(0,255,135,0.12);
    --red: #ff3b3b;
    --red-dim: rgba(255,59,59,0.12);
    --amber: #ffb800;
    --text: #f0f0f0;
    --muted: #555;
    --mono: 'Space Mono', monospace;
    --sans: 'DM Sans', sans-serif;
  }

  body { background: var(--bg); color: var(--text); font-family: var(--sans); }

  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Header */
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }
  .header-left { display: flex; align-items: center; gap: 10px; }
  .logo-dot {
    width: 10px; height: 10px;
    background: var(--accent);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--accent);
    animation: pulse 2s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
  .logo-text {
    font-family: var(--mono);
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.15em;
    color: var(--text);
  }

  /* Badges */
  .badge {
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    padding: 4px 10px;
    border-radius: 4px;
  }
  .badge-live { background: var(--accent-dim); color: var(--accent); border: 1px solid var(--accent); }
  .badge-reconnecting { background: rgba(255,184,0,0.12); color: var(--amber); border: 1px solid var(--amber); }
  .badge-stopped, .badge-idle { background: #1a1a1a; color: var(--muted); border: 1px solid var(--border); }
  .badge-failed { background: var(--red-dim); color: var(--red); border: 1px solid var(--red); }

  /* Main layout */
  .main {
    flex: 1;
    display: grid;
    grid-template-rows: 1fr auto;
    max-width: 1100px;
    width: 100%;
    margin: 0 auto;
    padding: 32px;
    gap: 24px;
  }

  /* Player */
  .player-section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    aspect-ratio: 16/9;
    position: relative;
  }
  .player-wrap { width: 100%; height: 100%; position: relative; background: #000; }
  .video-el { width: 100%; height: 100%; object-fit: contain; transition: opacity 0.3s; }
  .player-overlay {
    position: absolute; inset: 0;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 12px;
    background: #000;
    color: var(--muted);
    font-family: var(--mono);
    font-size: 13px;
  }
  .player-overlay.error { color: var(--red); }
  .error-icon { font-size: 28px; }
  .spinner {
    width: 28px; height: 28px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .player-empty {
    width: 100%; height: 100%;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 8px;
    color: var(--muted);
  }
  .empty-icon {
    font-size: 36px;
    color: #222;
    margin-bottom: 8px;
  }
  .empty-sub { font-size: 13px; color: #333; }

  /* Controls */
  .controls {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .input-label {
    display: block;
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.15em;
    color: var(--muted);
    margin-bottom: 8px;
  }
  .input-group { display: flex; gap: 10px; }
  .url-input {
    flex: 1;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 16px;
    color: var(--text);
    font-family: var(--mono);
    font-size: 13px;
    outline: none;
    transition: border-color 0.2s;
  }
  .url-input:focus { border-color: var(--accent); }
  .url-input:disabled { opacity: 0.4; cursor: not-allowed; }

  .btn {
    padding: 12px 24px;
    border: none;
    border-radius: 6px;
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.1em;
    cursor: pointer;
    transition: opacity 0.15s, transform 0.1s;
    display: flex; align-items: center; gap: 8px;
  }
  .btn:active { transform: scale(0.97); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-start { background: var(--accent); color: #000; }
  .btn-start:hover:not(:disabled) { opacity: 0.85; }
  .btn-stop { background: var(--red-dim); color: var(--red); border: 1px solid var(--red); }
  .btn-stop:hover { background: var(--red); color: #fff; }
  .btn-spinner {
    width: 14px; height: 14px;
    border: 2px solid rgba(0,0,0,0.3);
    border-top-color: #000;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  .error-msg {
    margin-top: 8px;
    font-size: 13px;
    color: var(--red);
    font-family: var(--mono);
  }

  /* Stream info */
  .stream-info {
    border-top: 1px solid var(--border);
    padding-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .info-row { display: flex; gap: 16px; align-items: baseline; }
  .info-label {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.12em;
    color: var(--muted);
    min-width: 80px;
    flex-shrink: 0;
  }
  .info-val {
    font-size: 12px;
    color: #888;
    word-break: break-all;
  }
  .mono { font-family: var(--mono); }
`;

import { useState } from "react";
import type { ArloCamera } from "../types";
import { api } from "../api/client";

interface Props {
  cameras: ArloCamera[];
  status: string;
}

const SIGNAL_BARS = ["▁", "▂", "▃", "▄", "█"];

function SignalIcon({ level }: { level: number | null }) {
  const bars = level ?? 0;
  return (
    <span style={{ fontSize: 13, letterSpacing: 1, color: "var(--text-muted)" }}>
      {SIGNAL_BARS.map((b, i) => (
        <span key={i} style={{ opacity: i < bars ? 1 : 0.25 }}>
          {b}
        </span>
      ))}
    </span>
  );
}

function BatteryIcon({ level }: { level: number | null }) {
  if (level === null) return <span style={{ color: "var(--text-muted)" }}>—</span>;
  const color = level > 40 ? "var(--green)" : level > 15 ? "var(--orange)" : "var(--red)";
  return (
    <span style={{ color, fontSize: 13, fontWeight: 500 }}>
      ⚡ {level}%
    </span>
  );
}

function CameraCard({ cam }: { cam: ArloCamera }) {
  const [loading, setLoading] = useState(false);
  const [imgUrl, setImgUrl] = useState<string | null>(cam.last_image);

  async function requestSnapshot() {
    setLoading(true);
    try {
      const result = await api.arlo.snapshot(cam.id) as { url?: string };
      if (result.url) setImgUrl(result.url);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.cameraCard}>
      {/* Snapshot */}
      <div style={styles.imageBox}>
        {imgUrl ? (
          <img src={imgUrl} alt={cam.name} style={styles.image} />
        ) : (
          <div style={styles.noImage}>
            <span style={{ fontSize: 32 }}>📷</span>
            <p style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 8 }}>No snapshot</p>
          </div>
        )}
      </div>

      {/* Info row */}
      <div style={styles.infoRow}>
        <div>
          <div style={styles.cameraName}>{cam.name}</div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>{cam.model}</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
          <BatteryIcon level={cam.battery} />
          <SignalIcon level={cam.signal} />
        </div>
      </div>

      {/* State + actions */}
      <div style={styles.footer}>
        <span style={{ ...styles.badge, background: cam.state === "idle" ? "rgba(63,185,80,0.15)" : "rgba(248,81,73,0.15)", color: cam.state === "idle" ? "var(--green)" : "var(--red)" }}>
          {cam.state}
        </span>
        <button style={styles.snapBtn} onClick={requestSnapshot} disabled={loading}>
          {loading ? "…" : "Snapshot"}
        </button>
      </div>
    </div>
  );
}

export function ArloCard({ cameras, status }: Props) {
  return (
    <section style={styles.section}>
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>Arlo Cameras</h2>
          <p style={styles.subtitle}>{cameras.length} camera{cameras.length !== 1 ? "s" : ""}</p>
        </div>
        <StatusBadge status={status} />
      </div>

      {cameras.length === 0 ? (
        <p style={{ color: "var(--text-muted)", padding: "24px 0" }}>No cameras found.</p>
      ) : (
        <div style={styles.grid}>
          {cameras.map((cam) => (
            <CameraCard key={cam.id} cam={cam} />
          ))}
        </div>
      )}
    </section>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; color: string; bg: string }> = {
    connected:     { label: "Live", color: "var(--green)", bg: "rgba(63,185,80,0.15)" },
    connecting:    { label: "Connecting…", color: "var(--orange)", bg: "rgba(240,136,62,0.15)" },
    not_configured:{ label: "Mock data", color: "var(--text-muted)", bg: "rgba(139,148,158,0.15)" },
    error:         { label: "Error", color: "var(--red)", bg: "rgba(248,81,73,0.15)" },
    timeout:       { label: "Timeout", color: "var(--red)", bg: "rgba(248,81,73,0.15)" },
    needs_2fa:     { label: "2FA required", color: "var(--orange)", bg: "rgba(240,136,62,0.15)" },
  };
  const s = map[status] ?? map["not_configured"];
  return (
    <span style={{ ...styles.badge, color: s.color, background: s.bg, padding: "4px 12px" }}>
      {s.label}
    </span>
  );
}

const styles: Record<string, React.CSSProperties> = {
  section: {
    background: "var(--surface)",
    borderRadius: "var(--radius)",
    padding: 24,
    border: "1px solid var(--border)",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 20,
  },
  title: { fontSize: 18, fontWeight: 600, color: "var(--text)" },
  subtitle: { fontSize: 13, color: "var(--text-muted)", marginTop: 2 },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
    gap: 16,
  },
  cameraCard: {
    background: "var(--surface2)",
    borderRadius: 10,
    border: "1px solid var(--border)",
    overflow: "hidden",
  },
  imageBox: {
    height: 140,
    background: "#0a0e14",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  image: { width: "100%", height: "100%", objectFit: "cover" },
  noImage: { display: "flex", flexDirection: "column", alignItems: "center" },
  infoRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 14px 8px",
  },
  cameraName: { fontWeight: 600, fontSize: 14 },
  footer: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "0 14px 14px",
  },
  badge: {
    fontSize: 11,
    fontWeight: 600,
    padding: "3px 8px",
    borderRadius: 20,
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  snapBtn: {
    fontSize: 12,
    padding: "5px 12px",
    borderRadius: 6,
    background: "var(--blue)",
    color: "#fff",
    fontWeight: 500,
  },
};

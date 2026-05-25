import { useState } from "react";
import type { NeothermZone } from "../types";
import { api } from "../api/client";

interface Props {
  zones: NeothermZone[];
  status: string;
}

const MODES = ["manual", "schedule", "eco", "off"] as const;
type Mode = (typeof MODES)[number];

const MODE_LABEL: Record<Mode, string> = {
  manual: "Manual",
  schedule: "Schedule",
  eco: "Eco",
  off: "Off",
};

function ZoneCard({ zone: initial }: { zone: NeothermZone }) {
  const [zone, setZone] = useState(initial);
  const [saving, setSaving] = useState(false);

  async function adjustTemp(delta: number) {
    const next = Math.round((zone.target_temp + delta) * 2) / 2; // 0.5° steps
    if (next < 5 || next > 35) return;
    setSaving(true);
    try {
      await api.neotherm.setTemperature(zone.id, next);
      setZone((z) => ({ ...z, target_temp: next, heating: next > z.current_temp }));
    } finally {
      setSaving(false);
    }
  }

  async function changeMode(mode: Mode) {
    setSaving(true);
    try {
      await api.neotherm.setMode(zone.id, mode);
      setZone((z) => ({ ...z, mode }));
    } finally {
      setSaving(false);
    }
  }

  const diff = zone.target_temp - zone.current_temp;
  const tempColor =
    diff > 1 ? "var(--heating)" : diff < -1 ? "var(--blue)" : "var(--green)";

  return (
    <div style={styles.zoneCard}>
      {/* Heating indicator strip */}
      <div
        style={{
          ...styles.heatingStrip,
          background: zone.heating ? "var(--heating)" : "transparent",
          opacity: zone.heating ? 1 : 0,
        }}
      />

      <div style={{ padding: "18px 18px 14px" }}>
        {/* Name + heating badge */}
        <div style={styles.zoneHeader}>
          <span style={styles.zoneName}>{zone.name}</span>
          {zone.heating && (
            <span style={styles.heatingBadge}>🔥 Heating</span>
          )}
        </div>

        {/* Temperature display */}
        <div style={styles.tempRow}>
          <div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 2 }}>
              CURRENT
            </div>
            <div style={{ fontSize: 36, fontWeight: 700, color: tempColor }}>
              {zone.current_temp.toFixed(1)}°
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
              Floor {zone.floor_temp.toFixed(1)}°
            </div>
          </div>

          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>
              TARGET
            </div>
            <div style={styles.tempControls}>
              <button
                style={styles.tempBtn}
                onClick={() => adjustTemp(-0.5)}
                disabled={saving}
              >
                −
              </button>
              <span style={styles.targetTemp}>
                {zone.target_temp.toFixed(1)}°
              </span>
              <button
                style={styles.tempBtn}
                onClick={() => adjustTemp(0.5)}
                disabled={saving}
              >
                +
              </button>
            </div>
          </div>
        </div>

        {/* Mode selector */}
        <div style={styles.modeRow}>
          {MODES.map((m) => (
            <button
              key={m}
              style={{
                ...styles.modeBtn,
                background:
                  zone.mode === m ? "var(--blue)" : "var(--surface)",
                color: zone.mode === m ? "#fff" : "var(--text-muted)",
              }}
              onClick={() => changeMode(m)}
              disabled={saving}
            >
              {MODE_LABEL[m]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export function NeothermCard({ zones, status }: Props) {
  const heatingCount = zones.filter((z) => z.heating).length;

  return (
    <section style={styles.section}>
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>Neotherm Floor Heating</h2>
          <p style={styles.subtitle}>
            {zones.length} zone{zones.length !== 1 ? "s" : ""}
            {heatingCount > 0 && ` · ${heatingCount} heating`}
          </p>
        </div>
        <StatusBadge status={status} />
      </div>

      {zones.length === 0 ? (
        <p style={{ color: "var(--text-muted)", padding: "24px 0" }}>No zones found.</p>
      ) : (
        <div style={styles.grid}>
          {zones.map((z) => (
            <ZoneCard key={z.id} zone={z} />
          ))}
        </div>
      )}
    </section>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; color: string; bg: string }> = {
    connected: { label: "Live", color: "var(--green)", bg: "rgba(63,185,80,0.15)" },
    mock:      { label: "Mock data", color: "var(--text-muted)", bg: "rgba(139,148,158,0.15)" },
    error:     { label: "Error", color: "var(--red)", bg: "rgba(248,81,73,0.15)" },
  };
  const s = map[status] ?? map["mock"];
  return (
    <span
      style={{
        fontSize: 11,
        fontWeight: 600,
        padding: "4px 12px",
        borderRadius: 20,
        textTransform: "uppercase",
        letterSpacing: "0.5px",
        color: s.color,
        background: s.bg,
      }}
    >
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
  title: { fontSize: 18, fontWeight: 600 },
  subtitle: { fontSize: 13, color: "var(--text-muted)", marginTop: 2 },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
    gap: 16,
  },
  zoneCard: {
    background: "var(--surface2)",
    borderRadius: 10,
    border: "1px solid var(--border)",
    overflow: "hidden",
    position: "relative",
  },
  heatingStrip: {
    height: 3,
    transition: "opacity 0.3s",
  },
  zoneHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  zoneName: { fontWeight: 600, fontSize: 15 },
  heatingBadge: {
    fontSize: 11,
    fontWeight: 600,
    padding: "3px 8px",
    borderRadius: 20,
    background: "rgba(255,107,53,0.2)",
    color: "var(--heating)",
  },
  tempRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-end",
    marginBottom: 14,
  },
  tempControls: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  targetTemp: {
    fontSize: 22,
    fontWeight: 700,
    minWidth: 64,
    textAlign: "center",
  },
  tempBtn: {
    width: 28,
    height: 28,
    borderRadius: 6,
    background: "var(--surface)",
    color: "var(--text)",
    fontSize: 16,
    fontWeight: 700,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    border: "1px solid var(--border)",
  },
  modeRow: {
    display: "flex",
    gap: 6,
    flexWrap: "wrap",
  },
  modeBtn: {
    fontSize: 11,
    fontWeight: 500,
    padding: "4px 10px",
    borderRadius: 6,
    border: "1px solid var(--border)",
    transition: "background 0.15s",
  },
};

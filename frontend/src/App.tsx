import { useEffect, useRef, useState } from "react";
import { ArloCard } from "./components/ArloCard";
import { NeothermCard } from "./components/NeothermCard";
import { api } from "./api/client";
import type { ArloCamera, DeviceOverview, NeothermZone } from "./types";

const REFRESH_MS = 30_000;

interface State {
  overview: DeviceOverview | null;
  cameras: ArloCamera[];
  zones: NeothermZone[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

function useFmt(date: Date | null) {
  if (!date) return "—";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function App() {
  const [state, setState] = useState<State>({
    overview: null,
    cameras: [],
    zones: [],
    loading: true,
    error: null,
    lastUpdated: null,
  });

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function fetchAll() {
    try {
      const [overview, cameras, zones] = await Promise.all([
        api.devices() as Promise<DeviceOverview>,
        api.arlo.cameras() as Promise<ArloCamera[]>,
        api.neotherm.zones() as Promise<NeothermZone[]>,
      ]);
      setState((s) => ({ ...s, overview, cameras, zones, loading: false, error: null, lastUpdated: new Date() }));
    } catch (e) {
      setState((s) => ({ ...s, loading: false, error: String(e) }));
    }
  }

  useEffect(() => {
    fetchAll();
    timerRef.current = setInterval(fetchAll, REFRESH_MS);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, []);

  const lastUpdated = useFmt(state.lastUpdated);

  return (
    <div style={styles.shell}>
      {/* Sidebar */}
      <aside style={styles.sidebar}>
        <div style={styles.logo}>
          <span style={{ fontSize: 22 }}>🏠</span>
          <span style={styles.logoText}>Home Hub</span>
        </div>
        <nav style={styles.nav}>
          <NavItem icon="📷" label="Cameras" active />
          <NavItem icon="🌡️" label="Heating" />
        </nav>
        <div style={styles.sidebarFooter}>
          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Updated</div>
          <div style={{ fontSize: 12, color: "var(--text)", marginTop: 2 }}>{lastUpdated}</div>
          <button style={styles.refreshBtn} onClick={fetchAll}>
            ↻ Refresh
          </button>
        </div>
      </aside>

      {/* Main */}
      <main style={styles.main}>
        <header style={styles.pageHeader}>
          <h1 style={styles.pageTitle}>Dashboard</h1>
          {state.loading && <span style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading…</span>}
          {state.error && (
            <span style={{ color: "var(--red)", fontSize: 13 }}>
              ⚠ {state.error} — is the backend running?
            </span>
          )}
        </header>

        {/* Summary row */}
        {state.overview && (
          <div style={styles.summaryRow}>
            <SummaryTile
              icon="📷"
              label="Cameras"
              value={state.overview.arlo.camera_count}
              status={state.overview.arlo.status}
            />
            <SummaryTile
              icon="🌡️"
              label="Heating zones"
              value={state.overview.neotherm.zone_count}
              status={state.overview.neotherm.status}
            />
            <SummaryTile
              icon="🔥"
              label="Heating active"
              value={state.zones.filter((z) => z.heating).length}
            />
            <SummaryTile
              icon="🌡"
              label="Avg temperature"
              value={
                state.zones.length
                  ? (state.zones.reduce((s, z) => s + z.current_temp, 0) / state.zones.length).toFixed(1) + "°"
                  : "—"
              }
            />
          </div>
        )}

        <div style={styles.cards}>
          <ArloCard
            cameras={state.cameras}
            status={state.overview?.arlo.status ?? "loading"}
          />
          <NeothermCard
            zones={state.zones}
            status={state.overview?.neotherm.status ?? "loading"}
          />
        </div>
      </main>
    </div>
  );
}

function NavItem({ icon, label, active }: { icon: string; label: string; active?: boolean }) {
  return (
    <div
      style={{
        ...styles.navItem,
        background: active ? "rgba(56,139,253,0.15)" : "transparent",
        color: active ? "var(--blue)" : "var(--text-muted)",
      }}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </div>
  );
}

function SummaryTile({
  icon,
  label,
  value,
  status,
}: {
  icon: string;
  label: string;
  value: number | string;
  status?: string;
}) {
  return (
    <div style={styles.summaryTile}>
      <div style={styles.summaryIcon}>{icon}</div>
      <div>
        <div style={styles.summaryValue}>{value}</div>
        <div style={styles.summaryLabel}>{label}</div>
        {status && (
          <div
            style={{
              fontSize: 10,
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              color:
                status === "connected"
                  ? "var(--green)"
                  : status === "mock"
                  ? "var(--text-muted)"
                  : "var(--orange)",
              marginTop: 2,
            }}
          >
            {status}
          </div>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  shell: {
    display: "flex",
    minHeight: "100vh",
  },
  sidebar: {
    width: 200,
    background: "var(--surface)",
    borderRight: "1px solid var(--border)",
    display: "flex",
    flexDirection: "column",
    padding: "20px 0",
    flexShrink: 0,
  },
  logo: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "0 20px 20px",
    borderBottom: "1px solid var(--border)",
  },
  logoText: { fontSize: 16, fontWeight: 700 },
  nav: { padding: "16px 10px", flex: 1 },
  navItem: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "8px 10px",
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 500,
    cursor: "pointer",
    marginBottom: 4,
  },
  sidebarFooter: {
    padding: "0 16px 4px",
    borderTop: "1px solid var(--border)",
    paddingTop: 16,
  },
  refreshBtn: {
    marginTop: 10,
    width: "100%",
    padding: "7px 0",
    borderRadius: 8,
    background: "var(--surface2)",
    color: "var(--text-muted)",
    fontSize: 13,
    border: "1px solid var(--border)",
  },
  main: {
    flex: 1,
    padding: "28px 32px",
    overflowY: "auto",
  },
  pageHeader: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    marginBottom: 24,
  },
  pageTitle: { fontSize: 26, fontWeight: 700 },
  summaryRow: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
    gap: 12,
    marginBottom: 24,
  },
  summaryTile: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius)",
    padding: "16px 18px",
    display: "flex",
    alignItems: "center",
    gap: 12,
  },
  summaryIcon: { fontSize: 24 },
  summaryValue: { fontSize: 22, fontWeight: 700 },
  summaryLabel: { fontSize: 12, color: "var(--text-muted)", marginTop: 1 },
  cards: { display: "flex", flexDirection: "column", gap: 20 },
};

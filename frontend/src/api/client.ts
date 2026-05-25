const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  devices: () => get("/devices"),
  arlo: {
    cameras: () => get("/arlo/cameras"),
    mode: () => get("/arlo/mode"),
    snapshot: (id: string) => post(`/arlo/cameras/${id}/snapshot`),
    setMode: (baseId: string, mode: string) =>
      post(`/arlo/base/${baseId}/mode`, { mode }),
  },
  neotherm: {
    zones: () => get("/neotherm/zones"),
    setTemperature: (zoneId: string, target: number) =>
      post(`/neotherm/zones/${zoneId}/temperature`, { target }),
    setMode: (zoneId: string, mode: string) =>
      post(`/neotherm/zones/${zoneId}/mode`, { mode }),
  },
};

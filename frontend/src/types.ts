export interface ArloCamera {
  id: string;
  name: string;
  battery: number | null;
  signal: number | null;
  state: string;
  last_image: string | null;
  model: string;
}

export interface NeothermZone {
  id: string;
  name: string;
  current_temp: number;
  target_temp: number;
  heating: boolean;
  mode: "manual" | "schedule" | "eco" | "off";
  floor_temp: number;
}

export interface DeviceOverview {
  arlo: { status: string; camera_count: number };
  neotherm: { status: string; zone_count: number };
}

// Reads from Vite env at build time. Set VITE_API_BASE when deploying
// (e.g. VITE_API_BASE=https://geoshield-api.onrender.com).
export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
export const WS_BASE = API_BASE.replace(/^http/, "ws");

export type RiskLevel = "Safe" | "Watch" | "Warning" | "Danger" | "Unknown";

export interface SensorReading {
  sensor_id: number;
  name: string;
  corridor: string;
  latitude: number;
  longitude: number;
  risk_label: RiskLevel;
  risk_probability: number | null;
  top_factors: { factor: string; impact: number }[];
  last_updated: string | null;
}

export interface AlertItem {
  id: number;
  sensor_id: number | null;
  level: string;
  message_en: string;
  message_hi?: string | null;
  message_as?: string | null;
  issued_by: string;
  created_at: string;
}

export interface SOSItem {
  id: number;
  latitude: number;
  longitude: number;
  note?: string | null;
  contact?: string | null;
  status: string;
  created_at: string;
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  latestReadings: () => fetch(`${API_BASE}/readings/latest`).then((r) => json<SensorReading[]>(r)),

  alerts: (limit = 20) => fetch(`${API_BASE}/alerts?limit=${limit}`).then((r) => json<AlertItem[]>(r)),

  createAlert: (payload: {
    sensor_id?: number | null;
    level: string;
    message_en: string;
    message_hi?: string;
    message_as?: string;
    issued_by?: string;
  }) =>
    fetch(`${API_BASE}/alerts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => json<AlertItem>(r)),

  sendSOS: (payload: { latitude: number; longitude: number; note?: string; contact?: string }) =>
    fetch(`${API_BASE}/sos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => json<SOSItem>(r)),

  listSOS: (status?: string) =>
    fetch(`${API_BASE}/sos${status ? `?status=${status}` : ""}`).then((r) => json<SOSItem[]>(r)),

  updateSOS: (id: number, status: string) =>
    fetch(`${API_BASE}/sos/${id}?status=${status}`, { method: "PATCH" }).then((r) => json<SOSItem>(r)),
};

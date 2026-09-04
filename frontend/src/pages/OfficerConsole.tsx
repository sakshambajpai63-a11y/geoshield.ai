import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, AlertItem, SensorReading, SOSItem } from "../lib/api";
import { useLiveFeed } from "../lib/useLiveFeed";
import { RiskMap } from "../components/RiskMap";
import { RiskBadge } from "../components/RiskBadge";

export default function OfficerConsole() {
  const [readings, setReadings] = useState<SensorReading[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [sos, setSos] = useState<SOSItem[]>([]);
  const [selected, setSelected] = useState<SensorReading | null>(null);
  const [broadcast, setBroadcast] = useState("");
  const [sending, setSending] = useState(false);
  const { connected } = useLiveFeed((evt) => {
    if (evt.type === "reading") {
      setReadings((prev) => {
        const others = prev.filter((r) => r.sensor_id !== evt.data.sensor_id);
        return [
          ...others,
          {
            sensor_id: evt.data.sensor_id,
            name: evt.data.sensor_name,
            corridor: evt.data.corridor ?? "",
            latitude: evt.data.latitude,
            longitude: evt.data.longitude,
            risk_label: evt.data.risk_label,
            risk_probability: evt.data.risk_probability,
            top_factors: evt.data.top_factors ?? [],
            last_updated: evt.data.timestamp,
          },
        ];
      });
    }
    if (evt.type === "alert") setAlerts((prev) => [evt.data, ...prev].slice(0, 30));
    if (evt.type === "sos") setSos((prev) => [evt.data, ...prev]);
  });

  useEffect(() => {
    api.latestReadings().then(setReadings).catch(() => {});
    api.alerts(30).then(setAlerts).catch(() => {});
    api.listSOS("open").then(setSos).catch(() => {});
  }, []);

  function issueBroadcast() {
    if (!selected || !broadcast.trim()) return;
    setSending(true);
    api
      .createAlert({
        sensor_id: selected.sensor_id,
        level: selected.risk_label,
        message_en: broadcast.trim(),
        issued_by: "officer",
      })
      .then(() => setBroadcast(""))
      .finally(() => setSending(false));
  }

  function resolveSOS(id: number) {
    api.updateSOS(id, "resolved").then(() => setSos((prev) => prev.filter((s) => s.id !== id)));
  }

  const counts = readings.reduce<Record<string, number>>((acc, r) => {
    acc[r.risk_label] = (acc[r.risk_label] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="grid h-screen grid-rows-[auto_1fr] bg-slate-900 text-neutral-100">
      <header className="flex items-center justify-between border-b border-white/10 px-5 py-3">
        <div className="flex items-center gap-3">
          <h1 className="text-base font-semibold">GeoShield AI — Officer Console</h1>
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs ${
              connected ? "bg-teal-700/40 text-teal-300" : "bg-white/10 text-neutral-400"
            }`}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-teal-400" : "bg-neutral-500"}`} />
            {connected ? "Live" : "Reconnecting…"}
          </span>
        </div>
        <Link to="/" className="text-sm text-teal-300 hover:underline">
          ← Citizen portal
        </Link>
      </header>

      <div className="grid grid-cols-1 gap-4 overflow-hidden p-4 lg:grid-cols-[1fr_360px]">
        {/* Map + status strip */}
        <div className="flex min-h-0 flex-col gap-4">
          <div className="flex gap-3">
            {(["Safe", "Watch", "Warning", "Danger"] as const).map((lvl) => (
              <div key={lvl} className="flex-1 rounded-lg border border-white/10 bg-slate-800 p-3">
                <div className="text-xs text-neutral-400">{lvl}</div>
                <div className="text-2xl font-semibold">{counts[lvl] ?? 0}</div>
              </div>
            ))}
          </div>
          <div className="min-h-0 flex-1 overflow-hidden rounded-xl border border-white/10">
            <RiskMap readings={readings} dark onSelect={setSelected} />
          </div>
        </div>

        {/* Right rail: sensor detail + broadcast + SOS queue */}
        <div className="flex min-h-0 flex-col gap-4 overflow-y-auto">
          <div className="rounded-xl border border-white/10 bg-slate-800 p-4">
            <h2 className="mb-2 text-sm font-semibold text-neutral-300">Selected sensor</h2>
            {selected ? (
              <div>
                <div className="mb-1 flex items-center justify-between">
                  <span className="font-medium">{selected.name}</span>
                  <RiskBadge level={selected.risk_label} size="sm" />
                </div>
                <p className="mb-2 text-xs text-neutral-400">{selected.corridor}</p>
                {selected.top_factors?.length > 0 && (
                  <ul className="mb-3 space-y-1 text-xs text-neutral-400">
                    {selected.top_factors.map((f) => (
                      <li key={f.factor}>
                        {f.factor.replace(/_/g, " ")}: impact {f.impact.toFixed(3)}
                      </li>
                    ))}
                  </ul>
                )}
                <textarea
                  value={broadcast}
                  onChange={(e) => setBroadcast(e.target.value)}
                  placeholder="Broadcast message to citizens near this sensor…"
                  className="mb-2 w-full rounded-md border border-white/10 bg-slate-900 p-2 text-sm text-neutral-100 placeholder:text-neutral-500"
                  rows={3}
                />
                <button
                  onClick={issueBroadcast}
                  disabled={sending || !broadcast.trim()}
                  className="w-full rounded-md bg-teal-600 px-3 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
                >
                  {sending ? "Sending…" : "Issue broadcast"}
                </button>
              </div>
            ) : (
              <p className="text-sm text-neutral-500">Click a sensor on the map to view details and broadcast an alert.</p>
            )}
          </div>

          <div className="rounded-xl border border-white/10 bg-slate-800 p-4">
            <h2 className="mb-2 text-sm font-semibold text-neutral-300">Open SOS reports ({sos.length})</h2>
            {sos.length === 0 ? (
              <p className="text-sm text-neutral-500">None right now.</p>
            ) : (
              <ul className="space-y-2">
                {sos.map((s) => (
                  <li key={s.id} className="rounded-md border border-white/10 bg-slate-900 p-2 text-sm">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-neutral-300">
                        {s.latitude.toFixed(4)}, {s.longitude.toFixed(4)}
                      </span>
                      <button
                        onClick={() => resolveSOS(s.id)}
                        className="text-xs text-teal-300 hover:underline"
                      >
                        Mark resolved
                      </button>
                    </div>
                    <span className="text-xs text-neutral-500">
                      {new Date(s.created_at).toLocaleTimeString()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-xl border border-white/10 bg-slate-800 p-4">
            <h2 className="mb-2 text-sm font-semibold text-neutral-300">Recent alerts</h2>
            <ul className="space-y-2">
              {alerts.slice(0, 8).map((a) => (
                <li key={a.id} className="text-sm">
                  <div className="flex items-center justify-between">
                    <RiskBadge level={a.level as any} size="sm" />
                    <span className="text-xs text-neutral-500">{a.issued_by}</span>
                  </div>
                  <p className="text-neutral-400">{a.message_en}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

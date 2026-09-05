import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { SensorReading, RiskLevel } from "../lib/api";

const RISK_HEX: Record<RiskLevel, string> = {
  Safe: "#2E7D4F",
  Watch: "#B8842E",
  Warning: "#CC5A26",
  Danger: "#B0362E",
  Unknown: "#9CA3AF",
};

const RISK_RADIUS: Record<RiskLevel, number> = {
  Safe: 8,
  Watch: 10,
  Warning: 13,
  Danger: 16,
  Unknown: 6,
};

export function RiskMap({
  readings,
  dark = false,
  onSelect,
}: {
  readings: SensorReading[];
  dark?: boolean;
  onSelect?: (r: SensorReading) => void;
}) {
  const center: [number, number] =
    readings.length > 0 ? [readings[0].latitude, readings[0].longitude] : [26.2, 92.9]; // NER centroid fallback

  return (
    <MapContainer center={center} zoom={7} className="h-full w-full" scrollWheelZoom>
      <TileLayer attribution='&copy;OpenStreetMap contributors' url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"/>
      {readings.map((r) => (
        <CircleMarker
          key={r.sensor_id}
          center={[r.latitude, r.longitude]}
          radius={RISK_RADIUS[r.risk_label] ?? 8}
          pathOptions={{
            color: RISK_HEX[r.risk_label] ?? RISK_HEX.Unknown,
            fillColor: RISK_HEX[r.risk_label] ?? RISK_HEX.Unknown,
            fillOpacity: 0.55,
            weight: 2,
          }}
          eventHandlers={{ click: () => onSelect?.(r) }}
        >
          <Popup>
            <div className="text-sm">
              <div className="font-semibold">{r.name}</div>
              <div className="text-neutral-500">{r.corridor}</div>
              <div className="mt-1">
                Risk: <strong>{r.risk_label}</strong>
                {r.risk_probability != null && ` (${Math.round(r.risk_probability * 100)}%)`}
              </div>
              {r.top_factors?.length > 0 && (
                <div className="mt-1 text-neutral-500">
                  Driven by: {r.top_factors.map((f) => f.factor.replace(/_/g, " ")).join(", ")}
                </div>
              )}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}

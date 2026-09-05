import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, AlertItem, SensorReading } from "../lib/api";
import { useLiveFeed } from "../lib/useLiveFeed";
import { RiskMap } from "../components/RiskMap";
import { RiskBadge } from "../components/RiskBadge";

const LANGS = { en: "English", hi: "हिंदी", as: "অসমীয়া" } as const;
type Lang = keyof typeof LANGS;

const STRINGS: Record<Lang, { title: string; sub: string; sos: string; sosSending: string; sosSent: string; feedTitle: string; empty: string }> = {
  en: {
    title: "GeoShield AI",
    sub: "Landslide risk & public safety — North Eastern Region",
    sos: "Send SOS with my location",
    sosSending: "Sending…",
    sosSent: "Help is on the way. Stay where you are if it's safe.",
    feedTitle: "Active alerts",
    empty: "No active alerts right now. Corridors are being monitored continuously.",
  },
  hi: {
    title: "जियोशील्ड AI",
    sub: "भूस्खलन जोखिम व सार्वजनिक सुरक्षा — पूर्वोत्तर क्षेत्र",
    sos: "अपना स्थान भेजकर SOS करें",
    sosSending: "भेजा जा रहा है…",
    sosSent: "मदद आ रही है। यदि सुरक्षित है तो वहीं रुकें।",
    feedTitle: "सक्रिय अलर्ट",
    empty: "अभी कोई सक्रिय अलर्ट नहीं है। मार्गों की लगातार निगरानी की जा रही है।",
  },
  as: {
    title: "জিঅ'শ্বীল্ড AI",
    sub: "ভূমিস্খলন বিপদ আৰু ৰাজহুৱা সুৰক্ষা — উত্তৰ-পূৱ অঞ্চল",
    sos: "মোৰ অৱস্থানসহ SOS পঠিয়াওক",
    sosSending: "পঠিওৱা হৈছে…",
    sosSent: "সহায় আহি আছে। সুৰক্ষিত হ'লে তাতেই থাকক।",
    feedTitle: "সক্ৰিয় সতৰ্কবাণী",
    empty: "এই মুহূৰ্তত কোনো সক্ৰিয় সতৰ্কবাণী নাই। পথসমূহ নিৰন্তৰ নিৰীক্ষণ কৰা হৈছে।",
  },
};

export default function CitizenPortal() {
  const [lang, setLang] = useState<Lang>("en");
  const [readings, setReadings] = useState<SensorReading[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [sosState, setSosState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const t = STRINGS[lang];

  useEffect(() => {
    api.latestReadings().then(setReadings).catch(() => {});
    api.alerts().then(setAlerts).catch(() => {});
  }, []);

  useLiveFeed((evt) => {
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
    if (evt.type === "alert") {
      setAlerts((prev) => [evt.data, ...prev].slice(0, 20));
    }
  });

  function sendSOS() {
    setSosState("sending");
    if (!navigator.geolocation) {
      setSosState("error");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        api
          .sendSOS({ latitude: pos.coords.latitude, longitude: pos.coords.longitude })
          .then(() => setSosState("sent"))
          .catch(() => setSosState("error"));
      },
      () => setSosState("error"),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  const worstLevel = ["Danger", "Warning", "Watch", "Safe"].find((lvl) =>
    readings.some((r) => r.risk_label === lvl)
  );

  return (
    <div className="min-h-screen bg-mist-50 text-neutral-900">
      <header className="border-b border-mist-200 bg-white px-5 py-4">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">{t.title}</h1>
            <p className="text-sm text-neutral-500">{t.sub}</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value as Lang)}
              className="rounded-md border border-mist-200 bg-white px-2 py-1.5 text-sm"
              aria-label="Language"
            >
              {Object.entries(LANGS).map(([code, label]) => (
                <option key={code} value={code}>
                  {label}
                </option>
              ))}
            </select>
            <Link to="/officer" className="text-sm text-teal-600 hover:underline">
              Officer console →
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-5 py-5">
        {/* SOS — always above the fold, unmissable */}
        <div className="mb-5 rounded-xl border border-mist-200 bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm text-neutral-500">Current regional status</div>
              {worstLevel ? (
                <div className="mt-1">
                  <RiskBadge level={worstLevel as any} />
                </div>
              ) : (
                <div className="mt-1 text-sm text-neutral-400">Loading…</div>
              )}
            </div>
            <button
              onClick={sendSOS}
              disabled={sosState === "sending"}
              className="rounded-lg bg-status-danger px-5 py-3 font-semibold text-white shadow-sm transition hover:brightness-110 disabled:opacity-60"
            >
              {sosState === "sending" ? t.sosSending : t.sos}
            </button>
          </div>
          {sosState === "sent" && (
            <p className="mt-3 rounded-md bg-[#E7F1EA] px-3 py-2 text-sm text-[#1E5636]">{t.sosSent}</p>
          )}
          {sosState === "error" && (
            <p className="mt-3 rounded-md bg-[#F5DEDC] px-3 py-2 text-sm text-[#7C2620]">
              Couldn't get your location. Check location permissions and try again.
            </p>
          )}
        </div>

        {/* Emergency helplines */}
        <div className="mb-5 rounded-xl border border-mist-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-neutral-500">
            Emergency helplines
          </h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            
              href="tel:112"
              className="rounded-lg border border-mist-200 p-3 text-center transition hover:bg-mist-50"
            >
              <div className="text-lg font-bold text-teal-700">112</div>
              <div className="text-xs text-neutral-500">National Emergency</div>
            </a>
            
              href="tel:1070"
              className="rounded-lg border border-mist-200 p-3 text-center transition hover:bg-mist-50"
            >
              <div className="text-lg font-bold text-teal-700">1070</div>
              <div className="text-xs text-neutral-500">Disaster Mgmt (MHA)</div>
            </a>
            
              href="tel:100"
              className="rounded-lg border border-mist-200 p-3 text-center transition hover:bg-mist-50"
            >
              <div className="text-lg font-bold text-teal-700">100</div>
              <div className="text-xs text-neutral-500">Police</div>
            </a>
            
              href="tel:108"
              className="rounded-lg border border-mist-200 p-3 text-center transition hover:bg-mist-50"
            >
              <div className="text-lg font-bold text-teal-700">108</div>
              <div className="text-xs text-neutral-500">Ambulance</div>
            </a>
          </div>
        </div>

        {/* Map */}
        <div className="mb-5 h-80 overflow-hidden rounded-xl border border-mist-200 sm:h-96">
          <RiskMap readings={readings} />
        </div>

        {/* Alert feed */}
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-neutral-500">
            {t.feedTitle}
          </h2>
          {alerts.length === 0 ? (
            <p className="rounded-lg border border-dashed border-mist-200 bg-white p-4 text-sm text-neutral-500">
              {t.empty}
            </p>
          ) : (
            <ul className="space-y-2">
              {alerts.map((a) => (
                <li key={a.id} className="rounded-lg border border-mist-200 bg-white p-3">
                  <div className="mb-1 flex items-center justify-between">
                    <RiskBadge level={a.level as any} size="sm" />
                    <span className="text-xs text-neutral-400">
                      {new Date(a.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm">
                    {lang === "hi" && a.message_hi ? a.message_hi : lang === "as" && a.message_as ? a.message_as : a.message_en}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}

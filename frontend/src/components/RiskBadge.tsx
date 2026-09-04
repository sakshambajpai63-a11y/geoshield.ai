import { RiskLevel } from "../lib/api";

const STYLES: Record<RiskLevel, { bg: string; text: string; dot: string }> = {
  Safe: { bg: "bg-[#E7F1EA]", text: "text-[#1E5636]", dot: "bg-status-safe" },
  Watch: { bg: "bg-[#F6EEDD]", text: "text-[#7A5A1E]", dot: "bg-status-watch" },
  Warning: { bg: "bg-[#F7E5DA]", text: "text-[#8C3F1B]", dot: "bg-status-warning" },
  Danger: { bg: "bg-[#F5DEDC]", text: "text-[#7C2620]", dot: "bg-status-danger" },
  Unknown: { bg: "bg-mist-200", text: "text-neutral-600", dot: "bg-neutral-400" },
};

export function RiskBadge({ level, size = "md" }: { level: RiskLevel; size?: "sm" | "md" }) {
  const s = STYLES[level] ?? STYLES.Unknown;
  const pad = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-medium ${pad} ${s.bg} ${s.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} aria-hidden />
      {level}
    </span>
  );
}

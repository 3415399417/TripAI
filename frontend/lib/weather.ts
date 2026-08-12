export function weatherEmoji(weather: string | null | undefined): string {
  const w = weather ?? "";
  if (w.includes("雷")) return "⛈️";
  if (w.includes("雪")) return "❄️";
  if (w.includes("雨")) return "🌧️";
  if (w.includes("晴")) return "☀️";
  if (w.includes("多云")) return "⛅";
  if (w.includes("阴")) return "☁️";
  if (w.includes("雾") || w.includes("霾")) return "🌫️";
  return "🌤️";
}

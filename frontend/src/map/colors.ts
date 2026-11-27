// Échelle séquentielle à 5 classes (bleu clair → bleu foncé), lisible en clair et en sombre.
export const SCALE = ["#dbe9f6", "#9ecae1", "#5ea3cf", "#2b72b0", "#0b3c78"];
export const NO_DATA = "#9aa0a6";
export const BREAKS = [0.2, 0.4, 0.6, 0.8]; // limites des classes sur [0, 1]

export function scoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined || Number.isNaN(score)) return NO_DATA;
  const i = BREAKS.findIndex((b) => score < b);
  return SCALE[i === -1 ? SCALE.length - 1 : i];
}

export function legendItems(): { color: string; label: string }[] {
  const edges = [0, ...BREAKS, 1];
  return SCALE.map((c, i) => ({ color: c, label: `${edges[i].toFixed(1)} – ${edges[i + 1].toFixed(1)}` }));
}

import { featureValue } from "../labels";
import type { Language, RegionScore } from "../types";

// Filtres combinables : une langue est retenue si elle satisfait TOUS les critères actifs.
// Un critère vide ("") est inactif. Une valeur inconnue ne satisfait jamais un critère actif.
export interface Filters {
  text: string;
  universe: string;
  category: string;
  morphology: string;   // typology.morphological_type
  syntax: string;       // syntax.basic_word_order
  phonology: string;    // phonology.tone
  writing: string;      // "with" | "without"
  family: string;       // famille fictive documentée (aucune pour l'instant)
  period: string;       // décennie de création, ex. "1980"
  minProximity: number; // meilleur score régional robuste minimal (0 = inactif)
}

export const EMPTY_FILTERS: Filters = {
  text: "", universe: "", category: "", morphology: "", syntax: "", phonology: "",
  writing: "", family: "", period: "", minProximity: 0,
};

export function decade(year: number | null): string | null {
  return year === null ? null : String(Math.floor(year / 10) * 10);
}

export function bestRobustScore(langId: string, regions: RegionScore[]): number | null {
  const s = regions.filter((r) => r.imaginary_id === langId && r.robust).map((r) => r.score_genus_weighted);
  return s.length ? Math.max(...s) : null;
}

function norm(s: string): string {
  return s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}

export function matches(lang: Language, f: Filters, regions: RegionScore[]): boolean {
  if (f.text) {
    const hay = norm([lang.name, lang.universe, lang.creator ?? "", lang.description].join(" "));
    if (!hay.includes(norm(f.text))) return false;
  }
  if (f.universe && lang.universe !== f.universe) return false;
  if (f.category && lang.category !== f.category) return false;
  if (f.morphology && featureValue(lang, "typology.morphological_type") !== f.morphology) return false;
  if (f.syntax && featureValue(lang, "syntax.basic_word_order") !== f.syntax) return false;
  if (f.phonology && featureValue(lang, "phonology.tone") !== f.phonology) return false;
  if (f.writing === "with" && featureValue(lang, "writing.scripts") === null) return false;
  if (f.writing === "without" && featureValue(lang, "writing.scripts") !== null) return false;
  if (f.family) return false; // aucune famille fictive n'est encore documentée
  if (f.period && decade(lang.year) !== f.period) return false;
  if (f.minProximity > 0) {
    const best = bestRobustScore(lang.id, regions);
    if (best === null || best < f.minProximity) return false;
  }
  return true;
}

export function filterLanguages(langs: Language[], f: Filters, regions: RegionScore[]): Language[] {
  return langs.filter((l) => matches(l, f, regions));
}

export function options(langs: Language[], get: (l: Language) => string | null): string[] {
  return [...new Set(langs.map(get).filter((x): x is string => x !== null))].sort((a, b) => a.localeCompare(b, "fr"));
}

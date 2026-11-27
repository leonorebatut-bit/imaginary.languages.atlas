import type { AtlasData, Feature, Language } from "../types";

const f = (feature_id: string, value: unknown, status: Feature["status"] = "documented"): Feature => ({
  feature_id, domain: feature_id.split(".")[0], value: status === "unavailable" ? null : value, status,
  method: "documented:grammar", unit: null, source_ids: status === "documented" ? ["a-s01@§ 1"] : [], examples: [], limits: null,
});

const base = (id: string, name: string, over: Partial<Language>): Language => ({
  id, name, category: "constructed_fictional", universe: "Univers A", creator: "X", year: 1984, description: "desc",
  documentation_level: "high", corpus_type: "c", real_language_reference: null, scripts: [], metadata_status: "unverified",
  corpus: { status: "none" }, source_ids: ["a-s01"],
  sources: [{ source_id: "a-s01", url: "https://example.org/a", title: "Grammaire A", type: "grammar", license: "CC BY-SA 4.0",
              retrieved_at: "2026-11-27T00:00:00", status: "ok", available_items: null, kept_items: null }],
  features: [], wals_profile: {}, n_wals_features: 0, scored: false, ...over,
});

export const LANG_A = base("a", "Alpha", {
  features: [f("syntax.basic_word_order", "SOV"), f("phonology.tone", "No tones"), f("writing.scripts", ["sa"]),
             f("typology.morphological_type", "agglutinative"), f("lexicon.ttr", null, "unavailable")],
  scripts: ["sa"], wals_profile: { "81A": "SOV", "13A": "No tones" }, n_wals_features: 8, scored: true,
});
export const LANG_B = base("b", "Bêta", {
  universe: "Univers B", category: "pseudo_language", year: 2012, creator: null,
  features: [f("syntax.basic_word_order", "SVO"), f("writing.scripts", null, "unavailable")],
});

export const FIXTURE: AtlasData = {
  languages: [LANG_A, LANG_B],
  scripts: [{ id: "sa", name: "Écriture A", universe: null, creator: null, type: null, direction: null, represents: ["a"],
              metadata_status: "unverified", sources: [{ url: "https://example.org/s", title: "Source écriture", license: "CC0" }] }],
  wals: [
    { id: "w1", name: "Wala", lat: 10, lon: 10, area: "Zone 1", area_method: "autotyp", family: "F1", genus: "G1", macroarea: "Africa",
      profile: { "81A": "SOV", "13A": "Complex tones" } },
    { id: "w2", name: "Wolo", lat: 20, lon: 20, area: "Zone 2", area_method: "autotyp", family: "F2", genus: "G2", macroarea: "Eurasia",
      profile: { "81A": "SVO" } },
  ],
  regions: [
    { imaginary_id: "a", area: "Zone 1", score_genus_weighted: 0.72, score_mean: 0.7, score_median: 0.7, score_sd: 0.1, score_iqr: 0.1,
      ci95_low: 0.6, ci95_high: 0.8, n_languages: 12, n_genera: 4, mean_features_compared: 8, robust: true,
      feature_agreement: { "81A": { compared: 12, matching: 9 } } },
    { imaginary_id: "a", area: "Zone 2", score_genus_weighted: 0.91, score_mean: 0.9, score_median: 0.9, score_sd: null, score_iqr: 0,
      ci95_low: null, ci95_high: null, n_languages: 2, n_genera: 1, mean_features_compared: 8, robust: false },
  ],
  nearest: { a: [{ wals_id: "w1", score: 0.5, n_compared: 8, n_same: 4, n_different: 4, matching: ["81A"], diverging: ["13A"] }] },
  mapping: [
    { wals_id: "81A", wals_name: "Order of Subject, Object and Verb", domain: "syntax", project_feature: "syntax.basic_word_order",
      possible_values: ["SOV", "SVO"], transform: "identity", scale: "nominal", justification: "j" },
    { wals_id: "13A", wals_name: "Tone", domain: "phonology", project_feature: "phonology.tone",
      possible_values: ["No tones", "Complex tones"], transform: "identity", scale: "ordinal", justification: "j" },
  ],
  areas: [{ area: "Zone 1", n_languages: 12, lat: 10, lon: 10 }, { area: "Zone 2", n_languages: 2, lat: 20, lon: 20 }],
  manifest: { pipeline_version: "0.1.0", min_comparable_features: 8, reference_data: { wals: { version: "v2020.4", license: "CC-BY-4.0" } },
              n_languages: 2, n_scripts: 1 },
  land: null,
};

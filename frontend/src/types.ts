export type Status = "documented" | "observed" | "computed" | "unavailable";

export interface Feature {
  feature_id: string;
  domain: string;
  value: unknown;
  status: Status;
  method: string;
  unit: string | null;
  source_ids: string[];
  examples: string[];
  limits: string | null;
}

export interface Language {
  id: string;
  name: string;
  category: string;
  universe: string;
  creator: string | null;
  year: number | null;
  year_note?: string | null;
  description: string;
  documentation_level: string;
  corpus_type: string;
  real_language_reference: { name: string; glottocode?: string | null; wals_code?: string | null } | null;
  real_language_inspiration_note?: string | null;
  scripts: string[];
  metadata_status: string;
  corpus: { status: string; file?: string; lines?: number; redistributable?: boolean; justification?: string };
  source_ids: string[];
  sources: Source[];
  features: Feature[];
  wals_profile: Record<string, string>;
  n_wals_features: number;
  scored: boolean;
}

export interface Script {
  id: string;
  name: string;
  universe: string | null;
  creator: string | null;
  type: string | null;
  type_note?: string | null;
  direction: string | null;
  represents: string[];
  metadata_status: string;
  sources: { url: string; title: string; license: string }[];
}

export interface WalsLanguage {
  id: string;
  name: string;
  lat: number;
  lon: number;
  area: string | null;
  area_method: string | null;
  family: string | null;
  genus: string | null;
  macroarea: string | null;
  profile: Record<string, string>;
}

export interface RegionScore {
  imaginary_id: string;
  area: string;
  score_genus_weighted: number;
  score_mean: number;
  score_median: number;
  score_sd: number | null;
  score_iqr: number;
  ci95_low: number | null;
  ci95_high: number | null;
  n_languages: number;
  n_genera: number;
  mean_features_compared: number;
  robust: boolean;
  feature_agreement?: Record<string, { compared: number; matching: number }>;
}

export interface NearestPair {
  wals_id: string;
  score: number;
  n_compared: number;
  n_same: number;
  n_different: number;
  matching: string[];
  diverging: string[];
}

export interface Mapping {
  wals_id: string;
  wals_name: string;
  domain: string;
  project_feature: string;
  possible_values: string[];
  transform: string;
  scale: "nominal" | "ordinal";
  justification: string;
}

export interface Area {
  area: string;
  n_languages: number;
  lat: number;
  lon: number;
}

export interface Manifest {
  pipeline_version: string;
  min_comparable_features: number;
  reference_data: Record<string, { version: string; license: string }>;
  n_languages: number;
  n_scripts: number;
}

export interface AtlasData {
  languages: Language[];
  scripts: Script[];
  wals: WalsLanguage[];
  regions: RegionScore[];
  nearest: Record<string, NearestPair[]>;
  mapping: Mapping[];
  areas: Area[];
  manifest: Manifest;
  land: GeoJSON.FeatureCollection | null;
}

export interface Source {
  source_id: string;
  url: string;
  title: string;
  type: string;
  license: string | null;
  retrieved_at: string | null;
  status: string;
  available_items: string | null;
  kept_items: string | null;
}

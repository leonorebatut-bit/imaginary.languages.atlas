import type { Feature, Language } from "./types";

export const CATEGORY_LABELS: Record<string, string> = {
  constructed_fictional: "Langue construite (fiction)",
  constructed_external: "Langue construite (hors fiction)",
  fragmentary: "Langue fragmentaire",
  idiolect: "Idiolecte",
  sociolect: "Sociolecte",
  transformed_variety: "Variété transformée",
  pseudo_language: "Pseudo-langue",
};

export const STATUS_LABELS: Record<string, string> = {
  documented: "Documenté",
  observed: "Observé",
  computed: "Calculé",
  unavailable: "Non disponible",
};

export const STATUS_HELP: Record<string, string> = {
  documented: "Repris d'une description publiée, avec citation vérifiée.",
  observed: "Constaté directement dans le corpus.",
  computed: "Calculé par une fonction du pipeline.",
  unavailable: "Aucune donnée fiable : la valeur n'est pas devinée.",
};

export const DOC_LEVEL_LABELS: Record<string, string> = {
  high: "élevé", medium: "moyen", low: "faible", fragmentary: "fragmentaire",
};

export const DOMAIN_LABELS: Record<string, string> = {
  phonology: "Phonologie", morphology: "Morphologie", syntax: "Syntaxe",
  lexicon: "Lexique", typology: "Typologie", writing: "Écriture",
};

export const FEATURE_LABELS: Record<string, { label: string; definition: string }> = {
  "phonology.consonant_inventory_size": { label: "Nombre de consonnes", definition: "Nombre de consonnes phonémiques décrites par une source." },
  "phonology.consonant_inventory": { label: "Inventaire consonantique", definition: "Consonnes phonémiques (API) relevées dans une source." },
  "phonology.vowel_quality_inventory_size": { label: "Nombre de qualités vocaliques", definition: "Voyelles distinctes par leur timbre, sans compter longueur ni nasalité." },
  "phonology.vowel_quality_inventory": { label: "Inventaire vocalique", definition: "Qualités vocaliques (API) relevées dans une source." },
  "phonology.consonant_types": { label: "Types de consonnes", definition: "Répartition des consonnes documentées par mode d'articulation." },
  "phonology.syllable_structure": { label: "Structure syllabique", definition: "Complexité syllabique selon les classes de WALS 12A." },
  "phonology.syllable_template": { label: "Gabarit syllabique maximal", definition: "Syllabe la plus complexe autorisée (C = consonne, V = voyelle)." },
  "phonology.tone": { label: "Tons", definition: "Présence et complexité d'un système tonal (WALS 13A)." },
  "phonology.observed_graphemes": { label: "Graphèmes observés", definition: "Lettres du corpus. Ce n'est pas un inventaire phonologique." },
  "morphology.morphemes_per_word": { label: "Morphèmes par mot", definition: "Indice de synthèse calculé sur des exemples glosés." },
  "morphology.prefix_share": { label: "Part des préfixes", definition: "Proportion des affixes placés avant la racine (exemples glosés)." },
  "morphology.suffix_share": { label: "Part des suffixes", definition: "Proportion des affixes placés après la racine (exemples glosés)." },
  "morphology.infix_count": { label: "Infixes", definition: "Nombre d'infixes dans les exemples glosés." },
  "morphology.categories_marked": { label: "Catégories marquées", definition: "Genre, nombre, cas et temps relevés dans les gloses." },
  "morphology.number_of_genders": { label: "Nombre de genres", definition: "Genres ou classes nominales (WALS 30A)." },
  "morphology.number_of_cases": { label: "Nombre de cas", definition: "Cas morphologiques (WALS 49A)." },
  "morphology.nominal_plurality_coding": { label: "Marquage du pluriel", definition: "Procédé de marquage du pluriel nominal (WALS 33A)." },
  "syntax.basic_word_order": { label: "Ordre des constituants", definition: "Ordre dominant du sujet, de l'objet et du verbe (WALS 81A)." },
  "syntax.subject_verb_order": { label: "Ordre sujet-verbe", definition: "WALS 82A." },
  "syntax.object_verb_order": { label: "Ordre objet-verbe", definition: "WALS 83A." },
  "syntax.adposition_order": { label: "Adpositions", definition: "Prépositions ou postpositions (WALS 85A)." },
  "syntax.genitive_noun_order": { label: "Ordre génitif-nom", definition: "WALS 86A." },
  "syntax.adjective_noun_order": { label: "Ordre adjectif-nom", definition: "WALS 87A." },
  "syntax.demonstrative_noun_order": { label: "Ordre démonstratif-nom", definition: "WALS 88A." },
  "syntax.numeral_noun_order": { label: "Ordre numéral-nom", definition: "WALS 89A." },
  "syntax.relative_clause_noun_order": { label: "Ordre relative-nom", definition: "WALS 90A." },
  "syntax.polar_question_strategy": { label: "Questions totales", definition: "Stratégie de formation des questions oui/non (WALS 116A)." },
  "syntax.negative_morpheme_type": { label: "Morphème de négation", definition: "WALS 112A." },
  "syntax.subordination": { label: "Subordination", definition: "Procédés de subordination décrits par une source." },
  "syntax.estimated_constituent_order": { label: "Ordre estimé (spaCy)", definition: "Estimation automatique, réservée aux variétés de l'anglais." },
  "typology.morphological_type": { label: "Type morphologique", definition: "Étiquette (agglutinant, fusionnel, isolant…) donnée par une source." },
  "typology.analytic_synthetic": { label: "Analytique / synthétique", definition: "Étiquette donnée par une source." },
  "typology.dominant_word_order": { label: "Ordre dominant", definition: "Reprise de l'ordre des constituants documenté." },
  "typology.synthesis_index_band": { label: "Bande de Greenberg", definition: "Indicateur descriptif tiré de l'indice de synthèse, pas une classification." },
  "lexicon.token_count": { label: "Mots (tokens)", definition: "Nombre de mots du corpus." },
  "lexicon.type_count": { label: "Formes distinctes", definition: "Nombre de formes différentes du corpus." },
  "lexicon.ttr": { label: "TTR", definition: "Formes / mots. Dépend de la taille du corpus : ne pas comparer." },
  "lexicon.mattr": { label: "MATTR", definition: "TTR moyen sur une fenêtre glissante de 50 mots." },
  "lexicon.mtld": { label: "MTLD", definition: "Longueur moyenne des segments de diversité lexicale constante." },
  "lexicon.hdd": { label: "HD-D", definition: "Diversité attendue dans un échantillon de 42 mots." },
  "lexicon.hapax_ratio": { label: "Part d'hapax", definition: "Formes qui n'apparaissent qu'une fois." },
  "lexicon.mean_word_length": { label: "Longueur moyenne des mots", definition: "En graphèmes. Ne permet pas de conclure au type morphologique." },
  "writing.scripts": { label: "Écritures", definition: "Systèmes d'écriture dont le lien avec la langue est documenté." },
};

export function featureLabel(id: string): string {
  return FEATURE_LABELS[id]?.label ?? id;
}

export function feature(lang: Language, id: string): Feature | undefined {
  return lang.features.find((f) => f.feature_id === id);
}

export function featureValue(lang: Language, id: string): string | null {
  const f = feature(lang, id);
  if (!f || f.status === "unavailable" || f.value === null) return null;
  return formatValue(f.value);
}

export function formatValue(v: unknown): string {
  if (v === null || v === undefined) return "null";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toLocaleString("fr-FR", { maximumFractionDigits: 3 });
  if (Array.isArray(v)) return v.join(" ");
  if (typeof v === "object") {
    return Object.entries(v as Record<string, unknown>)
      .map(([k, x]) => `${k} : ${Array.isArray(x) ? (x.length ? x.join(", ") : "—") : String(x)}`)
      .join(" ; ");
  }
  return String(v);
}

export function fmtScore(x: number | null | undefined, digits = 2): string {
  return x === null || x === undefined ? "—" : x.toLocaleString("fr-FR", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

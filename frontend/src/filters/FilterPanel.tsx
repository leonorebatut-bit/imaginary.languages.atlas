import { CATEGORY_LABELS } from "../labels";
import { featureValue } from "../labels";
import type { Language } from "../types";
import { decade, EMPTY_FILTERS, options, type Filters } from "./filters";

interface Props {
  languages: Language[];
  value: Filters;
  onChange: (f: Filters) => void;
  resultCount: number;
}

function Select({ label, value, onChange, opts, render }: {
  label: string; value: string; onChange: (v: string) => void; opts: string[]; render?: (v: string) => string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Toutes</option>
        {opts.map((o) => <option key={o} value={o}>{render ? render(o) : o}</option>)}
      </select>
    </label>
  );
}

export default function FilterPanel({ languages, value, onChange, resultCount }: Props) {
  const set = (k: keyof Filters) => (v: string | number) => onChange({ ...value, [k]: v });
  return (
    <fieldset className="filters">
      <legend>Filtres <span className="muted">({resultCount} langue{resultCount > 1 ? "s" : ""})</span></legend>
      <label className="field">
        <span>Recherche</span>
        <input type="search" value={value.text} placeholder="Nom, univers, créateur…" onChange={(e) => set("text")(e.target.value)} />
      </label>
      <Select label="Univers d'origine" value={value.universe} onChange={set("universe")} opts={options(languages, (l) => l.universe)} />
      <Select label="Type de langue" value={value.category} onChange={set("category")}
              opts={options(languages, (l) => l.category)} render={(c) => CATEGORY_LABELS[c] ?? c} />
      <Select label="Morphologie (type documenté)" value={value.morphology} onChange={set("morphology")}
              opts={options(languages, (l) => featureValue(l, "typology.morphological_type"))} />
      <Select label="Syntaxe (ordre des constituants)" value={value.syntax} onChange={set("syntax")}
              opts={options(languages, (l) => featureValue(l, "syntax.basic_word_order"))} />
      <Select label="Phonologie (tons)" value={value.phonology} onChange={set("phonology")}
              opts={options(languages, (l) => featureValue(l, "phonology.tone"))} />
      <label className="field">
        <span>Écriture propre</span>
        <select value={value.writing} onChange={(e) => set("writing")(e.target.value)}>
          <option value="">Indifférent</option>
          <option value="with">Avec écriture documentée</option>
          <option value="without">Sans écriture documentée</option>
        </select>
      </label>
      <label className="field">
        <span>Famille linguistique fictive</span>
        <select value={value.family} disabled title="Aucune famille fictive n'est encore documentée dans le corpus">
          <option value="">Non documentée pour l'instant</option>
        </select>
      </label>
      <Select label="Période de création" value={value.period} onChange={set("period")}
              opts={options(languages, (l) => decade(l.year))} render={(d) => `années ${d}`} />
      <label className="field">
        <span>Proximité minimale avec une aire réelle : {value.minProximity ? value.minProximity.toFixed(2) : "inactif"}</span>
        <input type="range" min={0} max={1} step={0.05} value={value.minProximity}
               onChange={(e) => set("minProximity")(Number(e.target.value))} aria-label="Proximité minimale" />
      </label>
      <button type="button" className="link-button" onClick={() => onChange(EMPTY_FILTERS)}>Réinitialiser les filtres</button>
    </fieldset>
  );
}

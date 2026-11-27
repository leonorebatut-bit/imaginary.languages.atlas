import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAtlas } from "../data";
import FilterPanel from "../filters/FilterPanel";
import { bestRobustScore, EMPTY_FILTERS, filterLanguages, type Filters } from "../filters/filters";
import { CATEGORY_LABELS, DOC_LEVEL_LABELS, featureValue, fmtScore } from "../labels";
import type { Language } from "../types";

type Key = "name" | "universe" | "category" | "year" | "documented" | "n_wals" | "best";

export default function LanguagesPage() {
  const { languages, regions } = useAtlas();
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [sort, setSort] = useState<{ key: Key; asc: boolean }>({ key: "name", asc: true });

  const rows = useMemo(() => {
    const get = (l: Language): string | number | null => {
      switch (sort.key) {
        case "name": return l.name;
        case "universe": return l.universe;
        case "category": return CATEGORY_LABELS[l.category] ?? l.category;
        case "year": return l.year;
        case "documented": return l.features.filter((f) => f.status === "documented").length;
        case "n_wals": return l.n_wals_features;
        case "best": return bestRobustScore(l.id, regions);
      }
    };
    return [...filterLanguages(languages, filters, regions)].sort((a, b) => {
      const x = get(a), y = get(b);
      if (x === null && y === null) return 0;
      if (x === null) return 1;   // les valeurs inconnues restent en bas, quel que soit le sens
      if (y === null) return -1;
      const c = typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y), "fr");
      return sort.asc ? c : -c;
    });
  }, [languages, regions, filters, sort]);

  const th = (key: Key, label: string) => (
    <th aria-sort={sort.key === key ? (sort.asc ? "ascending" : "descending") : "none"}>
      <button type="button" className="sort" onClick={() => setSort({ key, asc: sort.key === key ? !sort.asc : true })}>
        {label}{sort.key === key ? (sort.asc ? " ▲" : " ▼") : ""}
      </button>
    </th>
  );

  return (
    <main className="page">
      <h1>Langues</h1>
      <div className="list-layout">
        <FilterPanel languages={languages} value={filters} onChange={setFilters} resultCount={rows.length} />
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                {th("name", "Langue")}{th("universe", "Univers")}{th("category", "Type")}{th("year", "Année")}
                <th>Documentation</th><th>Ordre</th>
                {th("documented", "Doc.")}{th("n_wals", "WALS")}{th("best", "Meilleure aire")}
              </tr>
            </thead>
            <tbody>
              {rows.map((l) => (
                <tr key={l.id}>
                  <td><Link to={`/langues/${l.id}`}>{l.name}</Link></td>
                  <td>{l.universe}</td>
                  <td>{CATEGORY_LABELS[l.category] ?? l.category}</td>
                  <td className="num">{l.year ?? "—"}</td>
                  <td>{DOC_LEVEL_LABELS[l.documentation_level] ?? l.documentation_level}</td>
                  <td>{featureValue(l, "syntax.basic_word_order") ?? <span className="muted">—</span>}</td>
                  <td className="num">{l.features.filter((f) => f.status === "documented").length}</td>
                  <td className="num">{l.n_wals_features}</td>
                  <td className="num">{l.scored ? fmtScore(bestRobustScore(l.id, regions)) : <span className="muted" title="Moins de caractéristiques comparables que le seuil : pas de score">—</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted small">
            Doc. : valeurs documentées par une source citée. WALS : caractéristiques comparables avec WALS.
            Meilleure aire : score de l'aire robuste la plus proche ; « — » signifie pas de score (seuil non atteint).
          </p>
          {rows.length === 0 && <p className="muted">Aucune langue ne satisfait tous les filtres.</p>}
        </div>
      </div>
    </main>
  );
}

import { useCallback, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAtlas } from "../data";
import AtlasMap from "../map/AtlasMap";
import Legend from "../map/Legend";
import FilterPanel from "../filters/FilterPanel";
import { EMPTY_FILTERS, filterLanguages, type Filters } from "../filters/filters";
import { fmtScore } from "../labels";
import { scoreColor } from "../map/colors";

export default function MapPage() {
  const { languages, wals, areas, regions, land, mapping, manifest } = useAtlas();
  const [params, setParams] = useSearchParams();
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [robustOnly, setRobustOnly] = useState(false);
  const [selectedArea, setSelectedArea] = useState<string | null>(null);

  const filtered = useMemo(() => filterLanguages(languages, filters, regions), [languages, filters, regions]);
  const selectable = filtered.filter((l) => l.scored);
  const langId = params.get("langue") ?? selectable[0]?.id ?? null;
  const lang = languages.find((l) => l.id === langId) ?? null;
  const langRegions = useMemo(() => regions.filter((r) => r.imaginary_id === langId), [regions, langId]);
  const ranked = [...langRegions].filter((r) => !robustOnly || r.robust)
    .sort((a, b) => b.score_genus_weighted - a.score_genus_weighted);
  const area = langRegions.find((r) => r.area === selectedArea) ?? null;
  const walsName = Object.fromEntries(mapping.map((m) => [m.wals_id, m.wals_name]));
  const onSelectArea = useCallback((a: string) => setSelectedArea(a), []);

  return (
    <main className="page map-page">
      <h1>Carte des proximités typologiques</h1>
      <p className="callout">
        <strong>Important :</strong> cette carte représente une proximité typologique, pas une origine géographique,
        une parenté généalogique ou une influence historique.
      </p>
      <div className="map-layout">
        <aside className="map-side">
          <label className="field">
            <span>Langue imaginaire</span>
            <select value={langId ?? ""} onChange={(e) => { setParams({ langue: e.target.value }); setSelectedArea(null); }}>
              {selectable.length === 0 && <option value="">Aucune langue avec score ne correspond</option>}
              {selectable.map((l) => <option key={l.id} value={l.id}>{l.name} ({l.n_wals_features} caract.)</option>)}
            </select>
          </label>
          <p className="muted small">
            Seules les langues ayant au moins {manifest.min_comparable_features} caractéristiques comparables avec
            WALS ont un score ({languages.filter((l) => l.scored).length} sur {languages.length}).
          </p>
          <label className="check">
            <input type="checkbox" checked={robustOnly} onChange={(e) => setRobustOnly(e.target.checked)} />
            N'afficher que les aires robustes
          </label>
          <FilterPanel languages={languages} value={filters} onChange={setFilters} resultCount={filtered.length} />
        </aside>
        <div className="map-main">
          <AtlasMap land={land} wals={wals} areas={areas} regions={lang?.scored ? langRegions : []}
                    robustOnly={robustOnly} selectedArea={selectedArea} onSelectArea={onSelectArea} />
          <Legend />
        </div>
        <aside className="map-detail" aria-live="polite">
          {lang ? (
            <>
              <h2><Link to={`/langues/${lang.id}`}>{lang.name}</Link></h2>
              {area ? (
                <div className="area-detail">
                  <h3>{area.area}</h3>
                  <p className="big-score">{fmtScore(area.score_genus_weighted)}</p>
                  <p className="muted small">score moyen pondéré par genre</p>
                  <dl className="kv">
                    <dt>IC 95 % (bootstrap sur les genres)</dt><dd>{fmtScore(area.ci95_low)} – {fmtScore(area.ci95_high)}</dd>
                    <dt>Médiane / écart-type</dt><dd>{fmtScore(area.score_median)} / {fmtScore(area.score_sd)}</dd>
                    <dt>Langues WALS comparées</dt><dd>{area.n_languages}</dd>
                    <dt>Genres</dt><dd>{area.n_genera}</dd>
                    <dt>Caractéristiques comparées (moyenne)</dt><dd>{fmtScore(area.mean_features_compared, 1)}</dd>
                    <dt>Robustesse</dt><dd>{area.robust ? "robuste" : "peu robuste (moins de 10 langues ou de 3 genres)"}</dd>
                  </dl>
                  {area.feature_agreement && (
                    <table className="table compact">
                      <caption>Part des langues de l'aire qui partagent la valeur</caption>
                      <thead><tr><th>WALS</th><th>Concordance</th><th>n</th></tr></thead>
                      <tbody>
                        {Object.entries(area.feature_agreement).map(([id, a]) => (
                          <tr key={id}>
                            <td title={walsName[id]}>{id} {walsName[id]}</td>
                            <td>{a.compared ? `${Math.round((100 * a.matching) / a.compared)} %` : "—"}</td>
                            <td>{a.compared}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                  <button type="button" className="link-button" onClick={() => setSelectedArea(null)}>Revenir au classement</button>
                </div>
              ) : (
                <>
                  <h3>Aires les plus proches</h3>
                  <p className="muted small">Cliquez sur une aire de la carte ou de la liste pour le détail.</p>
                  <ol className="ranking">
                    {ranked.slice(0, 12).map((r) => (
                      <li key={r.area}>
                        <button type="button" className="link-button" onClick={() => setSelectedArea(r.area)}>
                          <span className="swatch" style={{ background: scoreColor(r.score_genus_weighted) }} />
                          {r.area}
                        </button>
                        <span className="num">{fmtScore(r.score_genus_weighted)}</span>
                        {!r.robust && <span className="muted small"> peu robuste</span>}
                      </li>
                    ))}
                  </ol>
                  <p><Link to={`/comparaison?langue=${lang.id}`}>Comparer caractéristique par caractéristique</Link></p>
                </>
              )}
            </>
          ) : <p className="muted">Aucune langue sélectionnée.</p>}
        </aside>
      </div>
    </main>
  );
}

import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAtlas } from "../data";
import { fmtScore } from "../labels";

// Comparaison caractéristique par caractéristique entre une langue imaginaire et une langue WALS.
// Le site ne recalcule aucun score : le score de Gower affiché est celui produit par le pipeline
// (50 langues les plus proches) ; pour les autres langues, seul le détail des valeurs est montré.
export default function ComparePage() {
  const { languages, wals, nearest, mapping } = useAtlas();
  const [params, setParams] = useSearchParams();
  const candidates = languages.filter((l) => l.n_wals_features > 0);
  const langId = params.get("langue") ?? candidates.find((l) => l.scored)?.id ?? candidates[0]?.id;
  const lang = languages.find((l) => l.id === langId);
  const near = (langId && nearest[langId]) || [];
  const walsById = useMemo(() => new Map(wals.map((w) => [w.id, w])), [wals]);
  const [query, setQuery] = useState("");
  const walsId = params.get("wals") ?? near[0]?.wals_id ?? null;
  const target = walsId ? walsById.get(walsId) : undefined;
  const pair = near.find((p) => p.wals_id === walsId);

  const hits = query.length >= 2
    ? wals.filter((w) => w.name.toLowerCase().includes(query.toLowerCase())).slice(0, 15) : [];
  const set = (next: Record<string, string>) => setParams({ ...(langId ? { langue: langId } : {}), ...(walsId ? { wals: walsId } : {}), ...next });

  const rows = lang && target ? mapping.map((m) => {
    const a = lang.wals_profile[m.wals_id] ?? null;
    const b = target.profile[m.wals_id] ?? null;
    return { m, a, b, state: a === null || b === null ? "na" : a === b ? "same" : "diff" };
  }) : [];
  const compared = rows.filter((r) => r.state !== "na");

  return (
    <main className="page">
      <h1>Comparaison avec une langue de WALS</h1>
      <p className="callout">Proximité typologique seulement : ni origine, ni parenté, ni influence historique.</p>
      <div className="compare-controls">
        <label className="field">
          <span>Langue imaginaire</span>
          <select value={langId ?? ""} onChange={(e) => setParams({ langue: e.target.value })}>
            {candidates.map((l) => <option key={l.id} value={l.id}>{l.name} ({l.n_wals_features} caract.{l.scored ? "" : ", sans score"})</option>)}
          </select>
        </label>
        <label className="field">
          <span>Chercher une langue WALS</span>
          <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="ex. Japanese, Basque…" />
        </label>
      </div>
      {hits.length > 0 && (
        <ul className="hits">
          {hits.map((w) => <li key={w.id}><button type="button" className="link-button" onClick={() => { set({ wals: w.id }); setQuery(""); }}>{w.name}</button> <span className="muted small">{w.family} · {w.area ?? "aire inconnue"}</span></li>)}
        </ul>
      )}

      {lang && (
        <div className="compare-layout">
          <section>
            <h2>Langues WALS les plus proches de {lang.name}</h2>
            {near.length === 0 ? (
              <p className="notice">Pas de classement : moins de caractéristiques comparables que le seuil.</p>
            ) : (
              <ol className="ranking">
                {near.slice(0, 20).map((p) => {
                  const w = walsById.get(p.wals_id);
                  return (
                    <li key={p.wals_id} className={p.wals_id === walsId ? "active" : ""}>
                      <button type="button" className="link-button" onClick={() => set({ wals: p.wals_id })}>{w?.name ?? p.wals_id}</button>
                      <span className="num">{fmtScore(p.score)}</span>
                      <span className="muted small"> {p.n_compared} caract. · {w?.area ?? "—"}</span>
                    </li>
                  );
                })}
              </ol>
            )}
          </section>
          <section>
            {target ? (
              <>
                <h2>{lang.name} et {target.name}</h2>
                <p className="muted small">
                  {target.family ?? "famille inconnue"} · genre {target.genus ?? "inconnu"} · aire {target.area ?? "inconnue"}
                  {target.area_method === "nearest_neighbour" ? " (rattachée par voisin le plus proche)" : ""}
                </p>
                <p>
                  {compared.length} caractéristique(s) comparable(s), {compared.filter((r) => r.state === "same").length} identique(s).
                  {pair ? ` Score de Gower : ${fmtScore(pair.score)}.` : " Score non affiché : cette langue n'est pas parmi les 50 plus proches."}
                </p>
                <div className="table-wrap">
                  <table className="table compact">
                    <thead><tr><th>WALS</th><th>{lang.name}</th><th>{target.name}</th><th>Résultat</th></tr></thead>
                    <tbody>
                      {rows.map(({ m, a, b, state }) => (
                        <tr key={m.wals_id} className={`cmp-${state}`}>
                          <td title={m.justification}>{m.wals_id} {m.wals_name}</td>
                          <td>{a ?? <span className="muted">null</span>}</td>
                          <td>{b ?? <span className="muted">null</span>}</td>
                          <td>{state === "same" ? "identique" : state === "diff" ? "différent" : <span className="muted">non comparable</span>}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="muted small">
                  Une caractéristique est « non comparable » si l'une des deux valeurs est inconnue ; elle est alors exclue du
                  score. Les échelles ordinales (taille d'inventaire, nombre de cas…) donnent un score partiel aux valeurs voisines,
                  ce que ce tableau ne détaille pas.
                </p>
                <p><Link to={`/langues/${lang.id}`}>Fiche de {lang.name}</Link></p>
              </>
            ) : <p className="muted">Choisissez une langue WALS.</p>}
          </section>
        </div>
      )}
    </main>
  );
}

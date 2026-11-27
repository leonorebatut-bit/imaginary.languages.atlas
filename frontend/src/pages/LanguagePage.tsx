import { Link, useParams } from "react-router-dom";
import { useAtlas } from "../data";
import FeatureRow from "../components/FeatureRow";
import { CATEGORY_LABELS, DOC_LEVEL_LABELS, fmtScore, STATUS_LABELS } from "../labels";
import type { Feature } from "../types";

const SECTIONS = [
  ["presentation", "1. Présentation"], ["corpus", "2. Corpus et sources"], ["phonology", "3. Phonologie"],
  ["morphology", "4. Morphologie"], ["syntax", "5. Syntaxe"], ["typology", "6. Typologie"],
  ["lexicon", "7. Lexique"], ["writing", "8. Écriture"], ["wals", "9. Comparaison WALS"], ["references", "10. Références"],
] as const;

const DOMAIN_NOTES: Record<string, string> = {
  phonology: "Seuls les phonèmes décrits par une source sont comptés ; les lettres du corpus ne sont jamais converties en inventaire phonologique.",
  morphology: "Les indices sont calculés uniquement sur des exemples glosés (règles de Leipzig) ; le type morphologique n'est jamais déduit de la longueur des mots.",
  syntax: "Les ordres sont repris d'une source ; l'estimation automatique n'est utilisée que pour les variétés construites sur l'anglais.",
  typology: "Les étiquettes typologiques viennent d'une source. La bande de Greenberg n'est qu'un indicateur descriptif.",
  lexicon: "Mesures sur le corpus disponible. Le TTR dépend de la taille du corpus ; MATTR, MTLD et HD-D sont moins sensibles. Aucune mesure sous 100 mots.",
  writing: "Seules les écritures dont le lien avec la langue est documenté sont indiquées.",
};

export default function LanguagePage() {
  const { id } = useParams();
  const { languages, scripts, regions, mapping, manifest } = useAtlas();
  const lang = languages.find((l) => l.id === id);
  if (!lang) return <main className="page"><h1>Langue introuvable</h1><p><Link to="/langues">Retour à la liste</Link></p></main>;

  const titles: Record<string, string> = Object.fromEntries(lang.sources.map((s) => [s.source_id, s.title]));
  for (const s of scripts) titles[`script:${s.id}`] = `fiche de l'écriture ${s.name} (section 8)`;
  const byDomain = (d: string): Feature[] => lang.features.filter((f) => f.domain === d)
    .sort((a, b) => Number(a.status === "unavailable") - Number(b.status === "unavailable"));
  const langScripts = scripts.filter((s) => lang.scripts.includes(s.id));
  const top = regions.filter((r) => r.imaginary_id === lang.id)
    .sort((a, b) => b.score_genus_weighted - a.score_genus_weighted).slice(0, 5);
  const walsName = Object.fromEntries(mapping.map((m) => [m.wals_id, m.wals_name]));
  const counts = (["documented", "observed", "computed", "unavailable"] as const)
    .map((s) => [s, lang.features.filter((f) => f.status === s).length] as const);

  const domainSection = (d: string, key: string, title: string) => {
    const fs = byDomain(d);
    const avail = fs.filter((f) => f.status !== "unavailable");
    return (
      <section id={key} key={key}>
        <h2>{title}</h2>
        <p className="muted small">{DOMAIN_NOTES[d]}</p>
        {avail.length === 0 && <p className="notice">Aucune donnée fiable pour ce domaine : rien n'est affiché à la place.</p>}
        <div className="features">{avail.map((f) => <FeatureRow key={f.feature_id} f={f} sourceTitles={titles} />)}</div>
        {fs.length > avail.length && (
          <details>
            <summary>{fs.length - avail.length} caractéristique(s) non disponible(s)</summary>
            <div className="features">{fs.filter((f) => f.status === "unavailable").map((f) => <FeatureRow key={f.feature_id} f={f} sourceTitles={titles} />)}</div>
          </details>
        )}
      </section>
    );
  };

  return (
    <main className="page language-page">
      <p><Link to="/langues">← Toutes les langues</Link></p>
      <h1>{lang.name}</h1>
      <nav className="toc" aria-label="Sections de la fiche">
        {SECTIONS.map(([k, t]) => <a key={k} href={`#${k}`} onClick={(e) => { e.preventDefault(); document.getElementById(k)?.scrollIntoView(); }}>{t}</a>)}
      </nav>

      <section id="presentation">
        <h2>1. Présentation</h2>
        {lang.metadata_status !== "verified" && (
          <p className="notice">Métadonnées non encore relues : à vérifier avant toute citation.</p>
        )}
        <p>{lang.description}</p>
        <dl className="kv">
          <dt>Univers</dt><dd>{lang.universe}</dd>
          <dt>Créateur ou créatrice</dt><dd>{lang.creator ?? <span className="muted">non renseigné</span>}</dd>
          <dt>Année</dt><dd>{lang.year ?? <span className="muted">non renseignée</span>}{lang.year_note ? ` (${lang.year_note})` : ""}</dd>
          <dt>Type</dt><dd>{CATEGORY_LABELS[lang.category] ?? lang.category}</dd>
          <dt>Niveau de documentation</dt><dd>{DOC_LEVEL_LABELS[lang.documentation_level] ?? lang.documentation_level}</dd>
          {lang.real_language_reference && (<><dt>Langue réelle de référence</dt><dd>{lang.real_language_reference.name}</dd></>)}
          {lang.real_language_inspiration_note && (<><dt>Inspiration déclarée</dt><dd>{lang.real_language_inspiration_note}</dd></>)}
          <dt>Statut des caractéristiques</dt><dd>{counts.map(([s, n]) => `${n} ${STATUS_LABELS[s].toLowerCase()}`).join(" · ")}</dd>
        </dl>
      </section>

      <section id="corpus">
        <h2>2. Corpus et sources</h2>
        <dl className="kv">
          <dt>Type de corpus</dt><dd>{lang.corpus_type}</dd>
          <dt>État</dt><dd>{lang.corpus.status === "available"
            ? `${lang.corpus.lines ?? "?"} lignes${lang.corpus.redistributable ? ", redistribuable" : ", conservé en local (licence non libre)"}`
            : <span className="muted">aucun corpus redistribuable</span>}</dd>
          {lang.corpus.justification && (<><dt>Remarque</dt><dd>{lang.corpus.justification}</dd></>)}
        </dl>
        <div className="table-wrap">
          <table className="table compact">
            <thead><tr><th>Source</th><th>Type</th><th>Licence</th><th>Éléments gardés / disponibles</th><th>État</th></tr></thead>
            <tbody>
              {lang.sources.map((s) => (
                <tr key={s.source_id}>
                  <td><a href={s.url} target="_blank" rel="noreferrer">{s.title}</a></td>
                  <td>{s.type}</td>
                  <td>{s.license ?? <span className="muted">inconnue</span>}</td>
                  <td className="num">{s.kept_items && s.available_items ? `${s.kept_items} / ${s.available_items}` : "—"}</td>
                  <td>{s.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {domainSection("phonology", "phonology", "3. Phonologie")}
      {domainSection("morphology", "morphology", "4. Morphologie")}
      {domainSection("syntax", "syntax", "5. Syntaxe")}
      {domainSection("typology", "typology", "6. Typologie")}
      {domainSection("lexicon", "lexicon", "7. Lexique")}

      <section id="writing">
        <h2>8. Écriture</h2>
        <p className="muted small">{DOMAIN_NOTES.writing}</p>
        {langScripts.length === 0 ? <p className="notice">Aucune écriture propre documentée.</p> : (
          <ul>
            {langScripts.map((s) => (
              <li key={s.id}><strong>{s.name}</strong>
                {s.type ? ` : ${s.type}` : ""}{s.direction ? `, ${s.direction}` : ""}{s.creator ? ` (${s.creator})` : ""}
                {s.sources.length === 0 && <span className="muted"> · aucune source : lien non retenu comme documenté</span>}
                {s.sources.map((x) => <span key={x.url}> · <a href={x.url} target="_blank" rel="noreferrer">{x.title}</a></span>)}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section id="wals">
        <h2>9. Comparaison WALS</h2>
        <p>
          {lang.n_wals_features} caractéristique(s) comparable(s) avec WALS
          {Object.keys(lang.wals_profile).length ? ` : ${Object.entries(lang.wals_profile).map(([k, v]) => `${k} ${v}`).join(" ; ")}` : ""}.
        </p>
        {lang.scored ? (
          <>
            <div className="table-wrap"><table className="table compact">
              <thead><tr><th>Aire</th><th>Score</th><th>IC 95 %</th><th>Langues</th><th>Genres</th><th>Robustesse</th></tr></thead>
              <tbody>
                {top.map((r) => (
                  <tr key={r.area}><td>{r.area}</td><td className="num">{fmtScore(r.score_genus_weighted)}</td>
                    <td className="num">{fmtScore(r.ci95_low)} – {fmtScore(r.ci95_high)}</td>
                    <td className="num">{r.n_languages}</td><td className="num">{r.n_genera}</td>
                    <td>{r.robust ? "robuste" : "peu robuste"}</td></tr>
                ))}
              </tbody>
            </table></div>
            <p><Link to={`/carte?langue=${lang.id}`}>Voir sur la carte</Link> · <Link to={`/comparaison?langue=${lang.id}`}>Comparaison détaillée</Link></p>
          </>
        ) : (
          <p className="notice">
            Pas de score : il faut au moins {manifest.min_comparable_features} caractéristiques comparables. Aucune valeur
            n'est ajoutée pour atteindre ce seuil.
          </p>
        )}
        <p className="muted small">Proximité typologique seulement : ni origine, ni parenté, ni influence historique.</p>
        {Object.keys(lang.wals_profile).length > 0 && (
          <details><summary>Correspondances utilisées</summary>
            <ul>{Object.keys(lang.wals_profile).map((k) => <li key={k}>{k} {walsName[k]}</li>)}</ul>
          </details>
        )}
      </section>

      <section id="references">
        <h2>10. Références</h2>
        <ol className="refs">
          {lang.sources.map((s) => (
            <li key={s.source_id}>
              {s.title}. <a href={s.url} target="_blank" rel="noreferrer">{s.url}</a>
              {s.license ? `. Licence : ${s.license}` : ""}{s.retrieved_at ? `. Consulté le ${s.retrieved_at.slice(0, 10)}` : ""}.
            </li>
          ))}
          <li>Dryer, Matthew S. &amp; Haspelmath, Martin (eds.) 2013. <em>The World Atlas of Language Structures Online</em>. Leipzig : MPI-EVA. CC-BY 4.0.</li>
          <li>Bickel, Balthasar, Johanna Nichols, Taras Zakharko et al. <em>The AUTOTYP database</em>. CC-BY 4.0.</li>
        </ol>
      </section>
    </main>
  );
}

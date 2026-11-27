import { Link } from "react-router-dom";
import { useAtlas } from "../data";

export default function HomePage() {
  const { languages, scripts, wals, manifest, mapping } = useAtlas();
  const scored = languages.filter((l) => l.scored);
  const documented = languages.filter((l) => l.features.some((f) => f.status === "documented"));
  const withCorpus = languages.filter((l) => l.corpus.status === "available");
  return (
    <main className="page home">
      <section className="hero">
        <h1>Imaginary Languages Atlas</h1>
        <p className="lead">
          Un atlas de recherche en linguistique computationnelle : {languages.length} langues et variétés imaginaires,
          décrites à partir de sources vérifiables et comparées aux {wals.length.toLocaleString("fr-FR")} langues
          naturelles de WALS.
        </p>
        <p className="callout">
          <strong>Important :</strong> cette carte représente une proximité typologique, pas une origine géographique,
          une parenté généalogique ou une influence historique.
        </p>
        <p><Link className="button" to="/carte">Ouvrir la carte</Link> <Link className="button secondary" to="/langues">Parcourir les langues</Link></p>
      </section>

      <section className="stats" aria-label="Chiffres clés">
        <div><b>{languages.length}</b><span>langues au catalogue</span></div>
        <div><b>{scripts.length}</b><span>systèmes d'écriture</span></div>
        <div><b>{documented.length}</b><span>langues avec caractéristiques documentées</span></div>
        <div><b>{scored.length}</b><span>langues avec un score WALS</span></div>
      </section>

      <section>
        <h2>Le projet</h2>
        <p>
          Les langues imaginaires (langues de fiction, langues construites, idiolectes, variétés transformées) sont
          rarement étudiées avec les outils de la typologie. L'atlas les décrit avec les mêmes caractéristiques que
          les langues naturelles, puis mesure à quelles aires linguistiques réelles elles ressemblent le plus.
        </p>
        <h2>Objectifs</h2>
        <ul>
          <li>Constituer un catalogue documenté, avec pour chaque langue ses sources et leur licence.</li>
          <li>Décrire phonologie, morphologie, syntaxe, lexique, typologie et écriture sans jamais deviner une valeur.</li>
          <li>Comparer chaque langue aux langues de WALS et agréger les résultats par aire linguistique.</li>
          <li>Rendre toute l'analyse reproductible avec une seule commande.</li>
        </ul>
        <h2>Méthodes</h2>
        <ul>
          <li>Chaque valeur porte un statut : <em>documentée</em> (citation vérifiée automatiquement dans la source),
            <em> observée</em> (dans le corpus), <em>calculée</em> ou <em>non disponible</em>.</li>
          <li>{mapping.length} caractéristiques sont mises en correspondance avec WALS, chacune avec une justification.</li>
          <li>La similarité est un indice de Gower : les valeurs manquantes sont exclues, et aucun score n'est donné
            sous {manifest.min_comparable_features} caractéristiques comparables.</li>
          <li>Les scores par aire (aires AUTOTYP) sont pondérés par genre, avec un intervalle de confiance bootstrap.
            Une aire de moins de 10 langues ou de 3 genres est signalée comme peu robuste.</li>
        </ul>
        <h2>Corpus</h2>
        <p>
          {withCorpus.length} langues disposent d'un corpus redistribuable (phrases Tatoeba, échantillonnées à
          5 000 phrases au plus). Les textes protégés par le droit d'auteur ne sont pas redistribués : seules leurs
          références et des statistiques dérivées sont publiées. Les corpus sont petits et inégaux, ce qui limite
          la portée des mesures lexicales.
        </p>
        <h2>Bases de données utilisées</h2>
        <ul>
          <li>WALS Online {manifest.reference_data.wals?.version} (Dryer &amp; Haspelmath 2013), CC-BY 4.0.</li>
          <li>AUTOTYP, registre des langues et aires linguistiques (Bickel, Nichols et al.), CC-BY 4.0.</li>
          <li>Tatoeba (phrases, CC BY 2.0 FR) et Wikipédia (descriptions grammaticales, CC BY-SA 4.0).</li>
          <li>Natural Earth pour le fond de carte (domaine public).</li>
        </ul>
        <h2>Limites</h2>
        <p>
          Les métadonnées du catalogue restent à relire. Le codage des caractéristiques documentées a été fait par un
          assistant IA à partir de citations vérifiées, mais doit être relu. Beaucoup de langues n'ont pas assez de
          caractéristiques comparables pour recevoir un score : c'est affiché, pas comblé.
        </p>
      </section>
    </main>
  );
}

import { legendItems, NO_DATA } from "./colors";

export default function Legend() {
  return (
    <div className="legend" aria-label="Légende">
      <div className="legend-title">Proximité typologique de l'aire (0 à 1)</div>
      <ul>
        {legendItems().map((i) => (
          <li key={i.label}><span className="swatch" style={{ background: i.color }} />{i.label}</li>
        ))}
        <li><span className="swatch" style={{ background: NO_DATA }} />pas de score</li>
        <li><span className="swatch dashed" />aire peu robuste (moins de 10 langues ou de 3 genres)</li>
      </ul>
      <p className="legend-note">
        Proximité typologique seulement : ni origine, ni parenté, ni influence historique.
        Chaque point est une langue de WALS placée à ses coordonnées ; sa couleur est celle du score de son aire.
      </p>
    </div>
  );
}

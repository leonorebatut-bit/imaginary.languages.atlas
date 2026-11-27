import { NavLink, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";
import MapPage from "./pages/MapPage";
import LanguagesPage from "./pages/LanguagesPage";
import LanguagePage from "./pages/LanguagePage";
import ComparePage from "./pages/ComparePage";

export default function App() {
  return (
    <>
      <header className="site-header">
        <NavLink to="/" className="brand">Imaginary Languages Atlas</NavLink>
        <nav aria-label="Navigation principale">
          <NavLink to="/" end>Accueil</NavLink>
          <NavLink to="/carte">Carte</NavLink>
          <NavLink to="/langues">Langues</NavLink>
          <NavLink to="/comparaison">Comparaison</NavLink>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/carte" element={<MapPage />} />
        <Route path="/langues" element={<LanguagesPage />} />
        <Route path="/langues/:id" element={<LanguagePage />} />
        <Route path="/comparaison" element={<ComparePage />} />
        <Route path="*" element={<main className="page"><h1>Page introuvable</h1></main>} />
      </Routes>
      <footer className="site-footer">
        <p>
          Proximité typologique seulement : les scores n'indiquent ni une origine géographique, ni une parenté,
          ni une influence historique. Données : WALS 2020.4 et AUTOTYP (CC-BY 4.0), Tatoeba (CC BY 2.0 FR),
          Wikipédia (CC BY-SA 4.0), Natural Earth (domaine public). Code sous licence MIT.
        </p>
      </footer>
    </>
  );
}

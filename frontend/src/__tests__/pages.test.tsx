import { render, screen, fireEvent, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { DataProvider } from "../data";
import { FIXTURE } from "./fixture";
import LanguagePage from "../pages/LanguagePage";
import LanguagesPage from "../pages/LanguagesPage";
import ComparePage from "../pages/ComparePage";
import HomePage from "../pages/HomePage";

function renderAt(path: string, route: string, el: JSX.Element) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <DataProvider initial={FIXTURE}><Routes><Route path={route} element={el} /></Routes></DataProvider>
    </MemoryRouter>,
  );
}

describe("pages", () => {
  it("accueil : avertissement sur la proximité typologique", () => {
    renderAt("/", "/", <HomePage />);
    expect(screen.getByText(/pas une origine géographique, une parenté généalogique ou une influence historique/)).toBeInTheDocument();
  });

  it("fiche : 10 sections, valeur documentée avec sa source, null jamais remplacé", () => {
    renderAt("/langues/a", "/langues/:id", <LanguagePage />);
    for (const t of ["1. Présentation", "2. Corpus et sources", "3. Phonologie", "4. Morphologie", "5. Syntaxe",
                     "6. Typologie", "7. Lexique", "8. Écriture", "9. Comparaison WALS", "10. Références"]) {
      expect(screen.getByRole("heading", { level: 2, name: t })).toBeInTheDocument();
    }
    expect(screen.getAllByText("SOV").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Grammaire A \(§ 1\)/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Métadonnées non encore relues/)).toBeInTheDocument();
    expect(screen.getByText(/1 caractéristique\(s\) non disponible\(s\)/)).toBeInTheDocument();
  });

  it("fiche d'une langue sans score : le seuil est expliqué", () => {
    renderAt("/langues/b", "/langues/:id", <LanguagePage />);
    expect(screen.getByText(/Pas de score : il faut au moins 8 caractéristiques/)).toBeInTheDocument();
  });

  it("liste : tri par année et filtre de recherche", () => {
    renderAt("/langues", "/langues", <LanguagesPage />);
    const rows = () => screen.getAllByRole("row").slice(1).map((r) => within(r).getAllByRole("cell")[0].textContent);
    expect(rows()).toEqual(["Alpha", "Bêta"]);
    fireEvent.click(screen.getByRole("button", { name: /Année/ }));
    fireEvent.click(screen.getByRole("button", { name: /Année/ }));
    expect(rows()).toEqual(["Bêta", "Alpha"]);
    fireEvent.change(screen.getByPlaceholderText(/Nom, univers/), { target: { value: "alpha" } });
    expect(rows()).toEqual(["Alpha"]);
  });

  it("comparaison : identique, différent et non comparable", () => {
    renderAt("/comparaison?langue=a", "/comparaison", <ComparePage />);
    expect(screen.getByText("identique")).toBeInTheDocument();
    expect(screen.getByText("différent")).toBeInTheDocument();
    expect(screen.getByText(/Score de Gower : 0,50/)).toBeInTheDocument();
  });
});

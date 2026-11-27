import { bestRobustScore, EMPTY_FILTERS, filterLanguages, decade } from "../filters/filters";
import { scoreColor, NO_DATA, SCALE, legendItems } from "../map/colors";
import { FIXTURE, LANG_A, LANG_B } from "./fixture";

const run = (over: Partial<typeof EMPTY_FILTERS>) =>
  filterLanguages(FIXTURE.languages, { ...EMPTY_FILTERS, ...over }, FIXTURE.regions).map((l) => l.id);

describe("filtres combinables", () => {
  it("sans filtre, toutes les langues", () => expect(run({})).toEqual(["a", "b"]));
  it("recherche insensible aux accents et à la casse", () => expect(run({ text: "BETA" })).toEqual(["b"]));
  it("univers, type, syntaxe, morphologie, tons", () => {
    expect(run({ universe: "Univers B" })).toEqual(["b"]);
    expect(run({ category: "pseudo_language" })).toEqual(["b"]);
    expect(run({ syntax: "SOV" })).toEqual(["a"]);
    expect(run({ morphology: "agglutinative" })).toEqual(["a"]);
    expect(run({ phonology: "No tones" })).toEqual(["a"]);
  });
  it("une valeur inconnue ne satisfait jamais un filtre actif", () => {
    expect(run({ phonology: "Complex tones" })).toEqual([]);
    expect(run({ morphology: "fusional" })).toEqual([]);
  });
  it("écriture documentée ou non", () => {
    expect(run({ writing: "with" })).toEqual(["a"]);
    expect(run({ writing: "without" })).toEqual(["b"]);
  });
  it("période par décennie", () => {
    expect(decade(1984)).toBe("1980");
    expect(decade(null)).toBeNull();
    expect(run({ period: "2010" })).toEqual(["b"]);
  });
  it("les critères se combinent (ET logique)", () => {
    expect(run({ syntax: "SOV", universe: "Univers B" })).toEqual([]);
    expect(run({ syntax: "SVO", universe: "Univers B" })).toEqual(["b"]);
  });
  it("proximité minimale : seules les aires robustes comptent", () => {
    expect(bestRobustScore("a", FIXTURE.regions)).toBe(0.72); // 0,91 est peu robuste, donc ignoré
    expect(bestRobustScore("b", FIXTURE.regions)).toBeNull();
    expect(run({ minProximity: 0.7 })).toEqual(["a"]);
    expect(run({ minProximity: 0.8 })).toEqual([]);
  });
  it("famille fictive : aucune documentée, donc aucun résultat", () => expect(run({ family: "x" })).toEqual([]));
  it("les données de test restent cohérentes", () => {
    expect(LANG_A.scored).toBe(true);
    expect(LANG_B.scored).toBe(false);
  });
});

describe("échelle de couleurs", () => {
  it("classes bornées et absence de score", () => {
    expect(scoreColor(0)).toBe(SCALE[0]);
    expect(scoreColor(0.2)).toBe(SCALE[1]);
    expect(scoreColor(0.79)).toBe(SCALE[3]);
    expect(scoreColor(1)).toBe(SCALE[4]);
    expect(scoreColor(null)).toBe(NO_DATA);
    expect(scoreColor(Number.NaN)).toBe(NO_DATA);
  });
  it("légende de 5 classes couvrant [0, 1]", () => {
    const items = legendItems();
    expect(items).toHaveLength(5);
    expect(items[0].label).toBe("0.0 – 0.2");
    expect(items[4].label).toBe("0.8 – 1.0");
  });
});

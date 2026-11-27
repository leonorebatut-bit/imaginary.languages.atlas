import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { AtlasData } from "./types";

// Les données sont des JSON statiques produits par `python scripts/rebuild_all.py`
// (étape site_data). Le site ne calcule aucun score : il filtre et affiche.
const base = `${import.meta.env.BASE_URL}data/`;

async function getJson<T>(name: string, optional = false): Promise<T | null> {
  const res = await fetch(base + name);
  if (!res.ok) {
    if (optional) return null;
    throw new Error(`${name} : HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function loadAtlasData(): Promise<AtlasData> {
  const [languages, scripts, wals, regions, nearest, mapping, areas, manifest, land] = await Promise.all([
    getJson<AtlasData["languages"]>("languages.json"),
    getJson<AtlasData["scripts"]>("scripts.json"),
    getJson<AtlasData["wals"]>("wals_languages.json"),
    getJson<AtlasData["regions"]>("regions.json"),
    getJson<AtlasData["nearest"]>("nearest.json"),
    getJson<AtlasData["mapping"]>("mapping.json"),
    getJson<AtlasData["areas"]>("areas.json"),
    getJson<AtlasData["manifest"]>("manifest.json"),
    getJson<GeoJSON.FeatureCollection>("land.geojson", true),
  ]);
  return { languages: languages!, scripts: scripts!, wals: wals!, regions: regions!, nearest: nearest!,
           mapping: mapping!, areas: areas!, manifest: manifest!, land };
}

const Ctx = createContext<AtlasData | null>(null);

export function DataProvider({ children, initial }: { children: ReactNode; initial?: AtlasData }) {
  const [data, setData] = useState<AtlasData | null>(initial ?? null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (initial) return;
    loadAtlasData().then(setData).catch((e: Error) => setError(e.message));
  }, [initial]);
  if (error) {
    return (
      <main className="page">
        <h1>Données indisponibles</h1>
        <p>Impossible de charger les données du site ({error}). Lancez <code>python scripts/rebuild_all.py</code> pour les produire.</p>
      </main>
    );
  }
  if (!data) return <main className="page"><p className="muted">Chargement des données…</p></main>;
  return <Ctx.Provider value={data}>{children}</Ctx.Provider>;
}

export function useAtlas(): AtlasData {
  const d = useContext(Ctx);
  if (!d) throw new Error("useAtlas hors de DataProvider");
  return d;
}

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Area, RegionScore, WalsLanguage } from "../types";
import { NO_DATA, scoreColor } from "./colors";
import { fmtScore } from "../labels";

interface Props {
  land: GeoJSON.FeatureCollection | null;
  wals: WalsLanguage[];
  areas: Area[];
  regions: RegionScore[];          // scores de la langue sélectionnée (vide si aucune)
  robustOnly: boolean;
  selectedArea: string | null;
  onSelectArea: (area: string) => void;
}

// Carte : chaque langue WALS est un point placé à ses coordonnées WALS, coloré selon le
// score de son aire linguistique (AUTOTYP). Les aires peu robustes sont plus pâles et
// cerclées en pointillés ; les aires sans score sont grises.
export default function AtlasMap({ land, wals, areas, regions, robustOnly, selectedArea, onSelectArea }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const layer = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!el.current || map.current) return;
    const m = L.map(el.current, { worldCopyJump: true, minZoom: 1, maxZoom: 7, zoomSnap: 0.5, attributionControl: true })
      .setView([15, 10], 1.5);
    m.attributionControl.setPrefix(false);
    m.attributionControl.addAttribution("Fond : Natural Earth · Données : WALS (CC-BY), AUTOTYP (CC-BY)");
    if (land) {
      L.geoJSON(land, { style: { className: "land-shape", weight: 0.6, fillOpacity: 1 },
                       interactive: false }).addTo(m);
    }
    layer.current = L.layerGroup().addTo(m);
    map.current = m;
    return () => { m.remove(); map.current = null; };
  }, [land]);

  useEffect(() => {
    const g = layer.current;
    if (!g) return;
    g.clearLayers();
    const byArea = new Map(regions.map((r) => [r.area, r]));
    for (const w of wals) {
      if (!w.area) continue;
      const r = byArea.get(w.area);
      const show = r && (!robustOnly || r.robust);
      const color = show ? scoreColor(r!.score_genus_weighted) : NO_DATA;
      const weak = r && !r.robust;
      const marker = L.circleMarker([w.lat, w.lon], {
        radius: selectedArea === w.area ? 4.5 : 3,
        color: selectedArea === w.area ? "#e8590c" : color,
        weight: selectedArea === w.area ? 1.2 : 0.5,
        dashArray: weak ? "2 2" : undefined,
        fillColor: color,
        fillOpacity: show ? (weak ? 0.45 : 0.9) : 0.35,
      });
      marker.bindTooltip(`${w.name} · ${w.area}${r ? ` · aire ${fmtScore(r.score_genus_weighted)}` : ""}`);
      marker.on("click", () => onSelectArea(w.area!));
      marker.addTo(g);
    }
    for (const a of areas) {
      const r = byArea.get(a.area);
      const label = L.marker([a.lat, a.lon], {
        interactive: true,
        icon: L.divIcon({
          className: "area-label",
          html: `<span>${a.area}${r ? `<b>${fmtScore(r.score_genus_weighted)}</b>` : ""}</span>`,
        }),
      });
      label.on("click", () => onSelectArea(a.area));
      label.addTo(g);
    }
  }, [wals, areas, regions, robustOnly, selectedArea, onSelectArea]);

  return <div ref={el} className="atlas-map" role="region" aria-label="Carte des aires linguistiques" />;
}

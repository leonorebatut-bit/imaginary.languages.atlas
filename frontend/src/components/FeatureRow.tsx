import type { Feature } from "../types";
import { FEATURE_LABELS, formatValue } from "../labels";
import StatusBadge from "./StatusBadge";

export default function FeatureRow({ f, sourceTitles }: { f: Feature; sourceTitles: Record<string, string> }) {
  const meta = FEATURE_LABELS[f.feature_id];
  return (
    <div className={`feature ${f.status === "unavailable" ? "feature-na" : ""}`}>
      <div className="feature-head">
        <h4>{meta?.label ?? f.feature_id}</h4>
        <StatusBadge status={f.status} />
      </div>
      <p className="feature-value">
        {f.status === "unavailable" ? <span className="muted">null</span> : formatValue(f.value)}
        {f.unit && f.status !== "unavailable" ? <span className="muted"> {f.unit}</span> : null}
      </p>
      {meta?.definition ? <p className="feature-def">{meta.definition}</p> : null}
      <dl className="feature-meta">
        <dt>Méthode</dt><dd><code>{f.method}</code></dd>
        {f.source_ids.length > 0 && (<><dt>Source</dt><dd>{f.source_ids.map((s) => sourceTitles[s.split("@")[0]] ? `${sourceTitles[s.split("@")[0]]}${s.includes("@") ? ` (${s.split("@")[1]})` : ""}` : s).join(" ; ")}</dd></>)}
        {f.examples.length > 0 && (<><dt>Exemple</dt><dd className="example">{f.examples.slice(0, 2).join(" · ")}</dd></>)}
        {f.limits && (<><dt>Limites</dt><dd>{f.limits}</dd></>)}
      </dl>
    </div>
  );
}

"""Dependency-free curriculum reports (CSV, JSON, and self-contained HTML/SVG)."""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path


REPORT_FIELDS = (
    "stage", "scenario", "seed", "episode", "total_timesteps", "episode_reward",
    "rescued", "signal_transmitted", "collisions", "steps", "detection_step", "coverage_pct",
)


def _summary(records: list[dict]) -> list[dict]:
    summaries = []
    for scenario in sorted({str(row.get("scenario", "unknown")) for row in records}):
        rows = [row for row in records if row.get("scenario") == scenario]
        window = max(1, min(10, len(rows) // 3 or 1))

        def stats(group: list[dict]) -> dict:
            count = max(1, len(group))
            return {
                "rescue_rate": sum(bool(x.get("rescued")) for x in group) / count,
                "mean_collisions": sum(float(x.get("collisions", 0)) for x in group) / count,
                "mean_steps": sum(float(x.get("steps", 0)) for x in group) / count,
                "mean_coverage": sum(float(x.get("coverage_pct", 0)) for x in group) / count,
            }

        summaries.append({
            "scenario": scenario,
            "episodes": len(rows),
            "window": window,
            "before": stats(rows[:window]),
            "after": stats(rows[-window:]),
        })
    return summaries


def write_reports(records: list[dict], output_dir: Path, metadata: dict | None = None) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "episodes.csv"
    json_path = output_dir / "report.json"
    html_path = output_dir / "report.html"

    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=REPORT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    payload = {"metadata": metadata or {}, "episodes": records, "per_house": _summary(records)}
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    width, height = 900, 280
    rewards = [float(row.get("episode_reward", 0)) for row in records] or [0.0]
    lo, hi = min(rewards), max(rewards)
    span = max(1.0, hi - lo)
    points = " ".join(
        f"{20 + i * (width - 40) / max(1, len(rewards) - 1):.1f},"
        f"{height - 20 - (value - lo) * (height - 40) / span:.1f}"
        for i, value in enumerate(rewards)
    )
    rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{:.1%} → {:.1%}</td>"
        "<td>{:.2f} → {:.2f}</td><td>{:.1f} → {:.1f}</td></tr>".format(
            html.escape(item["scenario"]), item["episodes"],
            item["before"]["rescue_rate"], item["after"]["rescue_rate"],
            item["before"]["mean_collisions"], item["after"]["mean_collisions"],
            item["before"]["mean_steps"], item["after"]["mean_steps"],
        ) for item in payload["per_house"]
    )
    document = f"""<!doctype html><html><head><meta charset='utf-8'>
<title>House Rescue Learning Report</title><style>
body{{font:15px system-ui;background:#101722;color:#e9f1f7;max-width:1000px;margin:30px auto}}
table{{border-collapse:collapse;width:100%}}th,td{{padding:9px;border:1px solid #405064;text-align:left}}
svg{{background:#172334;border-radius:8px;width:100%;height:auto}}.note{{color:#a9bac9}}
</style></head><body><h1>House Rescue Learning Report</h1>
<p class='note'>Before/after values are measured episode windows; improvement is reported as observed, not guaranteed.</p>
<h2>Episode reward</h2><svg viewBox='0 0 {width} {height}' role='img' aria-label='Episode reward curve'>
<polyline fill='none' stroke='#55d6be' stroke-width='3' points='{points}'/></svg>
<h2>Per-house comparison</h2><table><thead><tr><th>House</th><th>Episodes</th>
<th>Rescue rate</th><th>Mean collisions</th><th>Mean steps</th></tr></thead><tbody>{rows}</tbody></table>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return {"csv": csv_path, "json": json_path, "html": html_path}

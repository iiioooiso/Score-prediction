"""Prepare and clean raw facets into processed CSV and a facet registry JSON.

Usage: python scripts/prepare_data.py
"""
from __future__ import annotations
import re
import json
import os
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = Path(os.getenv("FACETS_CSV_PATH", ROOT / "data" / "raw" / "Facets Assignment.csv"))
OUT_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def read_raw_lines(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"Raw facets file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines()]
    # Drop header if present
    if lines and lines[0].lower().startswith("facets"):
        lines = lines[1:]
    # keep non-empty
    return [l for l in lines if l]


def clean_text(s: str) -> str:
    s = s.strip()
    # remove numbering prefixes like '800.' or '644.' or '1) '
    s = re.sub(r"^\s*\d+[\.)\s-]*", "", s)
    # remove leading numbering like '800. Sufi practice:' and keep remainder
    s = s.rstrip(":").strip()
    # normalize whitespace
    s = re.sub(r"\s+", " ", s)
    # normalize casing — keep original casing but strip odd punctuation
    return s


def infer_metadata(name: str) -> Dict:
    n = name.lower()
    # richer keyword-based category mapping and descriptions
    if any(k in n for k in ("depress", "anhedonia", "hopeless", "hopelessness", "sadness", "mood")):
        category = "Mental Health"
        subcategory = "Mood"
        inferability = "high"
        evidence_type = "behavioral"
        description = f"Measures evidence of low mood, sadness, hopelessness, reduced motivation, and loss of interest related to {name}."
    elif "burnout" in n:
        category = "Mental Health"
        subcategory = "Work-related"
        inferability = "high"
        evidence_type = "behavioral"
        description = "Measures chronic exhaustion, cynicism, and reduced professional efficacy (burnout symptoms)."
    elif any(k in n for k in ("risk", "adventure", "risk-taking", "creative risk")):
        category = "Personality"
        subcategory = "Sensation/Adventure"
        inferability = "medium"
        evidence_type = "behavioral"
        description = "Indicates tendency to seek novel or risky experiences and take actions with potential negative consequences."
    elif any(k in n for k in ("iq", "intelligence", "cognitive", "working memory", "numerical reasoning")):
        category = "Cognitive"
        subcategory = "Ability"
        inferability = "low"
        evidence_type = "cognitive"
        description = "Relates to general cognitive ability, reasoning, and problem-solving skills; often not directly inferable from conversation."
    elif any(k in n for k in ("level", "count", "frequency", "age", "rate", "ratio", "presence", "biological")):
        category = "Physiological / Metadata"
        subcategory = "Physiological"
        inferability = "impossible"
        evidence_type = "physiological"
        description = "Physiological or measured values that cannot be reliably inferred from conversation alone."
    elif any(k in n for k in ("leadership", "leadership potential", "leadership styles", "delegation")):
        category = "Leadership"
        subcategory = "Styles"
        inferability = "medium"
        evidence_type = "behavioral"
        description = "Indicates leadership behaviors such as delegation, decision-making, and influence in group settings."
    elif any(k in n for k in ("spiritual", "religious", "quran", "sufi", "kabbalah", "hindu", "i ching", "bahá’í")):
        category = "Spiritual / Cultural"
        subcategory = "Religious Practices"
        inferability = "low"
        evidence_type = "self-report"
        description = "Refers to religious or spiritual practices and participation; often self-reported and culture-specific."
    elif any(k in n for k in ("compassion", "empathy", "warmhearted", "social intelligence")):
        category = "Personality"
        subcategory = "Prosocial"
        inferability = "high"
        evidence_type = "behavioral"
        description = "Indicates prosocial tendencies such as empathy, concern for others, and social awareness."
    else:
        category = "General"
        subcategory = None
        inferability = "medium"
        evidence_type = "behavioral"
        description = f"Measures indications or behaviors related to {name}."

    return {
        "category": category,
        "subcategory": subcategory,
        "description": description,
        "inferability": inferability,
        "evidence_type": evidence_type,
    }


def process(lines: List[str]) -> List[Dict]:
    cleaned = [clean_text(l) for l in lines]
    # remove duplicates while preserving order
    seen = set()
    unique = []
    for c in cleaned:
        if not c or len(c) < 2:
            continue
        if c.lower() in seen:
            continue
        seen.add(c.lower())
        unique.append(c)

    registry = []
    for i, name in enumerate(unique, start=1):
        meta = infer_metadata(name)
        item = {
            "facet_id": i,
            "facet_name": name,
            "category": meta["category"],
            "subcategory": meta["subcategory"],
            "description": meta["description"],
            "inferability": meta["inferability"],
            "evidence_type": meta["evidence_type"],
        }
        registry.append(item)
    return registry


def write_outputs(registry: List[Dict], out_dir: Path):
    import csv

    out_csv = out_dir / "processed_facets.csv"
    out_json = out_dir / "facet_registry.json"

    fieldnames = ["facet_id", "facet_name", "category", "subcategory", "description", "inferability", "evidence_type"]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in registry:
            writer.writerow(r)

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def main():
    lines = read_raw_lines(RAW_PATH)
    registry = process(lines)
    write_outputs(registry, OUT_DIR)
    print(f"Processed {len(registry)} facets -> {OUT_DIR}")


if __name__ == "__main__":
    main()

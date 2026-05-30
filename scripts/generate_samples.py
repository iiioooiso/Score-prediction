"""Generate sample conversations and deterministic mock scores.

Produces data/samples/samples.jsonl and samples.zip
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
import random
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CONV_BANK = {
    "mental_health": [
        "I've been feeling down, I don't enjoy things like I used to.",
        "Lately I'm exhausted, I can't seem to get motivated for work.",
        "I worry a lot and sometimes feel hopeless about the future.",
    ],
    "leadership": [
        "My manager asks for input and makes decisions together with the team.",
        "I often take charge in meetings and delegate tasks to others.",
        "I prefer clear roles but encourage people to contribute ideas.",
    ],
    "technical": [
        "I backed up my files regularly and use cloud snapshots daily.",
        "I can quickly identify performance bottlenecks in code.",
        "I follow testing best practices and write unit tests.",
    ],
    "relationships": [
        "I care for my partner and try to be supportive when they're stressed.",
        "I often volunteer to help friends move or organize community events.",
        "I find it hard to trust people after being let down before.",
    ],
    "spiritual": [
        "I attend weekly religious gatherings and practice prayer regularly.",
        "I enjoy silent retreats and meditation practices on weekends.",
    ],
}

CATEGORY_FACETS = {
    "mental_health": ["Depression Symptoms", "Burnout Symptoms", "Happiness", "Contentment Levels"],
    "leadership": ["Leadership Potential", "Delegation skills", "Decision-making speed"],
    "technical": ["Cloud-backup frequency", "Data Analysis", "Troubleshooting technical issues"],
    "relationships": ["Empathy", "Compassion", "Trust in others"],
    "spiritual": ["Religious practice frequency", "Holiness", "Spiritual virtue: Humility practice index"],
}


def deterministic_score(conv: str, facet_name: str) -> dict:
    h = int(hashlib.sha256((conv + facet_name).encode()).hexdigest(), 16)
    score = (h % 5) + 1
    confidence = 0.3 + ((h % 70) / 100)
    reason = f"Mock deterministic reason for {facet_name}."
    return {"score": score, "confidence": round(confidence, 3), "reason": reason}


def main(n=50):
    from zipfile import ZipFile
    out_jsonl = OUT_DIR / "samples.jsonl"
    with out_jsonl.open("w", encoding="utf-8") as f:
        cats = list(CONV_BANK.keys())
        for i in range(n):
            cat = random.choice(cats)
            conv = random.choice(CONV_BANK[cat])
            # small variation
            if i % 3 == 0:
                conv = conv + " I had a rough week."
            facets = CATEGORY_FACETS.get(cat, [])
            scored = []
            for facet in facets:
                scored.append({"facet_name": facet, **deterministic_score(conv, facet)})
            entry = {"id": i + 1, "category": cat, "conversation": conv, "scores": scored}
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # create zip
    zip_path = OUT_DIR / "samples.zip"
    with ZipFile(zip_path, "w") as zf:
        zf.write(out_jsonl, arcname="samples.jsonl")

    print(f"Wrote {n} sample conversations to {out_jsonl} and {zip_path}")


if __name__ == "__main__":
    main(50)

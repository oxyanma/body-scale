"""Export measurements to Obsidian vault as a markdown weight log."""
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Path to the vault weight log (relative to BRAIN root)
VAULT_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "vault", "03-areas", "health", "weight-log.md"
)

FRONTMATTER = """---
type: log
title: "Weight Log"
tags:
  - health
  - weight
  - tracking
  - area/health
related:
  - "[[03-areas/health/index|Health]]"
  - "[[03-areas/health/analyses/2026-04-06-body-composition|BIA Baseline]]"
---

# Weight Log

> Auto-updated by [BioScale](http://127.0.0.1:8050) after each weighing.

| Date | Weight | BMI | Fat% | Muscle% | Water% | Visceral | Protein% | BMR | Score |
|------|--------|-----|------|---------|--------|----------|----------|-----|-------|
"""


def export_to_vault(measurement):
    """Append a measurement row to the vault weight log markdown table.

    Args:
        measurement: a Measurement ORM object (already committed to DB).
    """
    try:
        log_path = VAULT_LOG_PATH

        # Create file with header if it doesn't exist
        if not os.path.exists(log_path):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(FRONTMATTER)

        dt = measurement.measured_at or datetime.now()
        date_str = dt.strftime("%Y-%m-%d %H:%M")

        row = (
            f"| {date_str} "
            f"| {measurement.weight_kg:.2f} "
            f"| {measurement.bmi:.1f} "
            f"| {_fmt(measurement.body_fat_percent)} "
            f"| {_fmt(measurement.muscle_mass_percent)} "
            f"| {_fmt(measurement.body_water_percent)} "
            f"| {_fmt(measurement.visceral_fat)} "
            f"| {_fmt(measurement.protein_percent)} "
            f"| {_fmti(measurement.bmr)} "
            f"| {_fmti(measurement.body_score)} |\n"
        )

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(row)

        logger.info(f"Vault export: {date_str} {measurement.weight_kg:.2f} kg")
    except Exception as e:
        logger.error(f"Vault export failed: {e}")


def _fmt(v):
    """Format float or return --."""
    if v is None:
        return "--"
    return f"{v:.1f}"


def _fmti(v):
    """Format int or return --."""
    if v is None:
        return "--"
    return f"{v:.0f}"

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

| Date | Weight | BMI | Fat% | FatKg | SubcFat | Visceral | Muscle% | MuscleKg | SMM | LBM | FFMI | SMI | Water% | WaterKg | Bone | Protein% | ProteinKg | BMR | TDEE | MetAge | Score | Ideal | BodyType | LArmMus | RArmMus | LLegMus | RLegMus | LArmFat | RArmFat | LLegFat | RLegFat | Impedance |
|------|--------|-----|------|-------|---------|----------|---------|----------|-----|-----|------|-----|--------|---------|------|----------|-----------|-----|------|--------|-------|-------|----------|---------|---------|---------|---------|---------|---------|---------|---------|-----------|
"""


def export_to_vault(measurement, metrics=None):
    """Append a measurement row to the vault weight log markdown table.

    Args:
        measurement: a Measurement ORM object (already committed to DB).
        metrics: optional dict from get_all_metrics() for derived fields not in DB.
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

        md = metrics or {}

        # Values from ORM (always available)
        fat_pct = measurement.body_fat_percent
        fat_kg = _fmt(measurement.weight_kg * fat_pct / 100 if fat_pct else None)
        water_kg = _fmt(measurement.weight_kg * measurement.body_water_percent / 100
                        if measurement.body_water_percent else None)

        # Metrics dict provides derived fields not stored in DB
        protein_kg  = _fmt(md.get("protein_mass_kg"))
        body_type   = md.get("body_type") or "--"
        la_mus      = _fmt(md.get("left_arm_muscle_kg"))
        ra_mus      = _fmt(md.get("right_arm_muscle_kg"))
        ll_mus      = _fmt(md.get("left_leg_muscle_kg"))
        rl_mus      = _fmt(md.get("right_leg_muscle_kg"))
        la_fat      = _fmt(md.get("left_arm_fat_kg"))
        ra_fat      = _fmt(md.get("right_arm_fat_kg"))
        ll_fat      = _fmt(md.get("left_leg_fat_kg"))
        rl_fat      = _fmt(md.get("right_leg_fat_kg"))

        row = (
            f"| {date_str} "
            f"| {measurement.weight_kg:.2f} "
            f"| {measurement.bmi:.1f} "
            f"| {_fmt(fat_pct)} "
            f"| {fat_kg} "
            f"| {_fmt(measurement.subcutaneous_fat_kg)} "
            f"| {_fmt(measurement.visceral_fat)} "
            f"| {_fmt(measurement.muscle_mass_percent)} "
            f"| {_fmt(measurement.fat_free_mass_kg)} "
            f"| {_fmt(measurement.smm_kg)} "
            f"| {_fmt(measurement.lbm_kg)} "
            f"| {_fmt(measurement.ffmi)} "
            f"| {_fmt(measurement.smi)} "
            f"| {_fmt(measurement.body_water_percent)} "
            f"| {water_kg} "
            f"| {_fmt(measurement.bone_mass_kg)} "
            f"| {_fmt(measurement.protein_percent)} "
            f"| {protein_kg} "
            f"| {_fmti(measurement.bmr)} "
            f"| {_fmti(measurement.tdee)} "
            f"| {_fmti(measurement.metabolic_age)} "
            f"| {_fmti(measurement.body_score)} "
            f"| {_fmt(measurement.ideal_weight_kg)} "
            f"| {body_type} "
            f"| {la_mus} "
            f"| {ra_mus} "
            f"| {ll_mus} "
            f"| {rl_mus} "
            f"| {la_fat} "
            f"| {ra_fat} "
            f"| {ll_fat} "
            f"| {rl_fat} "
            f"| {_fmti(measurement.impedance)} |\n"
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

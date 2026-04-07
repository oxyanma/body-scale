"""One-time script: rebuild vault/weight-log.md from DB with all 32 columns."""
from database.db import SessionLocal
from database.models import Measurement, User
from calculations.body_composition import get_all_metrics
from dashboard.vault_export import export_to_vault, FRONTMATTER, VAULT_LOG_PATH
import os

db = SessionLocal()
measurements = db.query(Measurement).order_by(Measurement.measured_at).all()
users = {u.id: u for u in db.query(User).all()}

os.makedirs(os.path.dirname(VAULT_LOG_PATH), exist_ok=True)
with open(VAULT_LOG_PATH, 'w', encoding='utf-8') as f:
    f.write(FRONTMATTER)

for m in measurements:
    u = users.get(m.user_id)
    if u:
        metrics = get_all_metrics(
            m.weight_kg, u.height_cm, u.age, u.sex,
            impedance=m.impedance,
            activity_level=u.activity_level,
            waist_cm=u.waist_cm, hip_cm=u.hip_cm,
        )
    else:
        metrics = {}
    export_to_vault(m, metrics=metrics)
    print(f"Exported: {m.measured_at} {m.weight_kg}kg "
          f"type={metrics.get('body_type')} "
          f"la_mus={metrics.get('left_arm_muscle_kg')}")

db.close()
print("Done.")

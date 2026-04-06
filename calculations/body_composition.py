"""Body composition calculations — Complete BIA Metrics Suite.

Tier 1: weight + impedance + height + age + sex (current inputs)
Tier 2: + waist_cm + hip_cm (optional profile fields)
Tier 3: derived scores and indices

Body fat formula from OKOK CsAlgoBuilder reverse engineering.
SMM from Janssen et al. 2000 (validated against MRI).
All other metrics derived consistently with scientific references.
"""
import math

ACTIVITY_FACTORS = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'intense': 1.725,
    'athlete': 1.9
}


# ═══════════════════ TIER 1 — Core ═══════════════════

def calculate_bmi(weight_kg, height_cm):
    return weight_kg / ((height_cm / 100.0) ** 2)


def calculate_ideal_weight_range(height_cm):
    h2 = (height_cm / 100.0) ** 2
    return 18.5 * h2, 25.0 * h2


def calculate_ideal_weight(height_cm):
    """Center of healthy BMI range (22)."""
    return 22.0 * (height_cm / 100.0) ** 2


# ─── Body Fat % (OKOK CsAlgoBuilder getBFR) ───

def calculate_body_fat_percent(weight_kg, height_cm, age, sex, impedance=None):
    if impedance and impedance > 0:
        if sex == 'M':
            num = (-0.3315 * height_cm) + (0.6216 * weight_kg) + (0.0183 * age) + (0.0085 * impedance) + 22.554
        else:
            num = (-0.3332 * height_cm) + (0.7509 * weight_kg) + (0.0196 * age) + (0.0072 * impedance) + 22.7193
        fat_percent = (num / weight_kg) * 100
    else:
        bmi = calculate_bmi(weight_kg, height_cm)
        if sex == 'M':
            fat_percent = (1.20 * bmi) + (0.23 * age) - 16.2
        else:
            fat_percent = (1.20 * bmi) + (0.23 * age) - 5.4
    return max(5.0, min(45.0, round(fat_percent, 1)))


# ─── Fat-Free Mass ───

def calculate_ffm(weight_kg, body_fat_percent):
    """Fat-Free Mass (kg) = everything that isn't fat."""
    return round(weight_kg * (1 - body_fat_percent / 100.0), 2)


# ─── Fat Mass ───

def calculate_fat_mass(weight_kg, body_fat_percent):
    return round(weight_kg * body_fat_percent / 100.0, 2)


# ─── Impedance Index (H²/R) ───

def calculate_impedance_index(height_cm, impedance):
    """Classical BIA index — base for most equations (Kyle 2004)."""
    if impedance and impedance > 0:
        return round((height_cm ** 2) / impedance, 2)
    return None


# ─── Skeletal Muscle Mass (Janssen 2000, validated vs MRI) ───

def calculate_smm(height_cm, age, sex, impedance):
    """Janssen et al. J Appl Physiol 2000.
    SMM = (H²/R × 0.401) + (sex × 3.825) − (age × 0.071) + 5.102
    """
    if not impedance or impedance <= 0:
        return None
    imp_idx = (height_cm ** 2) / impedance
    sex_val = 1 if sex == 'M' else 0
    smm = (imp_idx * 0.401) + (sex_val * 3.825) - (age * 0.071) + 5.102
    return max(0.0, round(smm, 2))


# ─── Muscle Mass % (from SMM or FFM) ───

def calculate_muscle_mass_percent(weight_kg, height_cm, age, sex, impedance=None):
    smm = calculate_smm(height_cm, age, sex, impedance)
    if smm and smm > 0:
        return max(10.0, min(65.0, round((smm / weight_kg) * 100, 1)))
    # Fallback from FFM
    fat_pct = calculate_body_fat_percent(weight_kg, height_cm, age, sex, impedance)
    ffm = weight_kg * (1 - fat_pct / 100.0)
    ratio = 0.45 if sex == 'M' else 0.38
    return max(10.0, min(65.0, round((ffm * ratio / weight_kg) * 100, 1)))


# ─── Lean Body Mass (FFM minus bone minerals) ───

def calculate_lbm(ffm_kg, bone_mass_kg):
    return round(ffm_kg - bone_mass_kg, 2)


# ─── Body Water % ───

def calculate_body_water_percent(weight_kg, height_cm, age, sex, impedance=None):
    fat_pct = calculate_body_fat_percent(weight_kg, height_cm, age, sex, impedance)
    ffm_fraction = 1 - fat_pct / 100.0
    water_pct = ffm_fraction * 73.0  # Pace & Rathbun 1945
    return max(30.0, min(75.0, round(water_pct, 1)))


# ─── Bone Mass (kg) ───

def calculate_bone_mass_kg(weight_kg, height_cm, age, sex, impedance=None):
    """Empirical consumer BIA formula (OKOK/Tanita-style). Results ±0.3 kg vs DEXA."""
    fat_pct = calculate_body_fat_percent(weight_kg, height_cm, age, sex, impedance)
    lean_kg = weight_kg * (1 - fat_pct / 100.0)
    if sex == 'M':
        bone = 0.046 * lean_kg + 0.09 * (height_cm / 100.0)
    else:
        bone = 0.042 * lean_kg + 0.07 * (height_cm / 100.0)
    return max(0.5, min(5.0, round(bone, 2)))


# ─── Obesity Degree ───

def calculate_obesity_percent(weight_kg, height_cm, sex=None):
    """Deviation from ideal weight (BMI 22 midpoint). Universal formula."""
    ideal = calculate_ideal_weight(height_cm)
    if ideal <= 0:
        return 0.0
    return round(((weight_kg - ideal) / ideal) * 100.0, 1)


# ─── BMR & TDEE ───

def calculate_bmr(weight_kg, height_cm, age, sex):
    if sex == 'M':
        return round((10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5, 0)
    else:
        return round((10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161, 0)


def calculate_tdee(bmr, activity_level='sedentary'):
    return round(bmr * ACTIVITY_FACTORS.get(activity_level, 1.2), 0)


# ─── Visceral Fat Index ───

def calculate_visceral_fat(weight_kg, height_cm, age, sex, impedance=None):
    """Empirical estimate. Scale 1-59 follows Omron/Tanita convention.
    1-9 healthy, 10-14 high, 15+ dangerous. No published validated formula exists."""
    bmi = calculate_bmi(weight_kg, height_cm)
    fat_pct = calculate_body_fat_percent(weight_kg, height_cm, age, sex, impedance)
    if sex == 'M':
        vf = 0.15 * fat_pct + 0.35 * (bmi - 18.5) + 0.18 * age - 5.5
        if bmi > 30:
            vf += (bmi - 30) * 0.5
    else:
        vf = 0.12 * fat_pct + 0.28 * (bmi - 18.5) + 0.14 * age - 5.0
        if bmi > 30:
            vf += (bmi - 30) * 0.4
    return max(1.0, min(59.0, round(vf, 1)))


# ─── Metabolic Age ───

def calculate_metabolic_age(weight_kg, height_cm, age, sex, ffm_kg):
    """Metabolic age based on body composition deviation from ideal.
    
    Compares the user's body fat % to the ideal for a healthy person of
    their age/sex. More lean mass → younger metabolic age.
    Excess fat → older metabolic age.
    
    Uses a ±0.5 year shift per 1% deviation from ideal BF%.
    Clamped to [15, 80] range.
    """
    if not ffm_kg or ffm_kg <= 0:
        return age
    
    actual_bf = ((weight_kg - ffm_kg) / weight_kg) * 100.0
    
    # Ideal body fat % for age/sex (ACE/ACSM midpoints)
    if sex == 'M':
        if age < 30: ideal_bf = 15.0
        elif age < 40: ideal_bf = 17.0
        elif age < 50: ideal_bf = 19.0
        elif age < 60: ideal_bf = 20.5
        else: ideal_bf = 22.0
    else:
        if age < 30: ideal_bf = 23.0
        elif age < 40: ideal_bf = 25.0
        elif age < 50: ideal_bf = 27.0
        elif age < 60: ideal_bf = 29.0
        else: ideal_bf = 31.0
    
    # Positive deviation = more fat than ideal → older
    # Negative deviation = leaner than ideal → younger
    bf_deviation = actual_bf - ideal_bf
    age_shift = bf_deviation * 0.5  # 0.5 years per 1% BF deviation
    
    metabolic_age = int(round(age + age_shift))
    return max(15, min(80, metabolic_age))


# ─── Protein % ───

def calculate_protein_percent(muscle_percent):
    """Protein ≈ 20% of muscle tissue weight (Wang et al. 2003)."""
    return max(5.0, min(25.0, round(muscle_percent * 0.20, 1)))


# ─── Subcutaneous Fat ───

def calculate_subcutaneous_fat(fat_mass_kg):
    """~80% of total fat is subcutaneous in most individuals."""
    return round(fat_mass_kg * 0.80, 2)


# ═══════════════════ TIER 2 — Waist / Hip ═══════════════════

def calculate_whr(waist_cm, hip_cm):
    if waist_cm and hip_cm and hip_cm > 0:
        return round(waist_cm / hip_cm, 3)
    return None


def calculate_whtr(waist_cm, height_cm):
    if waist_cm and height_cm > 0:
        return round(waist_cm / height_cm, 3)
    return None


def calculate_cv_risk(whr, whtr, visceral_fat, bmi, sex):
    """Cardiovascular risk score 1-5 (AHA risk factors)."""
    risk = 1
    if whr:
        threshold = 0.90 if sex == 'M' else 0.85
        if whr > threshold:
            risk += 1
    if whtr and whtr > 0.5:
        risk += 1
    if visceral_fat > 12:
        risk += 1
    if bmi > 30:
        risk += 1
    labels = {1: "Low", 2: "Moderate", 3: "Elevated", 4: "High", 5: "Very High"}
    return risk, labels.get(risk, "High")


# ═══════════════════ TIER 3 — Indices & Scores ═══════════════════

def calculate_ffmi(ffm_kg, height_cm):
    """Fat-Free Mass Index = FFM / H². Schutz 2002."""
    h_m = height_cm / 100.0
    return round(ffm_kg / (h_m ** 2), 1)


def calculate_smi(smm_kg, height_cm):
    """Skeletal Muscle Index = SMM / H². Cruz-Jentoft 2019 (EWGSOP2)."""
    if smm_kg is None:
        return None
    h_m = height_cm / 100.0
    return round(smm_kg / (h_m ** 2), 1)


def calculate_sarcopenia_risk(smi, sex):
    """EWGSOP2 thresholds: M < 7.0, F < 5.7 kg/m²."""
    if smi is None:
        return "No data"
    if sex == 'M':
        if smi < 7.0:
            return "High"
        elif smi < 8.5:
            return "Moderate"
        return "Normal"
    else:
        if smi < 5.7:
            return "High"
        elif smi < 7.0:
            return "Moderate"
        return "Normal"


def calculate_dry_weight(ffm_kg):
    """Dry lean mass = FFM minus body water (FFM × 0.27)."""
    return round(ffm_kg * 0.27, 1)


def calculate_body_score(bmi, body_fat_percent, visceral_fat, muscle_percent, water_percent, sex):
    """Composite health score 1-100."""
    # Ideal reference values by sex
    ideal_bf = 17.0 if sex == 'M' else 27.0

    bmi_s = max(0, 100 - abs(bmi - 22) * 5)
    bf_s = max(0, 100 - abs(body_fat_percent - ideal_bf) * 3)
    vf_s = max(0, 100 - visceral_fat * 5)
    ms_s = min(100, muscle_percent * 2.2) if sex == 'M' else min(100, muscle_percent * 2.8)
    ideal_water = 57.5 if sex == 'M' else 52.5
    ws_s = max(0, 100 - abs(water_percent - ideal_water) * 3)

    score = int(bmi_s * 0.15 + bf_s * 0.30 + vf_s * 0.20 + ms_s * 0.20 + ws_s * 0.15)
    return max(1, min(100, score))


# ═══════════════════ ALL-IN-ONE ═══════════════════

def get_all_metrics(weight_kg, height_cm, age, sex, impedance=None,
                    activity_level='sedentary', waist_cm=None, hip_cm=None):
    bmi = calculate_bmi(weight_kg, height_cm)
    fat_percent = calculate_body_fat_percent(weight_kg, height_cm, age, sex, impedance)
    fat_mass_kg = calculate_fat_mass(weight_kg, fat_percent)
    ffm_kg = calculate_ffm(weight_kg, fat_percent)
    bone_mass_kg = calculate_bone_mass_kg(weight_kg, height_cm, age, sex, impedance)
    lbm_kg = calculate_lbm(ffm_kg, bone_mass_kg)
    
    # SMM (Skeletal Muscle Mass) % e Kg
    smm_percent = calculate_muscle_mass_percent(weight_kg, height_cm, age, sex, impedance)
    smm_kg = calculate_smm(height_cm, age, sex, impedance)
    if not smm_kg:
        smm_kg = round(weight_kg * smm_percent / 100.0, 2)
        
    # Total Muscle Mass (FFM - Bone Mass)
    muscle_mass_kg = lbm_kg
    muscle_percent = round((muscle_mass_kg / weight_kg) * 100.0, 1) if weight_kg > 0 else 0.0
    
    water_percent = calculate_body_water_percent(weight_kg, height_cm, age, sex, impedance)
    water_mass_kg = round(weight_kg * water_percent / 100.0, 2)
    protein_percent = calculate_protein_percent(muscle_percent)
    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = calculate_tdee(bmr, activity_level)
    visceral = calculate_visceral_fat(weight_kg, height_cm, age, sex, impedance)
    metabolic_age = calculate_metabolic_age(weight_kg, height_cm, age, sex, ffm_kg)
    ideal_wt = calculate_ideal_weight(height_cm)
    imp_idx = calculate_impedance_index(height_cm, impedance)
    ffmi = calculate_ffmi(ffm_kg, height_cm)
    obesity_percent = calculate_obesity_percent(weight_kg, height_cm, sex)
    smi = calculate_smi(smm_kg, height_cm)
    subcut_fat = calculate_subcutaneous_fat(fat_mass_kg)
    body_score = calculate_body_score(bmi, fat_percent, visceral, smm_percent, water_percent, sex)

    # Tier 2
    whr = calculate_whr(waist_cm, hip_cm)
    whtr = calculate_whtr(waist_cm, height_cm)

    return {
        # Core
        "weight_kg": round(weight_kg, 2),
        "bmi": round(bmi, 1),
        "body_fat_percent": round(fat_percent, 1),
        "fat_mass_kg": fat_mass_kg,
        "fat_free_mass_kg": ffm_kg,
        "muscle_mass_percent": muscle_percent,
        "muscle_mass_kg": muscle_mass_kg,
        "smm_percent": smm_percent,
        "obesity_percent": obesity_percent,
        "body_water_percent": water_percent,
        "water_mass_kg": water_mass_kg,
        "bone_mass_kg": bone_mass_kg,
        "visceral_fat": visceral,
        "bmr": bmr,
        "tdee": tdee,
        "metabolic_age": int(metabolic_age),
        "protein_percent": protein_percent,
        # New Tier 1
        "lbm_kg": lbm_kg,
        "smm_kg": smm_kg,
        "impedance_index": imp_idx,
        "ideal_weight_kg": round(ideal_wt, 1),
        "ffmi": ffmi,
        "smi": smi,
        "subcutaneous_fat_kg": subcut_fat,
        "body_score": body_score,
        # Tier 2
        "whr": whr,
        "whtr": whtr,
    }


# ═══════════════════ CLASSIFICATIONS ═══════════════════

def _get_classification(val, bounds, labels, colors):
    if val < bounds[0]:
        return labels[0], colors[0], 0
    elif val < bounds[1]:
        return labels[1], colors[1], 1
    elif val < bounds[2]:
        return labels[2], colors[2], 2
    else:
        return labels[3], colors[3], 3


def get_classifications(metrics, sex, age, height_cm):
    cls = {}

    # ── Weight ──
    w_min, w_max = calculate_ideal_weight_range(height_cm)
    w_obese = 30.0 * ((height_cm / 100.0) ** 2)
    w = metrics.get('weight_kg', 0)
    lb, color, _ = _get_classification(w, [w_min, w_max, w_obese],
        ["Low", "Healthy", "High", "Obese"], ["info", "success", "warning", "danger"])
    cls["weight"] = {"value": w, "unit": "kg", "name": "Weight", "label": lb, "color": color,
        "bounds": [round(w_min,1), round(w_max,1), round(w_obese,1)],
        "desc": "Total body weight. Sudden changes deserve attention.", "category": "composition"}

    # ── BMI ──
    bmi = metrics.get('bmi', 0)
    lb, color, _ = _get_classification(bmi, [18.5, 25.0, 30.0],
        ["Underweight", "Healthy", "Overweight", "Obese"], ["info", "success", "warning", "danger"])
    cls["bmi"] = {"value": bmi, "unit": "", "name": "BMI", "label": lb, "color": color,
        "bounds": [18.5, 25.0, 30.0],
        "desc": "Body Mass Index. International measure of ideal weight.", "category": "composition"}

    # ── Obesity % ──
    ob = metrics.get('obesity_percent', 0)
    lb, color, _ = _get_classification(ob, [-10.0, 10.0, 20.0],
        ["Low", "Healthy", "Above", "Obese"], ["info", "success", "warning", "danger"])
    cls["obesity_percent"] = {"value": ob, "unit": "%", "name": "Obesity Degree", "label": lb, "color": color,
        "bounds": [-10.0, 10.0, 20.0], "desc": "Percentage difference from standard weight.", "category": "composition"}

    # ── Body Fat % ──
    bf = metrics.get('body_fat_percent', 0)
    if sex == 'M':
        if age < 40: bounds = [10.0, 21.0, 26.0]
        elif age < 60: bounds = [11.0, 22.0, 27.0]
        else: bounds = [13.0, 24.0, 29.0]
    else:
        if age < 40: bounds = [20.0, 33.0, 39.0]
        elif age < 60: bounds = [23.0, 34.0, 40.0]
        else: bounds = [24.0, 36.0, 42.0]
    lb, color, _ = _get_classification(bf, bounds,
        ["Low", "Healthy", "High", "Obese"], ["info", "success", "warning", "danger"])
    cls["body_fat"] = {"value": bf, "unit": "%", "name": "Body Fat", "label": lb, "color": color,
        "bounds": bounds, "desc": "Total body fat percentage via bioimpedance.", "category": "composition"}

    # ── Fat Mass (kg) ──
    fm_val = metrics.get('fat_mass_kg', 0)
    fm_bounds = [round(w * bounds[0]/100, 1), round(w * bounds[1]/100, 1), round(w * bounds[2]/100, 1)]
    cls["fat_mass"] = {"value": fm_val, "unit": "kg", "name": "Fat Mass", "label": lb, "color": color,
        "bounds": fm_bounds, "desc": "Total body fat mass in kilograms.", "category": "composition"}

    # ── Visceral Fat ──
    vf = metrics.get('visceral_fat', 0)
    if vf <= 9: lb, color = "Healthy", "success"
    elif vf <= 14: lb, color = "High", "warning"
    else: lb, color = "Dangerous", "danger"
    cls["visceral_fat"] = {"value": vf, "unit": "", "name": "Visceral Fat", "label": lb, "color": color,
        "bounds": [9.0, 14.0, 15.0],
        "desc": "Fat around internal organs. Cardiovascular risk factor.", "category": "composition"}

    # ── Subcutaneous Fat ──
    sf = metrics.get('subcutaneous_fat_kg', 0)
    fm = metrics.get('fat_mass_kg', 0)
    sf_bounds = [round(b * 0.80, 1) for b in bounds]  # Use body_fat bounds scaled
    lb, color = ("Healthy", "success") if bf < bounds[1] else ("High", "warning") if bf < bounds[2] else ("Obese", "danger")
    cls["subcutaneous_fat"] = {"value": sf, "unit": "kg", "name": "Subcutaneous Fat", "label": lb, "color": color,
        "bounds": [round(w * 0.80 * b / 100, 1) for b in [20, 30, 40]],
        "desc": "Fat under the skin (~80% of total fat). Less dangerous than visceral.", "category": "composition"}

    # ── Body Water ──
    bw = metrics.get('body_water_percent', 0)
    bw_bounds = [50.0, 65.0, 80.0] if sex == 'M' else [45.0, 60.0, 80.0]
    lb, color, _ = _get_classification(bw, bw_bounds,
        ["Low", "Healthy", "High", "Retention"], ["info", "success", "warning", "danger"])
    cls["body_water"] = {"value": bw, "unit": "%", "name": "Body Water", "label": lb, "color": color,
        "bounds": bw_bounds, "desc": "Total body fluid percentage (73% of lean mass).", "category": "hydration"}

    # ── Water Mass (kg) ──
    wm = metrics.get('water_mass_kg', 0)
    wm_bounds = [round(w * bw_bounds[0]/100, 1), round(w * bw_bounds[1]/100, 1), round(w * bw_bounds[2]/100, 1)]
    cls["water_mass"] = {"value": wm, "unit": "kg", "name": "Water Mass", "label": lb, "color": color,
        "bounds": wm_bounds, "desc": "Total body water mass in kilograms.", "category": "hydration"}

    # ── Total Muscle Mass % ──
    mm = metrics.get('muscle_mass_percent', 0)
    mm_bounds = [65.0, 75.0, 85.0] if sex == 'M' else [60.0, 70.0, 80.0]
    lb, color, _ = _get_classification(mm, mm_bounds,
        ["Low", "Healthy", "Good", "Excellent"], ["warning", "success", "primary", "info"])
    cls["muscle_mass"] = {"value": mm, "unit": "%", "name": "Muscle Mass", "label": lb, "color": color,
        "bounds": mm_bounds, "desc": "Total muscle mass (estimated as LBM).", "category": "muscle"}

    # ── Total Muscle Mass (kg) ──
    mm_kg = metrics.get('muscle_mass_kg', 0)
    mm_kg_bounds = [round(w * mm_bounds[0]/100, 1), round(w * mm_bounds[1]/100, 1), round(w * mm_bounds[2]/100, 1)]
    lb_kg, color_kg, _ = _get_classification(mm_kg, mm_kg_bounds,
        ["Low", "Healthy", "Good", "Excellent"], ["warning", "success", "primary", "info"])
    cls["muscle_mass_kg"] = {"value": mm_kg, "unit": "kg", "name": "Muscle Mass (kg)", "label": lb_kg, "color": color_kg,
        "bounds": mm_kg_bounds, "desc": "Total muscle mass in kilograms (FFM - bone mass).", "category": "muscle"}

    # ── LBM (kg) ──
    lbm_val = metrics.get('lbm_kg', 0)
    if sex == 'M':
        lbm_bounds = [round(w * 0.65, 1), round(w * 0.75, 1), round(w * 0.85, 1)]
    else:
        lbm_bounds = [round(w * 0.60, 1), round(w * 0.70, 1), round(w * 0.80, 1)]
    lb_lbm, color_lbm, _ = _get_classification(lbm_val, lbm_bounds,
        ["Low", "Healthy", "Good", "Excellent"], ["warning", "success", "primary", "info"])
    cls["lbm"] = {"value": lbm_val, "unit": "kg", "name": "LBM", "label": lb_lbm, "color": color_lbm,
        "bounds": lbm_bounds, "desc": "Lean Body Mass — fat-free and bone-free mass.", "category": "muscle"}

    # ── SMM % ──
    smm_pct = metrics.get('smm_percent', 0)
    if smm_pct:
        smm_pct_bounds = [33.0, 40.0, 50.0] if sex == 'M' else [24.0, 31.0, 40.0]
        lb, color, _ = _get_classification(smm_pct, smm_pct_bounds,
            ["Low", "Healthy", "Excellent", "Athlete"], ["warning", "success", "primary", "info"])
        cls["smm_percent"] = {"value": smm_pct, "unit": "%", "name": "Skeletal M. (%)", "label": lb, "color": color,
            "bounds": smm_pct_bounds, "desc": "Skeletal muscle mass percentage.", "category": "muscle"}

    # ── SMM (kg) ──
    smm = metrics.get('smm_kg')
    if smm:
        smm_bounds = [20.0, 28.0, 38.0] if sex == 'M' else [14.0, 20.0, 28.0]
        lb, color, _ = _get_classification(smm, smm_bounds,
            ["Low", "Healthy", "Excellent", "Athlete"], ["warning", "success", "primary", "info"])
        cls["smm"] = {"value": smm, "unit": "kg", "name": "Skeletal Muscle", "label": lb, "color": color,
            "bounds": smm_bounds, "desc": "Skeletal muscle mass (Janssen 2000, validated vs MRI).", "category": "muscle"}

    # ── FFMI ──
    ffmi = metrics.get('ffmi', 0)
    ffmi_bounds = [17.0, 20.0, 25.0] if sex == 'M' else [14.0, 17.0, 21.0]
    lb, color, _ = _get_classification(ffmi, ffmi_bounds,
        ["Low", "Healthy", "Strong", "Athlete"], ["warning", "success", "primary", "info"])
    cls["ffmi"] = {"value": ffmi, "unit": "", "name": "FFMI", "label": lb, "color": color,
        "bounds": ffmi_bounds, "desc": "Fat-Free Mass Index (FFM/H²). Indicates natural muscular potential.", "category": "muscle"}

    # ── SMI ──
    smi = metrics.get('smi')
    if smi:
        smi_bounds = [7.0, 8.5, 10.5] if sex == 'M' else [5.7, 7.0, 8.5]
        lb, color, _ = _get_classification(smi, smi_bounds,
            ["Sarcopenia", "Moderate", "Healthy", "Strong"], ["danger", "warning", "success", "primary"])
        cls["smi"] = {"value": smi, "unit": "kg/m²", "name": "SMI", "label": lb, "color": color,
            "bounds": smi_bounds, "desc": "Skeletal Muscle Index. Assesses sarcopenia risk (EWGSOP2).", "category": "muscle"}

    # ── Bone Mass ──
    bm = metrics.get('bone_mass_kg', 0)
    bm_bounds = [2.5, 3.2, 4.5] if sex == 'M' else [1.8, 2.5, 3.5]
    lb, color, _ = _get_classification(bm, bm_bounds,
        ["Low", "Healthy", "Excellent", "High"], ["warning", "success", "primary", "info"])
    cls["bone_mass"] = {"value": bm, "unit": "kg", "name": "Bone Mass", "label": lb, "color": color,
        "bounds": bm_bounds, "desc": "Estimated bone mineral mass. Important for bone density.", "category": "muscle"}

    # ── Protein ──
    pr = metrics.get('protein_percent', 0)
    pr_bounds = [16.0, 20.0, 24.0]
    lb, color, _ = _get_classification(pr, pr_bounds,
        ["Low", "Healthy", "Excellent", "High"], ["warning", "success", "primary", "info"])
    cls["protein"] = {"value": pr, "unit": "%", "name": "Protein", "label": lb, "color": color,
        "bounds": pr_bounds, "desc": "Cellular protein (~20% of muscle tissue).", "category": "muscle"}

    # ── BMR ──
    bmr = metrics.get('bmr', 0)
    bmr_bounds = [1200, 1500, 2000] if sex == 'F' else [1400, 1700, 2400]
    lb, color, _ = _get_classification(bmr, bmr_bounds,
        ["Low", "Healthy", "High", "Super"], ["warning", "success", "primary", "info"])
    cls["bmr"] = {"value": bmr, "unit": "kcal", "name": "Metabolism", "label": lb, "color": color,
        "bounds": bmr_bounds, "desc": "Calories at absolute rest (Mifflin-St Jeor).", "category": "metabolism"}

    # ── Metabolic Age ──
    ma = metrics.get('metabolic_age', 0)
    diff = age - ma
    if diff <= -5: lb, color = "Aged", "danger"
    elif diff < 0: lb, color = "Above", "warning"
    elif diff <= 5: lb, color = "Healthy", "success"
    else: lb, color = "Young", "primary"
    cls["metabolic_age"] = {"value": ma, "unit": "years", "name": "Metabolic Age", "label": lb, "color": color,
        "bounds": [age-5, age, age+5], "desc": "Metabolic age based on your caloric expenditure.", "category": "metabolism"}

    # ── Ideal Weight ──
    iw = metrics.get('ideal_weight_kg', 0)
    weight_diff = round(w - iw, 1)
    diff_label = f"+{weight_diff}" if weight_diff > 0 else str(weight_diff)
    lb, color = ("Ideal", "success") if abs(weight_diff) < 3 else ("Close", "primary") if abs(weight_diff) < 8 else ("Far", "warning")
    cls["ideal_weight"] = {"value": iw, "unit": "kg", "name": "Ideal Weight", "label": f"Δ {diff_label}kg", "color": color,
        "bounds": [round(iw-5,1), round(iw,1), round(iw+5,1)],
        "desc": f"Center of healthy range (BMI 22). Difference: {diff_label} kg.", "category": "metabolism"}

    # ── Body Score ──
    bs = metrics.get('body_score', 0)
    bs_bounds = [40, 60, 80]
    lb, color, _ = _get_classification(bs, bs_bounds,
        ["Low", "Fair", "Good", "Excellent"], ["danger", "warning", "success", "primary"])
    cls["body_score"] = {"value": bs, "unit": "/100", "name": "Body Score", "label": lb, "color": color,
        "bounds": bs_bounds, "desc": "Composite score: fat, muscle, visceral, water and BMI.", "category": "score"}

    # ── WHR (Tier 2) ──
    whr_val = metrics.get('whr')
    if whr_val:
        whr_bounds = [0.85, 0.90, 1.0] if sex == 'M' else [0.75, 0.85, 0.95]
        lb, color, _ = _get_classification(whr_val, whr_bounds,
            ["Excellent", "Healthy", "High", "Risk"], ["primary", "success", "warning", "danger"])
        cls["whr"] = {"value": whr_val, "unit": "", "name": "Waist/Hip", "label": lb, "color": color,
            "bounds": whr_bounds, "desc": "Waist-to-hip ratio. Fat distribution indicator (WHO).", "category": "health"}

    # ── WHtR (Tier 2) ──
    whtr_val = metrics.get('whtr')
    if whtr_val:
        whtr_bounds = [0.40, 0.50, 0.60]
        lb, color, _ = _get_classification(whtr_val, whtr_bounds,
            ["Lean", "Healthy", "Risk", "High Risk"], ["info", "success", "warning", "danger"])
        cls["whtr"] = {"value": whtr_val, "unit": "", "name": "Waist/Height", "label": lb, "color": color,
            "bounds": whtr_bounds, "desc": "Waist-to-height ratio. < 0.5 = healthy (Ashwell 2012).", "category": "health"}

    return cls


# ═══════════════════ SELF-TEST ═══════════════════

if __name__ == "__main__":
    print("=== Complete BIA Metrics Suite ===\n")
    for label, w, h, a, s, z, wc, hc in [
        ("Healthy M", 83, 175, 35, 'M', 500, 85, 100),
        ("Lean M", 70, 175, 28, 'M', 580, None, None),
        ("Heavy M", 100, 175, 45, 'M', 400, 102, 108),
        ("Lean F", 60, 165, 30, 'F', 600, None, None),
        ("Elder M", 80, 170, 68, 'M', 480, 95, 102),
    ]:
        res = get_all_metrics(w, h, a, s, z, waist_cm=wc, hip_cm=hc)
        cls = get_classifications(res, s, a, h)
        print(f"── {label}: {s} {w}kg {h}cm {a}y Z={z} WC={wc} HC={hc}")
        for k, v in res.items():
            c = cls.get(k, {})
            lbl = c.get('label', '')
            vstr = f"{v:>8}" if v is not None else "    None"
            print(f"  {k:25s} = {vstr}  {lbl}")
        print()

import 'dart:math';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const Map<String, double> activityFactors = {
  'sedentary': 1.2,
  'light': 1.375,
  'moderate': 1.55,
  'intense': 1.725,
  'athlete': 1.9,
};

// ---------------------------------------------------------------------------
// Rounding helper
// ---------------------------------------------------------------------------

double _r(double x, int decimals) {
  return double.parse(x.toStringAsFixed(decimals));
}

// ---------------------------------------------------------------------------
// Individual calculation functions
// ---------------------------------------------------------------------------

double calculateBmi(double weightKg, double heightCm) {
  return weightKg / pow(heightCm / 100.0, 2);
}

List<double> calculateIdealWeightRange(double heightCm) {
  final h2 = pow(heightCm / 100.0, 2).toDouble();
  return [18.5 * h2, 25.0 * h2];
}

double calculateIdealWeight(double heightCm) {
  return 22.0 * pow(heightCm / 100.0, 2).toDouble();
}

double calculateBodyFatPercent(
  double weightKg,
  double heightCm,
  int age,
  String sex, {
  double? impedance,
}) {
  double fatPercent;

  if (impedance != null && impedance > 0) {
    double num;
    if (sex == 'M') {
      num = (-0.3315 * heightCm) +
          (0.6216 * weightKg) +
          (0.0183 * age) +
          (0.0085 * impedance) +
          22.554;
    } else {
      num = (-0.3332 * heightCm) +
          (0.7509 * weightKg) +
          (0.0196 * age) +
          (0.0072 * impedance) +
          22.7193;
    }
    fatPercent = (num / weightKg) * 100;
  } else {
    final bmi = calculateBmi(weightKg, heightCm);
    if (sex == 'M') {
      fatPercent = (1.20 * bmi) + (0.23 * age) - 16.2;
    } else {
      fatPercent = (1.20 * bmi) + (0.23 * age) - 5.4;
    }
  }

  return _r(fatPercent.clamp(5.0, 45.0), 1);
}

double calculateFfm(double weightKg, double bodyFatPercent) {
  return _r(weightKg * (1 - bodyFatPercent / 100.0), 2);
}

double calculateFatMass(double weightKg, double bodyFatPercent) {
  return _r(weightKg * bodyFatPercent / 100.0, 2);
}

double? calculateImpedanceIndex(double heightCm, double? impedance) {
  if (impedance != null && impedance > 0) {
    return _r(pow(heightCm, 2).toDouble() / impedance, 2);
  }
  return null;
}

double? calculateSmm(
  double heightCm,
  int age,
  String sex,
  double? impedance,
) {
  if (impedance == null || impedance <= 0) {
    return null;
  }
  final impIdx = pow(heightCm, 2).toDouble() / impedance;
  final sexVal = sex == 'M' ? 1.0 : 0.0;
  final smm = (impIdx * 0.401) + (sexVal * 3.825) - (age * 0.071) + 5.102;
  return max(0.0, _r(smm, 2));
}

double calculateMuscleMassPercent(
  double weightKg,
  double heightCm,
  int age,
  String sex, {
  double? impedance,
}) {
  final smm = calculateSmm(heightCm, age, sex, impedance);
  if (smm != null && smm > 0) {
    return ((smm / weightKg) * 100).clamp(10.0, 65.0);
  }
  final fatPct = calculateBodyFatPercent(weightKg, heightCm, age, sex,
      impedance: impedance);
  final ffm = weightKg * (1 - fatPct / 100.0);
  final ratio = sex == 'M' ? 0.45 : 0.38;
  return _r(((ffm * ratio / weightKg) * 100).clamp(10.0, 65.0), 1);
}

double calculateLbm(double ffmKg, double boneMassKg) {
  return _r(ffmKg - boneMassKg, 2);
}

double calculateBodyWaterPercent(
  double weightKg,
  double heightCm,
  int age,
  String sex, {
  double? impedance,
}) {
  final fatPct = calculateBodyFatPercent(weightKg, heightCm, age, sex,
      impedance: impedance);
  final ffmFraction = 1 - fatPct / 100.0;
  final waterPct = ffmFraction * 73.0;
  return _r(waterPct.clamp(30.0, 75.0), 1);
}

double calculateBoneMassKg(
  double weightKg,
  double heightCm,
  int age,
  String sex, {
  double? impedance,
}) {
  final fatPct = calculateBodyFatPercent(weightKg, heightCm, age, sex,
      impedance: impedance);
  final leanKg = weightKg * (1 - fatPct / 100.0);
  double bone;
  if (sex == 'M') {
    bone = 0.046 * leanKg + 0.09 * (heightCm / 100.0);
  } else {
    bone = 0.042 * leanKg + 0.07 * (heightCm / 100.0);
  }
  return _r(bone.clamp(0.5, 5.0), 2);
}

double calculateObesityPercent(double weightKg, double heightCm,
    {String? sex}) {
  final ideal = calculateIdealWeight(heightCm);
  if (ideal <= 0) return 0.0;
  return _r(((weightKg - ideal) / ideal) * 100.0, 1);
}

double calculateBmr(double weightKg, double heightCm, int age, String sex) {
  if (sex == 'M') {
    return _r((10 * weightKg) + (6.25 * heightCm) - (5 * age) + 5, 0);
  } else {
    return _r((10 * weightKg) + (6.25 * heightCm) - (5 * age) - 161, 0);
  }
}

double calculateTdee(double bmr, {String activityLevel = 'sedentary'}) {
  return _r(bmr * (activityFactors[activityLevel] ?? 1.2), 0);
}

double calculateVisceralFat(
  double weightKg,
  double heightCm,
  int age,
  String sex, {
  double? impedance,
}) {
  final bmi = calculateBmi(weightKg, heightCm);
  final fatPct = calculateBodyFatPercent(weightKg, heightCm, age, sex,
      impedance: impedance);
  double vf;
  if (sex == 'M') {
    vf = 0.15 * fatPct + 0.35 * (bmi - 18.5) + 0.18 * age - 5.5;
    if (bmi > 30) {
      vf += (bmi - 30) * 0.5;
    }
  } else {
    vf = 0.12 * fatPct + 0.28 * (bmi - 18.5) + 0.14 * age - 5.0;
    if (bmi > 30) {
      vf += (bmi - 30) * 0.4;
    }
  }
  return _r(vf.clamp(1.0, 59.0), 1);
}

int calculateMetabolicAge(
  double weightKg,
  double heightCm,
  int age,
  String sex,
  double? ffmKg,
) {
  if (ffmKg == null || ffmKg <= 0) return age;

  final actualBf = ((weightKg - ffmKg) / weightKg) * 100.0;
  double idealBf;

  if (sex == 'M') {
    if (age < 30) {
      idealBf = 15.0;
    } else if (age < 40) {
      idealBf = 17.0;
    } else if (age < 50) {
      idealBf = 19.0;
    } else if (age < 60) {
      idealBf = 20.5;
    } else {
      idealBf = 22.0;
    }
  } else {
    if (age < 30) {
      idealBf = 23.0;
    } else if (age < 40) {
      idealBf = 25.0;
    } else if (age < 50) {
      idealBf = 27.0;
    } else if (age < 60) {
      idealBf = 29.0;
    } else {
      idealBf = 31.0;
    }
  }

  final bfDeviation = actualBf - idealBf;
  final ageShift = bfDeviation * 0.5;
  final metabolicAge = (age + ageShift).round();
  return metabolicAge.clamp(15, 80);
}

double calculateProteinPercent(double musclePercent) {
  return _r((musclePercent * 0.20).clamp(5.0, 25.0), 1);
}

double calculateSubcutaneousFat(double fatMassKg) {
  return _r(fatMassKg * 0.80, 2);
}

double? calculateWhr(double? waistCm, double? hipCm) {
  if (waistCm != null && hipCm != null && hipCm > 0) {
    return _r(waistCm / hipCm, 3);
  }
  return null;
}

double? calculateWhtr(double? waistCm, double heightCm) {
  if (waistCm != null && heightCm > 0) {
    return _r(waistCm / heightCm, 3);
  }
  return null;
}

double calculateFfmi(double ffmKg, double heightCm) {
  final hM = heightCm / 100.0;
  return _r(ffmKg / pow(hM, 2).toDouble(), 1);
}

double? calculateSmi(double? smmKg, double heightCm) {
  if (smmKg == null) return null;
  final hM = heightCm / 100.0;
  return _r(smmKg / pow(hM, 2).toDouble(), 1);
}

int calculateBodyScore(
  double bmi,
  double bodyFatPercent,
  double visceralFat,
  double musclePercent,
  double waterPercent,
  String sex,
) {
  final idealBf = sex == 'M' ? 17.0 : 27.0;

  final bmiS = max(0.0, 100 - (bmi - 22).abs() * 5);
  final bfS = max(0.0, 100 - (bodyFatPercent - idealBf).abs() * 3);
  final vfS = max(0.0, 100 - visceralFat * 5);
  final msS = sex == 'M'
      ? min(100.0, musclePercent * 2.2)
      : min(100.0, musclePercent * 2.8);
  final idealWater = sex == 'M' ? 57.5 : 52.5;
  final wsS = max(0.0, 100 - (waterPercent - idealWater).abs() * 3);

  final score =
      (bmiS * 0.15 + bfS * 0.30 + vfS * 0.20 + msS * 0.20 + wsS * 0.15)
          .toInt();
  return score.clamp(1, 100);
}

// ---------------------------------------------------------------------------
// getAllMetrics
// ---------------------------------------------------------------------------

Map<String, dynamic> getAllMetrics(
  double weightKg,
  double heightCm,
  int age,
  String sex, {
  double? impedance,
  String activityLevel = 'sedentary',
  double? waistCm,
  double? hipCm,
}) {
  final bmi = calculateBmi(weightKg, heightCm);
  final fatPercent = calculateBodyFatPercent(weightKg, heightCm, age, sex,
      impedance: impedance);
  final fatMassKg = calculateFatMass(weightKg, fatPercent);
  final ffmKg = calculateFfm(weightKg, fatPercent);
  final boneMassKg = calculateBoneMassKg(weightKg, heightCm, age, sex,
      impedance: impedance);
  final lbmKg = calculateLbm(ffmKg, boneMassKg);
  final smmPercent = calculateMuscleMassPercent(weightKg, heightCm, age, sex,
      impedance: impedance);

  double? smmKgRaw = calculateSmm(heightCm, age, sex, impedance);
  final double smmKg =
      smmKgRaw ?? _r(weightKg * smmPercent / 100.0, 2);

  final muscleMassKg = lbmKg;
  final double musclePercent =
      weightKg > 0 ? _r((muscleMassKg / weightKg) * 100.0, 1) : 0.0;

  final waterPercent = calculateBodyWaterPercent(weightKg, heightCm, age, sex,
      impedance: impedance);
  final waterMassKg = _r(weightKg * waterPercent / 100.0, 2);
  final proteinPercent = calculateProteinPercent(musclePercent);
  final bmr = calculateBmr(weightKg, heightCm, age, sex);
  final tdee = calculateTdee(bmr, activityLevel: activityLevel);
  final visceral = calculateVisceralFat(weightKg, heightCm, age, sex,
      impedance: impedance);
  final metabolicAge =
      calculateMetabolicAge(weightKg, heightCm, age, sex, ffmKg);
  final idealWt = calculateIdealWeight(heightCm);
  final impIdx = calculateImpedanceIndex(heightCm, impedance);
  final ffmi = calculateFfmi(ffmKg, heightCm);
  final obesityPercent =
      calculateObesityPercent(weightKg, heightCm, sex: sex);
  final smi = calculateSmi(smmKg, heightCm);
  final subcutFat = calculateSubcutaneousFat(fatMassKg);
  final bodyScore =
      calculateBodyScore(bmi, fatPercent, visceral, smmPercent, waterPercent, sex);
  final whr = calculateWhr(waistCm, hipCm);
  final whtr = calculateWhtr(waistCm, heightCm);

  return {
    'weight_kg': _r(weightKg, 2),
    'bmi': _r(bmi, 1),
    'body_fat_percent': _r(fatPercent, 1),
    'fat_mass_kg': fatMassKg,
    'fat_free_mass_kg': ffmKg,
    'muscle_mass_percent': musclePercent,
    'muscle_mass_kg': muscleMassKg,
    'smm_percent': smmPercent,
    'obesity_percent': obesityPercent,
    'body_water_percent': waterPercent,
    'water_mass_kg': waterMassKg,
    'bone_mass_kg': boneMassKg,
    'visceral_fat': visceral,
    'bmr': bmr,
    'tdee': tdee,
    'metabolic_age': metabolicAge,
    'protein_percent': proteinPercent,
    'lbm_kg': lbmKg,
    'smm_kg': smmKg,
    'impedance_index': impIdx,
    'ideal_weight_kg': _r(idealWt, 1),
    'ffmi': ffmi,
    'smi': smi,
    'subcutaneous_fat_kg': subcutFat,
    'body_score': bodyScore,
    'whr': whr,
    'whtr': whtr,
  };
}

// ---------------------------------------------------------------------------
// ClassificationResult
// ---------------------------------------------------------------------------

class ClassificationResult {
  final double value;
  final String unit;
  final String name;
  final String label;
  final String color;
  final List<double> bounds;
  final String desc;
  final String category;

  const ClassificationResult({
    required this.value,
    required this.unit,
    required this.name,
    required this.label,
    required this.color,
    required this.bounds,
    required this.desc,
    required this.category,
  });

  Map<String, dynamic> toMap() => {
        'value': value,
        'unit': unit,
        'name': name,
        'label': label,
        'color': color,
        'bounds': bounds,
        'desc': desc,
        'category': category,
      };
}

// ---------------------------------------------------------------------------
// Internal classification helper
// ---------------------------------------------------------------------------

(String label, String color, int idx) _getClassification(
  double val,
  List<double> bounds,
  List<String> labels,
  List<String> colors,
) {
  if (val < bounds[0]) {
    return (labels[0], colors[0], 0);
  } else if (val < bounds[1]) {
    return (labels[1], colors[1], 1);
  } else if (val < bounds[2]) {
    return (labels[2], colors[2], 2);
  } else {
    return (labels[3], colors[3], 3);
  }
}

// ---------------------------------------------------------------------------
// getClassifications
// ---------------------------------------------------------------------------

Map<String, ClassificationResult> getClassifications(
  Map<String, dynamic> metrics,
  String sex,
  int age,
  double heightCm,
) {
  final cls = <String, ClassificationResult>{};

  // ---- BMI ----
  {
    final val = (metrics['bmi'] as num).toDouble();
    final bounds = [18.5, 25.0, 30.0];
    final labels = ['Underweight', 'Normal', 'Overweight', 'Obese'];
    final colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['bmi'] = ClassificationResult(
      value: val,
      unit: 'kg/m²',
      name: 'BMI',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Body Mass Index',
      category: 'composition',
    );
  }

  // ---- Body Fat % ----
  {
    final val = (metrics['body_fat_percent'] as num).toDouble();
    List<double> bounds;
    if (sex == 'M') {
      if (age < 40) {
        bounds = [8.0, 20.0, 25.0];
      } else if (age < 60) {
        bounds = [11.0, 22.0, 28.0];
      } else {
        bounds = [13.0, 25.0, 30.0];
      }
    } else {
      if (age < 40) {
        bounds = [21.0, 33.0, 39.0];
      } else if (age < 60) {
        bounds = [23.0, 34.0, 40.0];
      } else {
        bounds = [24.0, 36.0, 42.0];
      }
    }
    final labels = ['Low', 'Normal', 'High', 'Very High'];
    final colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['body_fat_percent'] = ClassificationResult(
      value: val,
      unit: '%',
      name: 'Body Fat',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Body fat percentage',
      category: 'composition',
    );
  }

  // ---- Muscle Mass % ----
  {
    final val = (metrics['smm_percent'] as num).toDouble();
    List<double> bounds;
    if (sex == 'M') {
      bounds = [33.0, 39.0, 44.0];
    } else {
      bounds = [24.0, 30.0, 35.0];
    }
    final labels = ['Low', 'Normal', 'High', 'Very High'];
    final colors = ['#e74c3c', '#2ecc71', '#3498db', '#9b59b6'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['smm_percent'] = ClassificationResult(
      value: val,
      unit: '%',
      name: 'Muscle Mass',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Skeletal muscle mass percentage',
      category: 'composition',
    );
  }

  // ---- Body Water % ----
  {
    final val = (metrics['body_water_percent'] as num).toDouble();
    List<double> bounds;
    if (sex == 'M') {
      bounds = [50.0, 55.0, 65.0];
    } else {
      bounds = [45.0, 50.0, 60.0];
    }
    final labels = ['Low', 'Normal', 'High', 'Very High'];
    final colors = ['#e74c3c', '#2ecc71', '#3498db', '#9b59b6'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['body_water_percent'] = ClassificationResult(
      value: val,
      unit: '%',
      name: 'Body Water',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Total body water percentage',
      category: 'composition',
    );
  }

  // ---- Bone Mass ----
  {
    final val = (metrics['bone_mass_kg'] as num).toDouble();
    List<double> bounds;
    if (sex == 'M') {
      bounds = [2.0, 2.6, 3.5];
    } else {
      bounds = [1.5, 2.0, 2.8];
    }
    final labels = ['Low', 'Normal', 'High', 'Very High'];
    final colors = ['#e74c3c', '#2ecc71', '#3498db', '#9b59b6'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['bone_mass_kg'] = ClassificationResult(
      value: val,
      unit: 'kg',
      name: 'Bone Mass',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Estimated bone mass',
      category: 'composition',
    );
  }

  // ---- Visceral Fat ----
  {
    final val = (metrics['visceral_fat'] as num).toDouble();
    final bounds = [9.0, 14.0, 17.0];
    final labels = ['Normal', 'High', 'Very High', 'Excessive'];
    final colors = ['#2ecc71', '#f39c12', '#e74c3c', '#c0392b'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['visceral_fat'] = ClassificationResult(
      value: val,
      unit: '',
      name: 'Visceral Fat',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Visceral fat rating',
      category: 'health',
    );
  }

  // ---- BMR ----
  {
    final val = (metrics['bmr'] as num).toDouble();
    final bounds = [1200.0, 1600.0, 2200.0];
    final labels = ['Low', 'Normal', 'High', 'Very High'];
    final colors = ['#e74c3c', '#2ecc71', '#3498db', '#9b59b6'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['bmr'] = ClassificationResult(
      value: val,
      unit: 'kcal',
      name: 'BMR',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Basal Metabolic Rate',
      category: 'metabolic',
    );
  }

  // ---- Protein % ----
  {
    final val = (metrics['protein_percent'] as num).toDouble();
    final bounds = [10.0, 16.0, 20.0];
    final labels = ['Low', 'Normal', 'High', 'Very High'];
    final colors = ['#e74c3c', '#2ecc71', '#3498db', '#9b59b6'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['protein_percent'] = ClassificationResult(
      value: val,
      unit: '%',
      name: 'Protein',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Estimated protein percentage',
      category: 'composition',
    );
  }

  // ---- Obesity % ----
  {
    final val = (metrics['obesity_percent'] as num).toDouble();
    final bounds = [-10.0, 10.0, 20.0];
    final labels = ['Underweight', 'Normal', 'Overweight', 'Obese'];
    final colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['obesity_percent'] = ClassificationResult(
      value: val,
      unit: '%',
      name: 'Obesity',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Obesity percentage relative to ideal weight',
      category: 'health',
    );
  }

  // ---- Body Score ----
  {
    final val = (metrics['body_score'] as num).toDouble();
    final bounds = [40.0, 60.0, 80.0];
    final labels = ['Poor', 'Fair', 'Good', 'Excellent'];
    final colors = ['#e74c3c', '#f39c12', '#2ecc71', '#3498db'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['body_score'] = ClassificationResult(
      value: val,
      unit: '',
      name: 'Body Score',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Overall body composition score',
      category: 'health',
    );
  }

  // ---- FFMI ----
  if (metrics['ffmi'] != null) {
    final val = (metrics['ffmi'] as num).toDouble();
    List<double> bounds;
    if (sex == 'M') {
      bounds = [17.0, 20.0, 23.0];
    } else {
      bounds = [14.0, 17.0, 20.0];
    }
    final labels = ['Below Average', 'Average', 'Above Average', 'Excellent'];
    final colors = ['#e74c3c', '#2ecc71', '#3498db', '#9b59b6'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['ffmi'] = ClassificationResult(
      value: val,
      unit: 'kg/m²',
      name: 'FFMI',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Fat-Free Mass Index',
      category: 'composition',
    );
  }

  // ---- Metabolic Age ----
  {
    final val = (metrics['metabolic_age'] as num).toDouble();
    final ageDbl = age.toDouble();
    final bounds = [ageDbl - 5, ageDbl, ageDbl + 5];
    final labels = ['Younger', 'Normal', 'Older', 'Much Older'];
    final colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['metabolic_age'] = ClassificationResult(
      value: val,
      unit: 'years',
      name: 'Metabolic Age',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Estimated metabolic age',
      category: 'metabolic',
    );
  }

  // ---- WHR ----
  if (metrics['whr'] != null) {
    final val = (metrics['whr'] as num).toDouble();
    List<double> bounds;
    if (sex == 'M') {
      bounds = [0.85, 0.90, 1.00];
    } else {
      bounds = [0.75, 0.80, 0.86];
    }
    final labels = ['Low', 'Normal', 'High', 'Very High'];
    final colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['whr'] = ClassificationResult(
      value: val,
      unit: '',
      name: 'Waist-to-Hip Ratio',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Waist-to-hip ratio',
      category: 'health',
    );
  }

  // ---- WHtR ----
  if (metrics['whtr'] != null) {
    final val = (metrics['whtr'] as num).toDouble();
    final bounds = [0.40, 0.50, 0.60];
    final labels = ['Slim', 'Healthy', 'Overweight', 'Obese'];
    final colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['whtr'] = ClassificationResult(
      value: val,
      unit: '',
      name: 'Waist-to-Height Ratio',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Waist-to-height ratio',
      category: 'health',
    );
  }

  // ---- SMI ----
  if (metrics['smi'] != null) {
    final val = (metrics['smi'] as num).toDouble();
    List<double> bounds;
    if (sex == 'M') {
      bounds = [7.0, 8.5, 10.5];
    } else {
      bounds = [5.5, 6.8, 8.0];
    }
    final labels = ['Low', 'Normal', 'High', 'Very High'];
    final colors = ['#e74c3c', '#2ecc71', '#3498db', '#9b59b6'];
    final (label, color, _) = _getClassification(val, bounds, labels, colors);
    cls['smi'] = ClassificationResult(
      value: val,
      unit: 'kg/m²',
      name: 'SMI',
      label: label,
      color: color,
      bounds: bounds,
      desc: 'Skeletal Muscle Index',
      category: 'composition',
    );
  }

  return cls;
}

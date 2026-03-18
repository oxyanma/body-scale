import pytest
from calculations.body_composition import get_all_metrics, calculate_bmi, get_classifications

def test_bmi():
    # 80kg, 1.75m -> 80 / (1.75^2) = 26.122
    bmi = calculate_bmi(80, 175)
    assert abs(bmi - 26.12) < 0.01

def test_all_metrics_without_impedance():
    # Homem, 80kg, 175cm, 35 anos
    metrics = get_all_metrics(80, 175, 35, 'M', impedance=None)
    
    assert metrics["weight_kg"] == 80.0
    assert metrics["bmi"] == 26.1
    # BMR Homem = (10 * 80) + (6.25 * 175) - (5 * 35) + 5 = 800 + 1093.75 - 175 + 5 = 1723.75
    assert metrics["bmr"] == 1724
    
def test_all_metrics_with_impedance():
    metrics = get_all_metrics(80, 175, 35, 'M', impedance=500)
    
    assert "body_fat_percent" in metrics
    assert "muscle_mass_percent" in metrics
    assert "bone_mass_kg" in metrics
    assert metrics["visceral_fat"] > 0
    
def test_classifications():
    metrics = get_all_metrics(80, 175, 35, 'M', impedance=500)
    classes = get_classifications(metrics, 'M', 35)
    assert classes["bmi"]["label"] == "Sobrepeso"

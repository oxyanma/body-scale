import 'package:flutter_test/flutter_test.dart';
import 'package:bioscale_mobile/calculations/body_composition.dart';

void main() {
  group('Body Composition Calculations', () {
    test('BMI calculation', () {
      final bmi = calculateBmi(83, 175);
      expect(bmi, closeTo(27.1, 0.1));
    });

    test('Ideal weight', () {
      final ideal = calculateIdealWeight(175);
      expect(ideal, closeTo(67.4, 0.1));
    });

    test('Body fat percent with impedance (male)', () {
      final bf = calculateBodyFatPercent(83, 175, 35, 'M', impedance: 500);
      expect(bf, greaterThan(5));
      expect(bf, lessThan(45));
    });

    test('Body fat percent without impedance (female)', () {
      final bf = calculateBodyFatPercent(60, 165, 30, 'F');
      expect(bf, greaterThan(5));
      expect(bf, lessThan(45));
    });

    test('getAllMetrics returns all keys', () {
      final metrics = getAllMetrics(83, 175, 35, 'M', impedance: 500);
      expect(metrics.containsKey('bmi'), isTrue);
      expect(metrics.containsKey('body_fat_percent'), isTrue);
      expect(metrics.containsKey('muscle_mass_kg'), isTrue);
      expect(metrics.containsKey('body_score'), isTrue);
    });

    test('getClassifications returns results', () {
      final metrics = getAllMetrics(83, 175, 35, 'M', impedance: 500);
      final cls = getClassifications(metrics, 'M', 35, 175);
      expect(cls.containsKey('bmi'), isTrue);
      expect(cls['bmi']!.value, closeTo(27.1, 0.1));
    });
  });
}

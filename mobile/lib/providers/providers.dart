import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/ble_service.dart';
import '../database/database_helper.dart';
import '../services/i18n_service.dart';

// BLE
final bleServiceProvider = Provider((ref) => BleService());
final bleStateProvider = StreamProvider<BleState>((ref) {
  return ref.watch(bleServiceProvider).stateStream;
});

// Database
final databaseProvider = Provider((ref) => DatabaseHelper.instance);

// Active user
final activeUserProvider = FutureProvider<Map<String, dynamic>?>((ref) async {
  final db = ref.watch(databaseProvider);
  return await db.getActiveUser();
});

// Measurements
final measurementsProvider =
    FutureProvider.family<List<Map<String, dynamic>>, int>(
        (ref, userId) async {
  final db = ref.watch(databaseProvider);
  return await db.getMeasurements(userId);
});

// Language
final languageProvider =
    StateProvider<String>((ref) => I18nService.currentLanguage);

import 'dart:async';

import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

/// Singleton helper for the local SQLite database.
///
/// Tables mirror the Python SQLAlchemy models used by the BioScale backend.
class DatabaseHelper {
  DatabaseHelper._init();

  static final DatabaseHelper instance = DatabaseHelper._init();

  static Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('bioscale.db');
    return _database!;
  }

  // ── Initialization ─────────────────────────────────────────────────────

  Future<Database> _initDB(String fileName) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, fileName);
    return openDatabase(
      path,
      version: 1,
      onCreate: _createDB,
    );
  }

  Future<void> _createDB(Database db, int version) async {
    await db.execute('''
      CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sex TEXT NOT NULL,
        age INTEGER NOT NULL,
        height_cm REAL NOT NULL,
        waist_cm REAL,
        hip_cm REAL,
        activity_level TEXT NOT NULL DEFAULT 'moderate',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        is_active INTEGER NOT NULL DEFAULT 1,
        language TEXT NOT NULL DEFAULT 'en'
      )
    ''');

    await db.execute('''
      CREATE TABLE ble_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac_address TEXT NOT NULL,
        name TEXT,
        protocol_version TEXT,
        last_seen TEXT,
        is_preferred INTEGER NOT NULL DEFAULT 0
      )
    ''');

    await db.execute('''
      CREATE TABLE measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        device_id INTEGER,
        measured_at TEXT NOT NULL DEFAULT (datetime('now')),
        weight_kg REAL NOT NULL,
        impedance INTEGER,
        bmi REAL,
        body_fat_percent REAL,
        muscle_mass_percent REAL,
        body_water_percent REAL,
        bone_mass_kg REAL,
        visceral_fat REAL,
        bmr REAL,
        tdee REAL,
        metabolic_age INTEGER,
        protein_percent REAL,
        fat_free_mass_kg REAL,
        smm_kg REAL,
        lbm_kg REAL,
        impedance_index REAL,
        body_score INTEGER,
        ideal_weight_kg REAL,
        ffmi REAL,
        smi REAL,
        subcutaneous_fat_kg REAL,
        whr REAL,
        whtr REAL,
        notes TEXT,
        raw_data_hex TEXT,
        source TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (device_id) REFERENCES ble_devices (id) ON DELETE SET NULL
      )
    ''');

    await db.execute('''
      CREATE TABLE goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        metric TEXT NOT NULL,
        target_value REAL NOT NULL,
        target_date TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        achieved_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
      )
    ''');

    await db.execute('''
      CREATE TABLE fasting_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        protocol TEXT NOT NULL,
        started_at TEXT NOT NULL,
        ended_at TEXT,
        target_hours REAL NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
      )
    ''');

    // Indexes for common queries
    await db.execute(
        'CREATE INDEX idx_measurements_user ON measurements (user_id)');
    await db.execute(
        'CREATE INDEX idx_measurements_date ON measurements (measured_at)');
    await db.execute('CREATE INDEX idx_goals_user ON goals (user_id)');
    await db.execute(
        'CREATE INDEX idx_fasting_user ON fasting_sessions (user_id)');
  }

  // ── User CRUD ──────────────────────────────────────────────────────────

  Future<int> insertUser(Map<String, dynamic> user) async {
    final db = await database;
    return db.insert('users', user);
  }

  Future<List<Map<String, dynamic>>> getUsers() async {
    final db = await database;
    return db.query('users', orderBy: 'name ASC');
  }

  Future<Map<String, dynamic>?> getActiveUser() async {
    final db = await database;
    final results = await db.query(
      'users',
      where: 'is_active = ?',
      whereArgs: [1],
      limit: 1,
    );
    return results.isNotEmpty ? results.first : null;
  }

  Future<void> setActiveUser(int userId) async {
    final db = await database;
    await db.transaction((txn) async {
      // Deactivate all users
      await txn.update('users', {'is_active': 0});
      // Activate the chosen user
      await txn.update(
        'users',
        {'is_active': 1, 'updated_at': DateTime.now().toIso8601String()},
        where: 'id = ?',
        whereArgs: [userId],
      );
    });
  }

  Future<void> updateUser(int id, Map<String, dynamic> data) async {
    final db = await database;
    data['updated_at'] = DateTime.now().toIso8601String();
    await db.update('users', data, where: 'id = ?', whereArgs: [id]);
  }

  // ── Measurement CRUD ───────────────────────────────────────────────────

  Future<int> insertMeasurement(Map<String, dynamic> m) async {
    final db = await database;
    return db.insert('measurements', m);
  }

  Future<List<Map<String, dynamic>>> getMeasurements(
    int userId, {
    int limit = 100,
  }) async {
    final db = await database;
    return db.query(
      'measurements',
      where: 'user_id = ?',
      whereArgs: [userId],
      orderBy: 'measured_at DESC',
      limit: limit,
    );
  }

  Future<Map<String, dynamic>?> getMeasurement(int id) async {
    final db = await database;
    final results = await db.query(
      'measurements',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    return results.isNotEmpty ? results.first : null;
  }

  Future<void> deleteMeasurement(int id) async {
    final db = await database;
    await db.delete('measurements', where: 'id = ?', whereArgs: [id]);
  }

  // ── Goal CRUD ──────────────────────────────────────────────────────────

  Future<int> insertGoal(Map<String, dynamic> goal) async {
    final db = await database;
    return db.insert('goals', goal);
  }

  Future<List<Map<String, dynamic>>> getGoals(int userId) async {
    final db = await database;
    return db.query(
      'goals',
      where: 'user_id = ?',
      whereArgs: [userId],
      orderBy: 'created_at DESC',
    );
  }

  Future<void> updateGoal(int id, Map<String, dynamic> data) async {
    final db = await database;
    await db.update('goals', data, where: 'id = ?', whereArgs: [id]);
  }

  Future<void> deleteGoal(int id) async {
    final db = await database;
    await db.delete('goals', where: 'id = ?', whereArgs: [id]);
  }

  // ── Export & Cleanup ───────────────────────────────────────────────────

  /// Export all measurements for a user as a CSV string.
  Future<String> exportCsv(int userId) async {
    final db = await database;
    final rows = await db.query(
      'measurements',
      where: 'user_id = ?',
      whereArgs: [userId],
      orderBy: 'measured_at ASC',
    );

    if (rows.isEmpty) return '';

    final header = rows.first.keys.join(',');
    final lines = <String>[header];
    for (final row in rows) {
      final values = row.values.map((v) {
        if (v == null) return '';
        final s = v.toString();
        // Escape values that contain commas or quotes
        if (s.contains(',') || s.contains('"')) {
          return '"${s.replaceAll('"', '""')}"';
        }
        return s;
      }).join(',');
      lines.add(values);
    }
    return lines.join('\n');
  }

  /// Delete all measurements for a user.
  Future<void> clearHistory(int userId) async {
    final db = await database;
    await db.delete(
      'measurements',
      where: 'user_id = ?',
      whereArgs: [userId],
    );
  }

  /// Drop and recreate all tables (factory reset).
  Future<void> deleteAllData() async {
    final db = await database;
    await db.transaction((txn) async {
      await txn.delete('fasting_sessions');
      await txn.delete('goals');
      await txn.delete('measurements');
      await txn.delete('ble_devices');
      await txn.delete('users');
    });
  }

  /// Close the database connection.
  Future<void> close() async {
    final db = await database;
    await db.close();
    _database = null;
  }
}

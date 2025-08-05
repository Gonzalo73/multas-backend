// db.js
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Ruta al archivo de la base de datos
const dbPath = path.resolve(__dirname, '../db/database.sqlite');
const db = new sqlite3.Database(dbPath);

// Crear tablas si no existen
db.serialize(() => {
  db.run(`
    CREATE TABLE IF NOT EXISTS patentes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      patente TEXT UNIQUE NOT NULL,
      fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS multas (
      acta TEXT UNIQUE NOT NULL,
      patente TEXT NOT NULL,
      descripcion TEXT,
      fecha TEXT,
      lugar TEXT,
      imagen_url TEXT,
      velocidad REAL,
      latitud REAL,
      longitud REAL
    )
  `);
});

module.exports = db;

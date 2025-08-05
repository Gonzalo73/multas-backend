const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.resolve(__dirname, './multas.db'); // Asegurate que apunte al lugar correcto
const db = new sqlite3.Database(dbPath);

// Verificamos que existan las tablas
db.serialize(() => {
  db.all("SELECT name FROM sqlite_master WHERE type='table'", (err, rows) => {
    if (err) {
      console.error("Error al obtener tablas:", err);
    } else {
      console.log("Tablas encontradas:");
      rows.forEach(row => console.log("- " + row.name));
    }
  });

  // Verificamos que patentes exista y esté vacía (o no)
  db.all("SELECT * FROM patentes", (err, rows) => {
    if (err) {
      console.error("Error consultando 'patentes':", err.message);
    } else {
      console.log("Contenido de la tabla 'patentes':");
      console.log(rows);
    }
  });
});

db.close();

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

const app = express();

// Usamos la carpeta persistente de Render
const DB_DIR = '/var/data';
const DB_PATH = path.join(DB_DIR, 'multas.db');

// Si la base no existe, la creamos vacía
if (!fs.existsSync(DB_DIR)) {
  fs.mkdirSync(DB_DIR, { recursive: true });
}

const db = new sqlite3.Database(DB_PATH, (err) => {
  if (err) {
    console.error('❌ Error al conectar con la base de datos:', err.message);
  } else {
    console.log(`✅ Conectado a base de datos en ${DB_PATH}`);
  }
});

// Crear tablas si no existen
db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS patentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    patente TEXT UNIQUE
  )`);

  db.run(`CREATE TABLE IF NOT EXISTS multas (
    id_multa TEXT PRIMARY KEY,
    patente TEXT,
    descripcion TEXT,
    fecha TEXT,
    lat REAL,
    lng REAL,
    imagen TEXT
  )`);

  console.log('📦 Tablas creadas/verificadas');
});

// Middlewares
app.use(cors());
app.use(bodyParser.json());

// Ruta base
app.get('/', (req, res) => {
  res.send('🚦 Backend de Multas está funcionando');
});

// Health check
app.get('/ping', (req, res) => {
  res.send('pong');
});

// Registrar patente
app.post('/api/patentes', (req, res) => {
  const { patente, email } = req.body;
  if (!patente) return res.status(400).json({ error: 'La patente es requerida' });

  db.run(
    'INSERT OR IGNORE INTO patentes (patente, email) VALUES (?, ?)',
    [patente, email || null],
    function (err) {
      if (err) {
        console.error('Error al registrar patente:', err.message);
        return res.status(500).json({ error: 'Error al registrar patente' });
      }
      res.status(201).json({ success: true });
    }
  );
});

// Eliminar patente
app.delete('/api/patentes/:patente', (req, res) => {
  const { patente } = req.params;

  db.run('DELETE FROM patentes WHERE patente = ?', [patente], function (err) {
    if (err) {
      console.error('Error al eliminar patente:', err.message);
      return res.status(500).json({ error: 'Error al eliminar patente' });
    }
    res.status(200).json({ success: true });
  });
});

// Obtener todas las patentes
app.get('/api/patentes', (req, res) => {
  db.all('SELECT patente, email FROM patentes', [], (err, rows) => {
    if (err) {
      console.error('Error al obtener patentes:', err.message);
      return res.status(500).json({ error: 'Error al obtener patentes' });
    }
    res.json(rows);
  });
});

// Obtener multas de una patente
app.get('/api/multas/:patente', (req, res) => {
  const { patente } = req.params;

  db.all('SELECT * FROM multas WHERE patente = ?', [patente], (err, rows) => {
    if (err) {
      console.error('Error al obtener multas:', err.message);
      return res.status(500).json({ error: 'Error al obtener multas' });
    }
    res.json(rows);
  });
});

// Servir imágenes de evidencia
app.get('/evidencias/:filename', (req, res) => {
  const { filename } = req.params;
  const imagePath = path.join(__dirname, 'evidencias', filename);

  if (fs.existsSync(imagePath)) {
    res.sendFile(imagePath);
  } else {
    res.status(404).json({ error: 'Imagen no encontrada' });
  }
});

// Iniciar servidor
const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`🚀 Servidor escuchando en el puerto ${port}`);
});

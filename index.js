// index.js

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

const app = express();
const db = new sqlite3.Database('./multas.db');

// Middlewares
app.use(cors());
app.use(bodyParser.json());

// Ruta base para verificar que el servicio funciona
app.get('/', (req, res) => {
  res.send('🚦 Backend de Multas está funcionando');
});

// Ruta /ping para health check
app.get('/ping', (req, res) => {
  res.send('pong');
});

// Ruta para registrar una nueva patente
app.post('/api/patentes', (req, res) => {
  const { patente } = req.body;
  if (!patente) {
    return res.status(400).json({ error: 'La patente es requerida' });
  }

  db.run('INSERT OR IGNORE INTO patentes (patente) VALUES (?)', [patente], function (err) {
    if (err) {
      console.error('Error al registrar patente:', err.message);
      return res.status(500).json({ error: 'Error al registrar patente' });
    }
    res.status(201).json({ success: true });
  });
});

// Ruta para eliminar una patente
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

// Ruta para obtener todas las patentes
app.get('/api/patentes', (req, res) => {
  db.all('SELECT patente FROM patentes', [], (err, rows) => {
    if (err) {
      console.error('Error al obtener patentes:', err.message);
      return res.status(500).json({ error: 'Error al obtener patentes' });
    }
    res.json(rows);
  });
});

// Ruta para obtener multas de una patente
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

// Ruta para servir imágenes de evidencias
app.get('/evidencias/:filename', (req, res) => {
  const { filename } = req.params;
  const imagePath = path.join(__dirname, 'evidencias', filename);

  if (fs.existsSync(imagePath)) {
    res.sendFile(imagePath);
  } else {
    res.status(404).json({ error: 'Imagen no encontrada' });
  }
});

// Iniciar servidor en Render (usa process.env.PORT o 3000 por defecto en local)
const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Servidor escuchando en el puerto ${port}`);
});

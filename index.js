const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

// Middleware opcional
app.use(express.json());

// Ruta de prueba
app.get('/ping', (req, res) => {
  res.send('pong');
});

// Ruta de ejemplo
app.get('/multas', (req, res) => {
  res.json({ mensaje: 'Acá irían las multas' });
});

app.listen(port, () => {
  console.log(`Servidor escuchando en el puerto ${port}`);
});

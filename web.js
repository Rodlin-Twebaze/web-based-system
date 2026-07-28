const express = require('express');
const app = express();

app.use(express.json()); // Allows server to read JSON body data

// A simple GET endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'Server is running smoothly!' });
});

app.listen(3000, () => {
  console.log('Server running on http://localhost:3000');
});
const express = require('express');
require('dotenv').config(); // Load .env file
const cors = require('cors');
const morgan = require('morgan'); // HTTP request logger
const bodyParser = require('body-parser');

const { PORT } = require('./config/app');
const connectDB = require('./config/mongoose-connection');

// Routes
// const authRoutes = require('./routes/authRoutes');
const userRoutes = require('./routes/userRoutes');

// const { errorHandler } = require('./middlewares/errorHandler');

const app = express();

app.use(cors()); 
app.use(morgan('dev')); 
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

connectDB();

app.use(express.json()); 
app.use('/api/users', userRoutes);

app.get('/', (req, res) => {
  res.send('Welcome to the API');
});

app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date() });
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});

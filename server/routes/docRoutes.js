const express = require('express');
const router = express.Router();
const { registerUser, loginUser } = require('../controllers/userController');
const {registerDoctor} = require('../controllers/docController');
const { selectDoctor }= require('../controllers/patientController');
// POST /api/users/register-doctor
router.post('/register-doctor', registerDoctor);

// POST /api/users/login
router.post('/login', loginUser);
router.post('/select-doctor', selectDoctor);
module.exports = router;
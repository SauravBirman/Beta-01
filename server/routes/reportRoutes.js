const express = require('express');
const router = express.Router();
const { uploadReport, grantAccess, accessReport, getReportsByUser } = require('../controllers/reportController');
const auth = require('../middlewares/authUser');
const multer = require('multer');

const upload = multer({ storage: multer.memoryStorage() });

router.post('/upload', auth, upload.single('file'), uploadReport);
router.post('/grant', auth,  grantAccess);
router.get('/:reportId/download', auth, accessReport);
// Get reports for a specific user (patient)
router.get('/user/:userId', auth, getReportsByUser);
// Shortcut for the authenticated user's reports
router.get('/me', auth, getReportsByUser);

module.exports = router;

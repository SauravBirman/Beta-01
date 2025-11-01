const express = require('express');
const router = express.Router();
const { uploadReport, grantAccess, accessReport} = require('../controllers/reportController');
const auth = require('../middlewares/authUser');
const multer = require('multer');

const upload = multer({ storage: multer.memoryStorage() });

router.post('/upload', auth, upload.single('file'), uploadReport);
router.post('/grant', auth, grantAccess);
router.get('/:reportId/download', auth, accessReport);

module.exports = router;

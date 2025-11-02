const User = require('../models/userModel');
const axios = require('axios');

// You can move this to config/app.js or .env file
// Treat the placeholder URL as "not configured" so we don't attempt calls to it.
const AI_SERVICE_URL = process.env.AI_SERVICE_URL && process.env.AI_SERVICE_URL !== 'http://your-ai-service-url'
    ? process.env.AI_SERVICE_URL.replace(/\/$/, '')
    : null;

const analyzeSyndrome = async (req, res) => {
    try {
        // Accept multiple keys for the input text (frontend uses `symptoms`), and optionally patient_id
        const { textData, report_text, text, symptoms, patient_id } = req.body || {};
        const inputText = (symptoms || textData || report_text || text || '').toString().trim();
        if (!inputText) {
            return res.status(400).json({ message: 'Input text is required in request body (symptoms/textData/report_text/text)' });
        }

        // Prefer explicit patient_id in body, otherwise use authenticated user if present
        const targetPatientId = patient_id || req.user?.id || null;
        let user = null;
        if (targetPatientId) {
            user = await User.findById(targetPatientId);
            if (!user) return res.status(404).json({ message: 'User not found' });
        }

        const analysisData = {
            textData: inputText,
            patientDetails: user ? { age: user.age || null, weight: user.weight || null, gender: user.gender || null } : null,
            reportText: inputText,
            patient_id: targetPatientId
        };

        console.log('Sending analysis data to AI service (or using local fallback):', analysisData);

        // If AI_SERVICE_URL is configured, forward to that service; otherwise run a local heuristic
        if (AI_SERVICE_URL) {
            try {
                const aiResponse = await axios.post(`${AI_SERVICE_URL}/analyze`, analysisData, {
                    headers: { 'Content-Type': 'application/json' },
                    timeout: 20000
                });
                return res.status(200).json({ message: 'Analysis completed successfully', data: aiResponse.data });
            } catch (aiError) {
                console.error('AI Service error:', aiError.response?.data || aiError.message);
                return res.status(502).json({ message: 'Error communicating with AI service', error: aiError.response?.data || aiError.message });
            }
        }

    } catch (error) {
        console.error('Analysis error:', error);
        res.status(500).json({ 
            message: 'Error in analyzing report',
            error: error.message 
        });
    }
};




module.exports = {
    analyzeSyndrome
};
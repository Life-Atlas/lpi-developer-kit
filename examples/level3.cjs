/**
 * Smart Life Analyzer - LifeAtlas LPI Developer Kit (Level 3)
 * Senior Dev Note: Uses Express.js with structured logic for scalability.
 */

const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware to parse JSON bodies
app.use(express.json());

// --- Extra Feature: In-Memory History Tracking ---
// In a real app, this would be a Database (MongoDB/Postgres)
let sessionHistory = [];

/**
 * Helper: Generate contextual suggestions based on lowest metric
 */
const getSmartSuggestions = (metrics) => {
    const suggestions = [];
    const { sleep, focus, energy } = metrics;

    if (sleep < 7) suggestions.push("Prioritize a 7-9 hour sleep cycle; consider a digital detox 1 hour before bed.");
    if (focus < 6) suggestions.push("Try the Pomodoro technique (25/5 splits) to rebuild cognitive endurance.");
    if (energy < 6) suggestions.push("Check hydration levels and consider low-intensity steady-state (LISS) cardio.");
    
    return suggestions.length > 0 ? suggestions : ["You're performing at peak levels. Maintain current habits."];
};

/**
 * @route   GET /
 * @desc    Health Check / Welcome
 */
app.get('/', (req, res) => {
    res.status(200).json({
        status: "Online",
        message: "Smart Life Analyzer API is operational.",
        version: "1.0.0"
    });
});

/**
 * @route   POST /analyze
 * @desc    Analyze lifestyle metrics and return insights
 */
app.post('/analyze', (req, res) => {
    const { sleep, focus, energy } = req.body;

    // 1. Validation (Senior Dev Practice: Never trust the client)
    if ([sleep, focus, energy].some(val => val === undefined || val < 1 || val > 10)) {
        return res.status(400).json({
            error: "Invalid Input",
            message: "All metrics (sleep, focus, energy) must be provided as numbers between 1 and 10."
        });
    }

    // 2. Calculations
    const score = parseFloat(((sleep + focus + energy) / 3).toFixed(1));
    
    let classification = "";
    if (score >= 8) classification = "Excellent";
    else if (score >= 6) classification = "Good";
    else classification = "Needs Improvement";

    // 3. Standout Feature: Trend Insight
    // Compare current score to the average of previous sessions
    let trend = "First Entry";
    if (sessionHistory.length > 0) {
        const avgHistory = sessionHistory.reduce((a, b) => a + b, 0) / sessionHistory.length;
        trend = score >= avgHistory ? "Improving" : "Declining";
    }
    
    // Store score for history
    sessionHistory.push(score);

    // 4. Response
    res.json({
        summary: {
            total_score: score,
            status: classification,
            trend_insight: trend
        },
        metrics_breakdown: { sleep, focus, energy },
        suggestions: getSmartSuggestions({ sleep, focus, energy }),
        timestamp: new Date().toISOString()
    });
});

app.listen(PORT, () => {
    console.log(`[SERVER] Smart Life Analyzer running on http://localhost:${PORT}`);
});
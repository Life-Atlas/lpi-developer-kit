"""
Flask Interface for LPI Digital Twin Advisor (Improved)
------------------------------------------------------
Serves the agent with clean API responses + better structure
"""

from flask import Flask, render_template, request, jsonify
from agent import run_agent
import logging

app = Flask(__name__)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LPI_WEB")

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    """Render UI"""
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def query_agent():
    """
    Handles user queries and returns structured response.
    """
    try:
        data = request.get_json() or {}
        question = data.get('question', '').strip()

        if not question:
            return jsonify({
                "status": "error",
                "message": "No question provided"
            }), 400

        logger.info(f"User question: {question}")

        # Call agent
        result = run_agent(question)

        return jsonify({
            "status": "success",
            "question": question,
            "result": result
        }), 200

    except Exception as e:
        logger.error(f"Agent failure: {str(e)}")

        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "details": str(e)
        }), 500


# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("\n🚀 Starting LPI Digital Twin Advisor Web App...")
    print("👉 Open: http://localhost:5000\n")

    app.run(debug=True, port=5000)

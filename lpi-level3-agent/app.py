"""
Flask Interface for LPI Agent
-----------------------------
Serves the dynamic digital twin context logic to our Custom CSS/HTML
Glassmorphism Web UI.

Author: Vineet Sharma
Date: 2026-04-16
"""

from flask import Flask, render_template, request, jsonify
from agent import run_agent

app = Flask(__name__)

@app.route('/')
def index() -> str:
    """Renders the main UI root view."""
    return str(render_template('index.html'))

@app.route('/api/query', methods=['POST'])
def query_agent(): # type: ignore
    """
    Accepts POST requests containing 'question'.
    Securely catches processing failures safely responding with 500s.
    """
    try:
        data = request.json or {}
        question: str = data.get('question', '')
        if not question:
            return jsonify({"error": "No question provided"}), 400
        
        result = run_agent(question)
        return jsonify(result), 200
    except Exception as e:
        app.logger.error(f"Internal Agent Execution Failure: {e}")
        return jsonify({"error": f"Internal execution failure: {str(e)}"}), 500

if __name__ == "__main__":
    # Exposing the UI endpoints locally
    app.run(debug=True, port=5000)

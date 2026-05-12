from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

workers = pd.read_csv("data/factory_workers (1).csv")

@app.route("/")
def home():
    return jsonify({
        "message": "Level 6 Neo4j Flask API Running"
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "running"
    })

@app.route("/workers")
def workers_count():
    return jsonify({
        "total_workers": len(workers)
    })

@app.route("/stats")
def stats():
    return jsonify({
        "workers": len(workers),
        "columns": list(workers.columns)
    })

if __name__ == "__main__":
    app.run(debug=True)
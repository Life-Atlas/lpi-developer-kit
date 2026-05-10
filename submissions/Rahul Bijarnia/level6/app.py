from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Level 6 Neo4j App Running Successfully!"

if __name__ == "__main__":
    app.run(debug=True, port=5050)
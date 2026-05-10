# Level 6 - Neo4j Flask & Streamlit Integration Project

## Overview

This project demonstrates the integration of a Neo4j AuraDB database with Python Flask and Streamlit applications.  
The application connects to Neo4j using environment variables stored securely in a `.env` file.

The project includes:
- Neo4j AuraDB connection
- Flask web application
- Streamlit integration
- Environment variable configuration
- CSV dataset handling
- Graph database connectivity verification

---

## Tech Stack

- Python 3.14
- Flask
- Streamlit
- Neo4j AuraDB
- Neo4j Python Driver
- dotenv

---

## Project Structure

```text
level6/
│
├── app.py
├── seed_graph.py
├── requirements.txt
├── README.md
├── How-I-Did-It.md
├── .env
│
└── data/
    ├── factory_capacity.csv
    ├── factory_production.csv
    └── factory_workers.csv
```

---

## Installation

### 1. Clone Repository

```bash
git clone <your-repository-url>
cd lpi-developer-kit/submissions/Rahul\ Bijarnia/level6
```

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install flask streamlit neo4j python-dotenv
```

---

## Neo4j AuraDB Setup

1. Create a Neo4j AuraDB Free instance
2. Open Developer Hub
3. Select Python connection
4. Copy:
   - URI
   - Username
   - Password

---

## Configure Environment Variables

Create a `.env` file inside the `level6` folder.

Example:

```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=your_username
NEO4J_PASSWORD=your_password
```

---

## Verify Neo4j Connection

Run:

```bash
python seed_graph.py
```

Expected Output:

```text
Connected Successfully
```

---

## Run Flask Application

Run:

```bash
python app.py
```

Expected Output:

```text
Running on http://127.0.0.1:5050
```

Open the URL in browser.

---

## Run Streamlit Application

Run:

```bash
streamlit run app.py
```

Expected Output:

```text
Local URL: http://localhost:8501
```

Open the Streamlit URL in browser.

---

## Application Output

The application displays:

```text
Level 6 Neo4j App Running Successfully!
```

---

## Features

- Secure Neo4j connection using `.env`
- Flask integration
- Streamlit integration
- Neo4j AuraDB connectivity verification
- Environment variable handling
- Local development server

---

## Challenges Faced

- Neo4j authentication failure
- Incorrect environment variable names
- Flask port permission issue
- VS Code `.env` loading issue

---

## Solutions Implemented

- Corrected `.env` variable names
- Enabled `python.terminal.useEnvFile`
- Restarted VS Code terminal
- Changed Flask port to `5050`

---

## Author

Rahul Bijarnia
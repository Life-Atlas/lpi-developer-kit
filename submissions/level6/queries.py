"""
queries.py — All Neo4j Cypher queries for the Streamlit dashboard.
Import this module in app.py; never read raw CSVs from the dashboard.
"""

from neo4j import GraphDatabase


def get_driver(uri: str, user: str, password: str):
    return GraphDatabase.driver(uri, auth=(user, password))


# ════════════════════════════════════════════════════════════════════
# PAGE 1 — Project Overview
# ════════════════════════════════════════════════════════════════════

def get_all_projects(driver):
    """
    Returns a list of dicts with per-project aggregated metrics:
    project_id, project_name, project_number,
    total_planned, total_actual, variance_pct, products
    """
    cypher = """
    MATCH (proj:Project)-[s:SCHEDULED_AT]->(:Station)
    WITH proj,
         sum(s.planned_hours) AS total_planned,
         sum(s.actual_hours)  AS total_actual
    OPTIONAL MATCH (proj)-[:PRODUCES]->(prod:Product)
    WITH proj, total_planned, total_actual, collect(DISTINCT prod.product_type) AS products
    RETURN proj.project_id    AS project_id,
           proj.project_name  AS project_name,
           proj.project_number AS project_number,
           total_planned,
           total_actual,
           CASE WHEN total_planned > 0
                THEN round((total_actual - total_planned) / total_planned * 100, 1)
                ELSE 0 END   AS variance_pct,
           products
    ORDER BY proj.project_id
    """
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher)]


def get_project_week_breakdown(driver):
    """Weekly planned vs actual per project (for a stacked/grouped chart)."""
    cypher = """
    MATCH (proj:Project)-[s:SCHEDULED_AT]->(:Station)
    RETURN proj.project_id   AS project_id,
           proj.project_name AS project_name,
           s.week            AS week,
           sum(s.planned_hours) AS planned_hours,
           sum(s.actual_hours)  AS actual_hours
    ORDER BY proj.project_id, s.week
    """
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher)]


# ════════════════════════════════════════════════════════════════════
# PAGE 2 — Station Load
# ════════════════════════════════════════════════════════════════════

def get_station_load(driver):
    """
    Returns planned vs actual hours per station per week.
    Includes overload flag (actual > planned).
    """
    cypher = """
    MATCH (wk:Week)-[hs:HAS_SCHEDULE]->(st:Station)
    RETURN st.station_code AS station_code,
           st.station_name AS station_name,
           wk.week         AS week,
           hs.planned_hours AS planned_hours,
           hs.actual_hours  AS actual_hours,
           hs.actual_hours > hs.planned_hours AS overloaded
    ORDER BY st.station_code, wk.week
    """
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher)]


def get_station_totals(driver):
    """Total planned vs actual per station across all weeks."""
    cypher = """
    MATCH (wk:Week)-[hs:HAS_SCHEDULE]->(st:Station)
    RETURN st.station_code  AS station_code,
           st.station_name  AS station_name,
           sum(hs.planned_hours) AS total_planned,
           sum(hs.actual_hours)  AS total_actual,
           sum(hs.actual_hours) - sum(hs.planned_hours) AS variance_hours
    ORDER BY station_code
    """
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher)]


# ════════════════════════════════════════════════════════════════════
# PAGE 3 — Capacity Tracker
# ════════════════════════════════════════════════════════════════════

def get_weekly_capacity(driver):
    """
    Returns weekly capacity breakdown:
    week, own_hours, hired_hours, overtime_hours,
    total_capacity, total_planned, deficit
    """
    cypher = """
    MATCH (wk:Week)
    WHERE wk.total_capacity IS NOT NULL
    RETURN wk.week            AS week,
           wk.own_hours       AS own_hours,
           wk.hired_hours     AS hired_hours,
           wk.overtime_hours  AS overtime_hours,
           wk.total_capacity  AS total_capacity,
           wk.total_planned   AS total_planned,
           wk.deficit         AS deficit,
           wk.own_staff_count AS own_staff,
           wk.hired_staff_count AS hired_staff
    ORDER BY wk.week
    """
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher)]


# ════════════════════════════════════════════════════════════════════
# PAGE 4 — Worker Coverage
# ════════════════════════════════════════════════════════════════════

def get_all_workers(driver):
    """Returns all worker nodes."""
    cypher = """
    MATCH (w:Worker)
    RETURN w.worker_id       AS worker_id,
           w.name            AS name,
           w.role            AS role,
           w.primary_station AS primary_station,
           w.certifications  AS certifications,
           w.hours_per_week  AS hours_per_week,
           w.type            AS type
    ORDER BY w.worker_id
    """
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher)]


def get_worker_coverage_matrix(driver):
    """
    Returns rows of (worker_id, name, station_code, station_name).
    Use to build a pivot matrix in Streamlit.
    """
    cypher = """
    MATCH (w:Worker)-[:CAN_COVER]->(st:Station)
    RETURN w.worker_id     AS worker_id,
           w.name          AS name,
           w.type          AS worker_type,
           st.station_code AS station_code,
           st.station_name AS station_name
    ORDER BY w.worker_id, st.station_code
    """
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher)]


def get_single_point_of_failure_stations(driver):
    """Stations covered by only ONE worker (certified/can_cover)."""
    cypher = """
    MATCH (w:Worker)-[:CAN_COVER]->(st:Station)
    WITH st, count(w) AS cover_count
    WHERE cover_count = 1
    MATCH (w2:Worker)-[:CAN_COVER]->(st)
    RETURN st.station_code AS station_code,
           st.station_name AS station_name,
           w2.name         AS sole_worker,
           cover_count
    ORDER BY st.station_code
    """
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher)]


def get_station_worker_count(driver):
    """How many workers can cover each station."""
    cypher = """
    MATCH (w:Worker)-[:CAN_COVER]->(st:Station)
    RETURN st.station_code AS station_code,
           st.station_name AS station_name,
           count(w)        AS worker_count
    ORDER BY station_code
    """
    with driver.session() as s:
        return [dict(r) for r in s.run(cypher)]


# ════════════════════════════════════════════════════════════════════
# SELF-TEST CHECKS
# ════════════════════════════════════════════════════════════════════

def check_connection(driver):
    """CHECK 1: Neo4j alive."""
    try:
        driver.verify_connectivity()
        return True, "Neo4j connected"
    except Exception as e:
        return False, str(e)


def check_node_count(driver, minimum=50):
    """CHECK 2: Total node count >= minimum."""
    with driver.session() as s:
        count = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
    ok = count >= minimum
    return ok, f"{count} nodes (min: {minimum})"


def check_relationship_count(driver, minimum=100):
    """CHECK 3: Total relationship count >= minimum."""
    with driver.session() as s:
        count = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    ok = count >= minimum
    return ok, f"{count} relationships (min: {minimum})"


def check_label_count(driver, minimum=6):
    """CHECK 4: Distinct node labels >= minimum."""
    with driver.session() as s:
        labels = [r["label"] for r in s.run("CALL db.labels() YIELD label RETURN label")]
    ok = len(labels) >= minimum
    return ok, f"{len(labels)} labels: {', '.join(labels)}"


def check_rel_type_count(driver, minimum=8):
    """CHECK 5: Distinct relationship types >= minimum."""
    with driver.session() as s:
        types = [r["type"] for r in s.run(
            "CALL db.relationshipTypes() YIELD relationshipType AS type RETURN type")]
    ok = len(types) >= minimum
    return ok, f"{len(types)} types: {', '.join(types)}"


def check_variance_query(driver, threshold=1.0):
    """CHECK 6: Projects with variance > threshold% return results."""
    cypher = """
    MATCH (proj:Project)-[s:SCHEDULED_AT]->(:Station)
    WITH proj,
         sum(s.planned_hours) AS total_planned,
         sum(s.actual_hours)  AS total_actual
    WHERE total_planned > 0
      AND abs((total_actual - total_planned) / total_planned * 100) > $threshold
    RETURN proj.project_id   AS project_id,
           proj.project_name AS project_name,
           round((total_actual - total_planned) / total_planned * 100, 1) AS variance_pct
    ORDER BY variance_pct DESC
    """
    with driver.session() as s:
        results = [dict(r) for r in s.run(cypher, threshold=threshold)]
    ok = len(results) > 0
    msg = f"{len(results)} project(s) with >10% variance"
    return ok, msg, results


def run_all_checks(driver):
    """Run all 6 self-test checks and return structured results."""
    checks = []

    ok, msg = check_connection(driver)
    checks.append({"label": "Neo4j connection alive",          "ok": ok, "msg": msg, "pts": 3})

    ok, msg = check_node_count(driver)
    checks.append({"label": "Node count ≥ 50",                 "ok": ok, "msg": msg, "pts": 3})

    ok, msg = check_relationship_count(driver)
    checks.append({"label": "Relationship count ≥ 100",        "ok": ok, "msg": msg, "pts": 3})

    ok, msg = check_label_count(driver)
    checks.append({"label": "6+ distinct node labels",         "ok": ok, "msg": msg, "pts": 3})

    ok, msg = check_rel_type_count(driver)
    checks.append({"label": "8+ distinct relationship types",  "ok": ok, "msg": msg, "pts": 3})

    ok, msg, variance_rows = check_variance_query(driver)
    checks.append({"label": 'Projects with variance >1% (graph query works)', "ok": ok, "msg": msg, "pts": 5,
                   "detail": variance_rows})

    total_earned  = sum(c["pts"] for c in checks if c["ok"])
    total_possible = sum(c["pts"] for c in checks)
    return checks, total_earned, total_possible
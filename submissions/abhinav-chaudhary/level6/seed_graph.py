"""
seed_graph.py — Level 6 Neo4j Graph Seed Script
================================================
Swedish steel fabrication factory knowledge graph.

Loads:
  - factory_production.csv  → Project, Product, Station, ProductionEntry, BOP
  - factory_workers.csv     → Worker, Certification
  - factory_capacity.csv    → Week, CapacitySnapshot

Relationships created (12 types, 100+ instances):
  HAS_RUN, USES_PRODUCT, PROCESSED_AT*, SCHEDULED_IN*, REQUIRES_STATION,
  STRUCTURED_BY, PRIMARILY_AT, CAN_COVER, WORKED_ON, HOLDS,
  REQUIRES_CERT, HAS_SNAPSHOT

  * PROCESSED_AT carries: planned_hours, actual_hours, completed_units
  * SCHEDULED_IN carries: planned_hours, actual_hours

Usage:
  pip install neo4j python-dotenv
  Copy your .env next to this file (see .env.example below), then:
  python seed_graph.py

.env.example:
  NEO4J_URI=bolt://localhost:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=your_password
"""

import csv
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

# ─────────────────────────────────────────────
# 0. Configuration
# ─────────────────────────────────────────────
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# CSVs must be in the same directory as this script
BASE_DIR        = Path(__file__).parent
PRODUCTION_CSV  = BASE_DIR / "factory_production.csv"
WORKERS_CSV     = BASE_DIR / "factory_workers.csv"
CAPACITY_CSV    = BASE_DIR / "factory_capacity.csv"

# Station → certifications required (derived from worker cert domain knowledge
# and the answers.md analysis; used to build REQUIRES_CERT edges)
STATION_CERT_MAP = {
    "011": ["MIG/MAG"],
    "012": ["Surface treatment", "CE marking"],
    "013": ["Surface treatment"],
    "014": ["MIG/MAG", "TIG"],
    "015": ["SIS", "SS-EN 1090", "NDT"],
    "016": ["Casting", "Formwork"],
    "017": ["Surface treatment", "Spray painting"],
    "018": ["Sheet metal", "Assembly"],
    "019": ["Assembly", "Welding"],
    "021": ["CE", "ISO 9001"],
}


# ─────────────────────────────────────────────
# 1. CSV helpers
# ─────────────────────────────────────────────

def load_csv(path: Path) -> list[dict]:
    """Read a CSV file and return a list of row dicts."""
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def split_field(value: str) -> list[str]:
    """Split a comma-separated field, stripping whitespace from each part."""
    return [v.strip() for v in value.split(",") if v.strip()]


# ─────────────────────────────────────────────
# 2. Constraint / index creation
# ─────────────────────────────────────────────

CONSTRAINTS = [
    # Uniqueness constraint per node label + primary key
    ("Project",         "project_id"),
    ("ProductionEntry", "entry_id"),
    ("Station",         "station_code"),
    ("Product",         "product_type"),
    ("Worker",          "worker_id"),
    ("Week",            "week_id"),
    ("Certification",   "cert_id"),
    ("BOP",             "bop_id"),
    # CapacitySnapshot has no natural standalone PK; it's always reached via
    # Week so no separate uniqueness constraint needed.
]


def create_constraints(session) -> None:
    """Create uniqueness constraints idempotently (Neo4j 5.x syntax)."""
    print("  Creating uniqueness constraints …")
    for label, prop in CONSTRAINTS:
        name = f"unique_{label.lower()}_{prop}"
        cypher = (
            f"CREATE CONSTRAINT {name} IF NOT EXISTS "
            f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
        )
        session.run(cypher)
    print(f"  ✓ {len(CONSTRAINTS)} constraints ensured.")


# ─────────────────────────────────────────────
# 3. Node seeding
# ─────────────────────────────────────────────

def seed_projects_products_stations_bops_entries(session, rows: list[dict]) -> None:
    """
    From factory_production.csv create:
      Project, Product, Station, BOP, ProductionEntry nodes
    and:
      HAS_RUN, USES_PRODUCT, PROCESSED_AT, SCHEDULED_IN,
      REQUIRES_STATION, STRUCTURED_BY relationships.
    """
    print("  Merging Project / Product / Station / BOP nodes …")

    # ── Projects ──────────────────────────────
    projects_seen = {}
    for r in rows:
        pid = r["project_id"]
        if pid not in projects_seen:
            projects_seen[pid] = r

    session.run(
        """
        UNWIND $projects AS p
        MERGE (n:Project {project_id: p.project_id})
          ON CREATE SET
            n.project_number = p.project_number,
            n.project_name   = p.project_name,
            n.etapp          = p.etapp
        """,
        projects=[
            {
                "project_id":     v["project_id"],
                "project_number": v["project_number"],
                "project_name":   v["project_name"],
                "etapp":          v["etapp"],
            }
            for v in projects_seen.values()
        ],
    )
    print(f"    ✓ {len(projects_seen)} Project nodes")

    # ── Products ──────────────────────────────
    products_seen = {}
    for r in rows:
        pt = r["product_type"]
        if pt not in products_seen:
            products_seen[pt] = r

    session.run(
        """
        UNWIND $products AS p
        MERGE (n:Product {product_type: p.product_type})
          ON CREATE SET
            n.unit        = p.unit,
            n.unit_factor = toFloat(p.unit_factor)
        """,
        products=[
            {
                "product_type": v["product_type"],
                "unit":         v["unit"],
                "unit_factor":  v["unit_factor"],
            }
            for v in products_seen.values()
        ],
    )
    print(f"    ✓ {len(products_seen)} Product nodes")

    # ── Stations ──────────────────────────────
    stations_seen = {}
    for r in rows:
        sc = r["station_code"]
        if sc not in stations_seen:
            stations_seen[sc] = r

    session.run(
        """
        UNWIND $stations AS s
        MERGE (n:Station {station_code: s.station_code})
          ON CREATE SET n.station_name = s.station_name
        """,
        stations=[
            {"station_code": v["station_code"], "station_name": v["station_name"]}
            for v in stations_seen.values()
        ],
    )
    print(f"    ✓ {len(stations_seen)} Station nodes")

    # ── BOPs ──────────────────────────────────
    bops_seen = {}
    for r in rows:
        bid = r["bop"]
        if bid not in bops_seen:
            bops_seen[bid] = r

    session.run(
        """
        UNWIND $bops AS b
        MERGE (n:BOP {bop_id: b.bop_id})
          ON CREATE SET n.etapp = b.etapp
        """,
        bops=[
            {"bop_id": v["bop"], "etapp": v["etapp"]}
            for v in bops_seen.values()
        ],
    )
    print(f"    ✓ {len(bops_seen)} BOP nodes")

    # ── ProductionEntry nodes ─────────────────
    # One node per CSV row; entry_id = "<project_id>_<station_code>_<week>"
    entries = []
    for i, r in enumerate(rows):
        entry_id = f"{r['project_id']}_{r['station_code']}_{r['week']}"
        entries.append(
            {
                "entry_id":       entry_id,
                "planned_hours":  float(r["planned_hours"]),
                "actual_hours":   float(r["actual_hours"]),
                "completed_units": int(r["completed_units"]),
                "quantity":       int(r["quantity"]),
                # FK references for relationship creation below
                "project_id":    r["project_id"],
                "product_type":  r["product_type"],
                "station_code":  r["station_code"],
                "bop_id":        r["bop"],
                "week_id":       r["week"],
            }
        )

    session.run(
        """
        UNWIND $entries AS e
        MERGE (n:ProductionEntry {entry_id: e.entry_id})
          ON CREATE SET
            n.planned_hours   = e.planned_hours,
            n.actual_hours    = e.actual_hours,
            n.completed_units = e.completed_units,
            n.quantity        = e.quantity
        """,
        entries=entries,
    )
    print(f"    ✓ {len(entries)} ProductionEntry nodes")

    # ─────────────────────────────────────────
    # Relationships from production data
    # ─────────────────────────────────────────
    print("  Creating production relationships …")

    # HAS_RUN: Project → ProductionEntry
    session.run(
        """
        UNWIND $entries AS e
        MATCH (proj:Project        {project_id:  e.project_id})
        MATCH (pe:ProductionEntry  {entry_id:    e.entry_id})
        MERGE (proj)-[:HAS_RUN]->(pe)
        """,
        entries=entries,
    )
    print(f"    ✓ HAS_RUN ({len(entries)} edges)")

    # USES_PRODUCT: ProductionEntry → Product
    session.run(
        """
        UNWIND $entries AS e
        MATCH (pe:ProductionEntry {entry_id:    e.entry_id})
        MATCH (pr:Product         {product_type: e.product_type})
        MERGE (pe)-[:USES_PRODUCT]->(pr)
        """,
        entries=entries,
    )
    print(f"    ✓ USES_PRODUCT ({len(entries)} edges)")

    # PROCESSED_AT: ProductionEntry → Station  [★ with properties]
    session.run(
        """
        UNWIND $entries AS e
        MATCH (pe:ProductionEntry {entry_id:    e.entry_id})
        MATCH (st:Station         {station_code: e.station_code})
        MERGE (pe)-[r:PROCESSED_AT]->(st)
          ON CREATE SET
            r.planned_hours   = e.planned_hours,
            r.actual_hours    = e.actual_hours,
            r.completed_units = e.completed_units
        """,
        entries=entries,
    )
    print(f"    ✓ PROCESSED_AT ({len(entries)} edges, with planned_hours / actual_hours / completed_units)")

    # SCHEDULED_IN: ProductionEntry → Week  [★ with properties]
    session.run(
        """
        UNWIND $entries AS e
        MATCH (pe:ProductionEntry {entry_id: e.entry_id})
        MATCH (w:Week             {week_id:  e.week_id})
        MERGE (pe)-[r:SCHEDULED_IN]->(w)
          ON CREATE SET
            r.planned_hours = e.planned_hours,
            r.actual_hours  = e.actual_hours
        """,
        entries=entries,
    )
    print(f"    ✓ SCHEDULED_IN ({len(entries)} edges, with planned_hours / actual_hours)")

    # REQUIRES_STATION: Project → Station (derived — distinct pairs)
    proj_station_pairs = list(
        {(r["project_id"], r["station_code"]) for r in rows}
    )
    session.run(
        """
        UNWIND $pairs AS pair
        MATCH (proj:Project {project_id:   pair[0]})
        MATCH (st:Station   {station_code: pair[1]})
        MERGE (proj)-[:REQUIRES_STATION]->(st)
        """,
        pairs=[[p, s] for p, s in proj_station_pairs],
    )
    print(f"    ✓ REQUIRES_STATION ({len(proj_station_pairs)} edges)")

    # STRUCTURED_BY: Project → BOP
    proj_bop_pairs = list(
        {(r["project_id"], r["bop"]) for r in rows}
    )
    session.run(
        """
        UNWIND $pairs AS pair
        MATCH (proj:Project {project_id: pair[0]})
        MATCH (b:BOP        {bop_id:     pair[1]})
        MERGE (proj)-[:STRUCTURED_BY]->(b)
        """,
        pairs=[[p, b] for p, b in proj_bop_pairs],
    )
    print(f"    ✓ STRUCTURED_BY ({len(proj_bop_pairs)} edges)")


def seed_weeks_and_snapshots(session, rows: list[dict]) -> None:
    """
    From factory_capacity.csv create:
      Week, CapacitySnapshot nodes
    and:
      HAS_SNAPSHOT relationship.
    """
    print("  Merging Week / CapacitySnapshot nodes …")

    weeks = []
    for r in rows:
        weeks.append(
            {
                "week_id":        r["week"],
                "own_hours":      int(r["own_hours"]),
                "hired_hours":    int(r["hired_hours"]),
                "overtime_hours": int(r["overtime_hours"]),
                "total_capacity": int(r["total_capacity"]),
                "total_planned":  int(r["total_planned"]),
                "deficit":        int(r["deficit"]),
            }
        )

    # Week nodes (lightweight time anchors)
    session.run(
        """
        UNWIND $weeks AS w
        MERGE (n:Week {week_id: w.week_id})
        """,
        weeks=weeks,
    )
    print(f"    ✓ {len(weeks)} Week nodes")

    # CapacitySnapshot nodes keyed by week_id so MERGE stays idempotent;
    # the snapshot itself has no natural standalone PK, so we embed week_id
    # as a surrogate for idempotency only — it is not exposed as a schema key.
    session.run(
        """
        UNWIND $weeks AS w
        MATCH (wk:Week {week_id: w.week_id})
        MERGE (cs:CapacitySnapshot {week_id: w.week_id})
          ON CREATE SET
            cs.own_hours      = w.own_hours,
            cs.hired_hours    = w.hired_hours,
            cs.overtime_hours = w.overtime_hours,
            cs.total_capacity = w.total_capacity,
            cs.total_planned  = w.total_planned,
            cs.deficit        = w.deficit
        MERGE (wk)-[:HAS_SNAPSHOT]->(cs)
        """,
        weeks=weeks,
    )
    print(f"    ✓ {len(weeks)} CapacitySnapshot nodes")
    print(f"    ✓ HAS_SNAPSHOT ({len(weeks)} edges)")


def seed_workers_and_certs(session, rows: list[dict]) -> None:
    """
    From factory_workers.csv create:
      Worker, Certification nodes
    and:
      PRIMARILY_AT, CAN_COVER, HOLDS, WORKED_ON relationships.
    Also derives REQUIRES_CERT (Station → Certification).
    """
    print("  Merging Worker / Certification nodes …")

    # ── Certification nodes ───────────────────
    # Collect all unique cert names across all workers
    all_certs: set[str] = set()
    for r in rows:
        all_certs.update(split_field(r["certifications"]))
    # Also include certs from STATION_CERT_MAP
    for certs in STATION_CERT_MAP.values():
        all_certs.update(certs)

    cert_list = [
        {
            "cert_id":     cert.lower().replace(" ", "_").replace("/", "_"),
            "name":        cert,
            "issuing_body": _issuing_body(cert),
        }
        for cert in sorted(all_certs)
    ]
    session.run(
        """
        UNWIND $certs AS c
        MERGE (n:Certification {cert_id: c.cert_id})
          ON CREATE SET
            n.name        = c.name,
            n.issuing_body = c.issuing_body
        """,
        certs=cert_list,
    )
    print(f"    ✓ {len(cert_list)} Certification nodes")

    # ── Worker nodes ──────────────────────────
    workers = []
    for r in rows:
        # primary_station may be "all" for foremen — normalise to None
        primary = r["primary_station"].strip()
        workers.append(
            {
                "worker_id":      r["worker_id"],
                "name":           r["name"],
                "role":           r["role"],
                "hours_per_week": int(r["hours_per_week"]),
                "type":           r["type"],
                "primary_station": None if primary == "all" else primary,
                "can_cover":      split_field(r["can_cover_stations"]),
                "certifications": split_field(r["certifications"]),
            }
        )

    session.run(
        """
        UNWIND $workers AS w
        MERGE (n:Worker {worker_id: w.worker_id})
          ON CREATE SET
            n.name           = w.name,
            n.role           = w.role,
            n.hours_per_week = w.hours_per_week,
            n.type           = w.type
        """,
        workers=workers,
    )
    print(f"    ✓ {len(workers)} Worker nodes")

    # ── PRIMARILY_AT: Worker → Station ────────
    # Skip workers whose primary_station is "all" (Victor Elm, foreman)
    primary_pairs = [
        {"worker_id": w["worker_id"], "station_code": w["primary_station"]}
        for w in workers
        if w["primary_station"] is not None
    ]
    session.run(
        """
        UNWIND $pairs AS p
        MATCH (w:Worker  {worker_id:   p.worker_id})
        MATCH (s:Station {station_code: p.station_code})
        MERGE (w)-[:PRIMARILY_AT]->(s)
        """,
        pairs=primary_pairs,
    )
    print(f"    ✓ PRIMARILY_AT ({len(primary_pairs)} edges)")

    # ── CAN_COVER: Worker → Station ───────────
    can_cover_pairs = []
    for w in workers:
        for sc in w["can_cover"]:
            can_cover_pairs.append({"worker_id": w["worker_id"], "station_code": sc})

    session.run(
        """
        UNWIND $pairs AS p
        MATCH (w:Worker  {worker_id:   p.worker_id})
        MATCH (s:Station {station_code: p.station_code})
        MERGE (w)-[:CAN_COVER]->(s)
        """,
        pairs=can_cover_pairs,
    )
    print(f"    ✓ CAN_COVER ({len(can_cover_pairs)} edges)")

    # ── HOLDS: Worker → Certification ─────────
    holds_pairs = []
    for w in workers:
        for cert_name in w["certifications"]:
            cert_id = cert_name.lower().replace(" ", "_").replace("/", "_")
            holds_pairs.append({"worker_id": w["worker_id"], "cert_id": cert_id})

    session.run(
        """
        UNWIND $pairs AS p
        MATCH (w:Worker        {worker_id: p.worker_id})
        MATCH (c:Certification {cert_id:   p.cert_id})
        MERGE (w)-[:HOLDS]->(c)
        """,
        pairs=holds_pairs,
    )
    print(f"    ✓ HOLDS ({len(holds_pairs)} edges)")

    # ── WORKED_ON: Worker → ProductionEntry ───
    # Heuristic: a worker WORKED_ON every ProductionEntry whose station_code
    # is in their can_cover list (they could staff that station).
    # The foreman (W11, can_cover all stations) is linked to all entries.
    worked_on_pairs = []
    for w in workers:
        cover_set = set(w["can_cover"])
        worked_on_pairs.append(
            {
                "worker_id":    w["worker_id"],
                "station_codes": list(cover_set),
            }
        )

    session.run(
        """
        UNWIND $workers AS w
        MATCH (wk:Worker {worker_id: w.worker_id})
        MATCH (pe:ProductionEntry)-[:PROCESSED_AT]->(s:Station)
        WHERE s.station_code IN w.station_codes
        MERGE (wk)-[:WORKED_ON]->(pe)
        """,
        workers=worked_on_pairs,
    )
    print("    ✓ WORKED_ON (all worker-station-entry assignments merged)")


def seed_requires_cert(session) -> None:
    """
    Create REQUIRES_CERT: Station → Certification edges
    using the domain-derived STATION_CERT_MAP.
    """
    print("  Creating REQUIRES_CERT relationships …")
    pairs = []
    for station_code, cert_names in STATION_CERT_MAP.items():
        for cert_name in cert_names:
            cert_id = cert_name.lower().replace(" ", "_").replace("/", "_")
            pairs.append({"station_code": station_code, "cert_id": cert_id})

    session.run(
        """
        UNWIND $pairs AS p
        MATCH (s:Station       {station_code: p.station_code})
        MATCH (c:Certification {cert_id:      p.cert_id})
        MERGE (s)-[:REQUIRES_CERT]->(c)
        """,
        pairs=pairs,
    )
    print(f"    ✓ REQUIRES_CERT ({len(pairs)} edges)")


# ─────────────────────────────────────────────
# 4. Utility helpers
# ─────────────────────────────────────────────

def _issuing_body(cert_name: str) -> str:
    """Map a certification name to a plausible issuing body."""
    mapping = {
        "MIG/MAG":            "Swedish Welding Commission",
        "TIG":                "Swedish Welding Commission",
        "ISO 9606":           "ISO / SIS",
        "Surface treatment":  "Swedish Corrosion Institute",
        "CE marking":         "EU / Notified Body",
        "Blasting":           "Swedish Corrosion Institute",
        "Surface protection": "Swedish Corrosion Institute",
        "Hydraulics":         "Internal",
        "Mechanics":          "Internal",
        "Crane":              "Swedish Work Environment Authority",
        "SIS":                "SIS Swedish Standards Institute",
        "SS-EN 1090":         "SIS Swedish Standards Institute",
        "NDT":                "BINDT / PCN",
        "Casting":            "Swedish Foundry Association",
        "Formwork":           "Internal",
        "Spray painting":     "Swedish Corrosion Institute",
        "Sheet metal":        "Internal",
        "Assembly":           "Internal",
        "Welding":            "Swedish Welding Commission",
        "Leadership":         "Internal",
        "CE":                 "EU / Notified Body",
        "ISO 9001":           "ISO / SIS",
        "ISO 9001,SS-EN 1090,Audit": "ISO / SIS",
        "Audit":              "Internal",
    }
    return mapping.get(cert_name, "Internal")


# ─────────────────────────────────────────────
# 5. Verification report
# ─────────────────────────────────────────────

def print_graph_summary(session) -> None:
    """Print a quick node / relationship count summary."""
    print("\n" + "═" * 50)
    print("  Graph summary")
    print("═" * 50)

    node_counts = session.run(
        """
        CALL apoc.meta.stats() YIELD labels
        RETURN labels
        """
    )
    # Fall back to manual counts if APOC is not installed
    labels = [
        "Project", "ProductionEntry", "Station", "Product",
        "Worker", "Week", "CapacitySnapshot", "Certification", "BOP",
    ]
    total_nodes = 0
    for label in labels:
        result = session.run(f"MATCH (n:{label}) RETURN count(n) AS c")
        count = result.single()["c"]
        total_nodes += count
        print(f"  {label:<22} {count:>4} nodes")

    print(f"  {'─'*36}")
    print(f"  {'TOTAL':<22} {total_nodes:>4} nodes")

    rel_types = [
        "HAS_RUN", "USES_PRODUCT", "PROCESSED_AT", "SCHEDULED_IN",
        "REQUIRES_STATION", "STRUCTURED_BY", "PRIMARILY_AT", "CAN_COVER",
        "WORKED_ON", "HOLDS", "REQUIRES_CERT", "HAS_SNAPSHOT",
    ]
    total_rels = 0
    print()
    for rel in rel_types:
        result = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c")
        count = result.single()["c"]
        total_rels += count
        print(f"  [:{rel}]{' ' * max(1, 22 - len(rel))} {count:>4} edges")

    print(f"  {'─'*36}")
    print(f"  {'TOTAL':<22} {total_rels:>4} relationships")
    print("═" * 50)
    print()

    targets_met = total_nodes >= 50 and total_rels >= 100
    if targets_met:
        print("  ✅  Targets met: 50+ nodes, 100+ relationships, 8+ relationship types")
    else:
        print(f"  ⚠️   Check targets — nodes: {total_nodes} / 50, rels: {total_rels} / 100")
    print()


# ─────────────────────────────────────────────
# 6. Main entry point
# ─────────────────────────────────────────────

def main() -> None:
    # Validate CSV files exist
    for path in (PRODUCTION_CSV, WORKERS_CSV, CAPACITY_CSV):
        if not path.exists():
            print(f"ERROR: CSV not found: {path}", file=sys.stderr)
            sys.exit(1)

    # Load CSVs
    production_rows = load_csv(PRODUCTION_CSV)
    workers_rows    = load_csv(WORKERS_CSV)
    capacity_rows   = load_csv(CAPACITY_CSV)

    print(f"\nLoaded {len(production_rows)} production rows, "
          f"{len(workers_rows)} worker rows, "
          f"{len(capacity_rows)} capacity rows.\n")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as session:
        print("── Step 1: Constraints ──────────────────────")
        create_constraints(session)

        print("\n── Step 2: Weeks & Capacity Snapshots ───────")
        seed_weeks_and_snapshots(session, capacity_rows)

        print("\n── Step 3: Projects / Products / Stations / BOPs / ProductionEntries ──")
        seed_projects_products_stations_bops_entries(session, production_rows)

        print("\n── Step 4: Workers & Certifications ─────────")
        seed_workers_and_certs(session, workers_rows)

        print("\n── Step 5: Station → Certification requirements ──")
        seed_requires_cert(session)

        print_graph_summary(session)

    driver.close()
    print("Done. Graph is ready.")


if __name__ == "__main__":
    main()

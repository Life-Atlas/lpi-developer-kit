"""Page 7 — Self-Test (runs automatically, green/red checklist, score out of 20)"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import run_query, get_driver


def _check(label: str, passed: bool, points: int, detail: str = ""):
    icon = "✅" if passed else "❌"
    color = "#166534" if passed else "#7f1d1d"
    border = "#4ade80" if passed else "#ef4444"
    pts_earned = points if passed else 0
    st.markdown(
        f"""<div style="background:{color};border-left:4px solid {border};
        border-radius:8px;padding:12px 16px;margin-bottom:8px;">
        {icon} <b>{label}</b> &nbsp;
        <span style="float:right;background:{'#14532d' if passed else '#450a0a'};
        padding:2px 10px;border-radius:20px;font-size:0.8rem;">
        {pts_earned}/{points} pts</span>
        {'<br><span style="color:#cbd5e1;font-size:0.82rem;margin-top:4px;display:block;">'
         + detail + '</span>' if detail else ''}
        </div>""",
        unsafe_allow_html=True,
    )
    return pts_earned


def render():
    st.title("✅ Self-Test")
    st.markdown("Automated graph validation — 6 checks, 20 points total. Runs on every page load.")

    total = 0
    max_score = 20

    # ── Check 1: Neo4j connection alive (3 pts) ────────────────────────────────
    try:
        driver = get_driver()
        driver.verify_connectivity()
        total += _check("Check 1 — Neo4j connection alive", True, 3, "Connected successfully.")
    except Exception as e:
        _check("Check 1 — Neo4j connection alive", False, 3, str(e))

    # ── Check 2: node count ≥ 50 (3 pts) ──────────────────────────────────────
    try:
        res = run_query("MATCH (n) RETURN count(n) AS cnt")
        node_count = res[0]["cnt"] if res else 0
        passed = node_count >= 50
        total += _check(
            "Check 2 — Node count ≥ 50", passed, 3,
            f"Found {node_count} nodes."
        )
    except Exception as e:
        _check("Check 2 — Node count ≥ 50", False, 3, str(e))

    # ── Check 3: relationship count ≥ 100 (3 pts) ─────────────────────────────
    try:
        res = run_query("MATCH ()-[r]->() RETURN count(r) AS cnt")
        rel_count = res[0]["cnt"] if res else 0
        passed = rel_count >= 100
        total += _check(
            "Check 3 — Relationship count ≥ 100", passed, 3,
            f"Found {rel_count} relationships."
        )
    except Exception as e:
        _check("Check 3 — Relationship count ≥ 100", False, 3, str(e))

    # ── Check 4: 6+ distinct node labels (3 pts) ──────────────────────────────
    try:
        res = run_query("CALL db.labels() YIELD label RETURN collect(label) AS labels")
        labels = res[0]["labels"] if res else []
        passed = len(labels) >= 6
        total += _check(
            "Check 4 — 6+ distinct node labels", passed, 3,
            f"Labels: {', '.join(sorted(labels))} ({len(labels)} total)"
        )
    except Exception as e:
        _check("Check 4 — 6+ distinct node labels", False, 3, str(e))

    # ── Check 5: 8+ distinct relationship types (3 pts) ───────────────────────
    try:
        res = run_query("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS rels")
        rels = res[0]["rels"] if res else []
        passed = len(rels) >= 8
        total += _check(
            "Check 5 — 8+ distinct relationship types", passed, 3,
            f"Types: {', '.join(sorted(rels))} ({len(rels)} total)"
        )
    except Exception as e:
        _check("Check 5 — 8+ distinct relationship types", False, 3, str(e))

    # ── Check 6: Bottleneck query returns results (5 pts) ─────────────────────
    BOTTLENECK_CYPHER = """
MATCH (p:Project)-[:HAS_WORKORDER]->(wo:WorkOrder)-[:AT_STATION]->(s:Station)
WHERE wo.actual_hours > wo.planned_hours * 1.1
RETURN p.project_name AS project, s.station_name AS station,
       wo.planned_hours AS planned, wo.actual_hours AS actual
LIMIT 10
"""
    try:
        res = run_query(BOTTLENECK_CYPHER)
        passed = len(res) > 0
        detail_lines = []
        for r in res[:5]:
            detail_lines.append(
                f"• {r['project']} @ {r['station']} — "
                f"planned {r['planned']:.0f}h actual {r['actual']:.0f}h"
            )
        detail = f"Returned {len(res)} bottleneck work orders.<br>" + "<br>".join(detail_lines)
        total += _check(
            "Check 6 — Bottleneck query (actual > planned × 1.1)", passed, 5,
            detail if passed else "Query returned 0 rows — no bottlenecks found or query mismatch."
        )
    except Exception as e:
        _check("Check 6 — Bottleneck query (actual > planned × 1.1)", False, 5, str(e))

    # ── Score summary ──────────────────────────────────────────────────────────
    st.markdown("---")
    pct = int(total / max_score * 100)
    score_color = "#4ade80" if pct >= 80 else ("#facc15" if pct >= 50 else "#ef4444")
    grade = "A" if pct >= 90 else ("B" if pct >= 75 else ("C" if pct >= 50 else "F"))

    st.markdown(
        f"""<div style="text-align:center;padding:32px;background:linear-gradient(135deg,#1e2235,#252a3f);
        border-radius:16px;border:1px solid #2d3454;margin-top:16px;">
        <div style="font-size:4rem;font-weight:800;color:{score_color};">{total} / {max_score}</div>
        <div style="font-size:1.4rem;color:#94a3b8;margin-top:8px;">Grade: <b style="color:{score_color};">{grade}</b> ({pct}%)</div>
        </div>""",
        unsafe_allow_html=True,
    )

    if total == max_score:
        st.balloons()
        st.success("🎉 Perfect score! All checks passed.")
    elif total >= 14:
        st.info(f"Good — {total}/{max_score} points. Fix failing checks to reach 100%.")
    else:
        st.error(f"Only {total}/{max_score} points. Run seed_graph.py and verify your Neo4j connection.")

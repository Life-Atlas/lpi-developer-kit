# HOW_I_DID_IT — Level 5 Knowledge Graph Foundations

## Ankit Kumar Singh — ankitsinghh007

## Step 1 — Understanding the Challenge

I first read the Level 5 instructions carefully to understand what the challenge was actually testing. Initially I thought it was mainly about Neo4j syntax or writing Cypher queries, but after reading the requirements multiple times I understood that the real goal was graph thinking — modeling a factory as a connected operational system instead of treating it as disconnected tables.

The challenge provided three datasets:

* `factory_production.csv`
* `factory_workers.csv`
* `factory_capacity.csv`

I explored the datasets to understand:

* how projects move through stations,
* how workers relate to stations,
* how capacity deficits appear across weeks,
* and how bottlenecks emerge operationally.

Instead of jumping directly into coding, I spent time identifying relationships and dependencies inside the data.

---

## Step 2 — Designing the Graph Schema

After understanding the datasets, I started designing the graph schema.

I identified the main entities in the system:

* Project
* Product
* Station
* Worker
* Week
* Capacity
* Certification
* Etapp
* Bottleneck

The difficult part was deciding what should be modeled as:

* a node,
* a relationship,
* or a relationship property.

One important design choice I made was placing operational values like:

* planned hours,
* actual hours,
* completed units,
* variance percentage

inside the `SCHEDULED_AT` relationship instead of directly on nodes.

I chose this because the operational data describes the interaction between a project and a station during a specific week, not the project or station independently.

This helped me better understand how graph databases model behavior and interactions instead of only storing isolated records.

---

## Step 3 — Thinking Beyond Tables

One of the biggest mindset shifts during this challenge was learning to think in graphs instead of relational tables.

At first I naturally started thinking in SQL terms:

* joins,
* rows,
* filtering tables,
* and aggregations.

But while designing the schema I realized factories are highly interconnected systems:

* workers cover multiple stations,
* stations affect multiple projects,
* projects overload shared resources,
* and capacity problems propagate through the network.

That made graph modeling feel much more natural.

The SQL vs Cypher comparison section helped me understand this deeply. In SQL, solving operational dependency problems often requires several joins and complicated filtering logic. In Cypher, the query follows the actual shape of the system directly through relationships.

That was probably the biggest conceptual lesson from Level 5.

---

## Step 4 — Identifying Bottlenecks

While analyzing the production and capacity datasets, I noticed some stations repeatedly exceeded planned hours.

The most overloaded stations were:

* Station 014 (`Svets o montage`)
* Station 016 (`Gjutning`)

These stations were being overloaded by multiple projects during the same weeks.

Instead of modeling bottlenecks as just a numeric property, I decided to represent bottlenecks as graph entities because they emerge from multiple operational relationships together.

This helped me understand how graphs can represent system-level events and not just raw data rows.

I also experimented with Cypher logic for detecting overload conditions dynamically using variance percentages and grouped station analysis.

---

## Step 5 — Hybrid Graph + Vector Thinking

Another part I found interesting was combining graph reasoning with vector similarity.

Instead of embedding raw CSV rows, I thought about embedding:

* project descriptions,
* operational characteristics,
* station footprints,
* and worker skill profiles.

Then the graph structure could be used to:

* validate operational similarity,
* filter reachable matches,
* and identify projects with historically low variance.

This helped me understand the difference between:

* semantic similarity (vectors)
  and
* structural relationships (graphs).

It also gave me a better understanding of how modern AI systems combine vector search and graph traversal together.

---

## Step 6 — Planning Level 6

While writing the Level 5 answers, I also started planning the Level 6 implementation.

I designed:

* node mappings,
* relationship mappings,
* dashboard panels,
* heatmaps,
* bottleneck analysis,
* and worker coverage visualizations.

This planning stage made the later Neo4j setup much easier because I already understood the structure of the system before implementing it.

---

## Problems I Faced

Some challenges I faced were:

### 1. Deciding What Belongs on Nodes vs Relationships

Initially I kept trying to place operational metrics directly on nodes, but later I realized many values describe interactions between entities instead of the entities themselves.

### 2. Thinking in Graphs Instead of SQL

I was more familiar with relational thinking initially, so learning to think in traversals and connected relationships took time.

### 3. Understanding Operational Relationships

The manufacturing dataset was more complex than it first looked. I had to carefully trace how projects, stations, workers, and capacity influence each other operationally.

### 4. Bottleneck Modeling

Representing bottlenecks properly was difficult because they are not isolated records — they emerge from multiple overloaded relationships together.

---

## What I Learned

Through this challenge I learned:

* how Neo4j models connected systems,
* how Cypher differs from SQL,
* how graph traversal simplifies operational dependency analysis,
* how bottlenecks can be represented as graph entities,
* and how vector search and knowledge graphs can complement each other in AI systems.

I also learned how digital twin systems rely heavily on connected operational reasoning instead of isolated analytics.

This challenge changed the way I think about industrial data systems and operational intelligence.

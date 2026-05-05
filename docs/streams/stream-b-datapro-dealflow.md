# Stream B — DataPro+ DealFlow Platform

**Customer:** Josh Young (DataProPlus / EnergyJobline, UK)  
**Repos:** `LifeAtlas/datacenter-flow` (frontend) + `LifeAtlas/DataCenterBackend` (backend)  
**Team Size:** 13 interns  
**Duration:** May 16 – June 27, 2026

---

## Background

### The Problem

The global datacenter market is exploding — driven by AI, cloud computing, and data sovereignty requirements. But the **deal-making process** for datacenter capacity, land, and investment is stuck in the 1990s:

- Opportunities circulate via email, WhatsApp, and spreadsheets
- There's no central platform where buyers and sellers can discover each other
- Sensitive site data (exact location, power contracts, pricing) must be controlled — you can't just put it on a website
- Brokers like Josh manually coordinate introductions between parties
- Due diligence documents are shared as email attachments with no tracking

**Nothing like this exists.** The incumbents (CoStar, CBRE) focus on traditional real estate. Nobody has built a purpose-built datacenter dealflow platform with gated access and digital twin visualization.

### The Opportunity

Josh Young has been brokering datacenter deals across Europe, Middle East, and Asia for years. He has:
- **Live opportunities ready to list** (sites in UK, Nordics, Middle East)
- **A network of buyers** (hyperscalers, colocation providers, investors)
- **A proven revenue model**: introduction fees of 1-3% per deal (deals range EUR 500K to multi-million)

One successful deal through the platform pays for everything.

### What Already Exists

Daniel W built an initial demo at `datacenter-flow.netlify.app` in late 2025. It shows:
- A map-based interface for browsing datacenter opportunities
- Deal cards with key parameters (MW, location, status)
- Basic investor view

The codebase is clean: React 19 + Vite 6 + Tailwind, ~6K lines, 60 files. **You can read all of it on day 1.**

### What Actually Exists (Honest Audit — May 6, 2026)

**Frontend (`datacenter-flow`) — Solid browsing shell, ~70% of UI:**
- Supabase auth fully wired (AuthContext, session management, signOut)
- Real data loading from Supabase (deals + 7 related tables: deal_power, deal_land, deal_permits, deal_funding, deal_offtake, deal_specs, documents)
- Deal CRUD in deal-service.ts (create with all nested parameters)
- HomePage: category/region/stage filtering, search, sort, deal cards
- DealPage: detailed view with all parameter sections
- MapPage: Leaflet map with deal locations
- InvestorPage: investor-facing view
- DealEditForm: admin can add/edit deals
- LockedContent component: blur effect + lock overlay — but **FAKE unlock** (setTimeout, not real access control)
- ShareConfigModal: sharing with visibility controls
- Rich TypeScript types: 15+ interfaces for deal parameters

**Backend (`DataCenterBackend`) — Almost nothing:**
- Single endpoint: `POST /extract-data` → uploads PDFs to Gemini for structured extraction
- Rich Pydantic schema (17 nested models matching frontend types)
- No CRUD endpoints, no auth, no database connection, no user management
- CORS wide open (`allow_origins=["*"]`)

**What's NOT built (the 90% that matters for Josh):**
- Real 3-layer access control (LockedContent is cosmetic only)
- NDA workflow (no signing, no tracking, no per-opportunity access)
- Admin panel (no user approval, no engagement tracking)
- Lead capture ("Request More Info" → email to Josh)
- User tracking (IP/session/activity)
- Link sharing prevention
- Referral/introduction layer
- Backend API for any of the above
- Supabase RLS policies
- No Supabase project currently connected (env vars needed)

**Last pushed: January 9, 2026 — 4 months stale.**

---

## The 3-Layer Information Control Model

This is the core innovation. Every opportunity has three layers of visibility:

### Layer 1 — Public Teaser
Anyone can see: country/region, approximate MW capacity, power status, planning stage, infrastructure overview. **No exact location. No pricing. No owner identity.**

Purpose: attract interest, let buyers browse and filter.

### Layer 2 — After NDA
After a user creates an account and signs a digital NDA, they unlock: detailed site intelligence, media packs, technical documents, financial summaries.

Purpose: serious buyers can evaluate the opportunity before committing to an introduction.

### Layer 3 — After Approval
Josh (the platform operator) manually approves a buyer for a specific opportunity. They then get: exact location, direct introduction to the site owner, meeting coordination.

Purpose: protect the deal. Josh earns his introduction fee at this stage.

### Why This Matters Architecturally

This isn't a simple CRUD app. You're building:
- **Role-based access control** (viewer → registered → NDA-signed → approved)
- **Per-opportunity permissions** (approved for Site A doesn't mean approved for Site B)
- **Audit trail** (who viewed what, when, from where)
- **Document management** with access tiers
- **Lead qualification workflow** for the platform operator

---

## Three Opportunity Categories

| Category | What | Key Fields |
|----------|------|------------|
| **A: Capacity Leasing** | Existing datacenter with MW available | Location (city-level), MW available, power source, PUE, connectivity, timeline |
| **B: Land / Powered Land** | Sites suitable for new builds | Acreage, power availability, planning status, distance to fiber/substation |
| **C: Investment / JV** | Projects seeking capital or partners | Capital required, project stage, expected ROI, partner requirements |

---

## Week 0 — This Week (May 6-13): Study + L5/L6

This week you're doing L5/L6 (individual LPI challenges) AND studying up on DataPro+.

### Required Reading (before May 16)
1. **Clone both repos** and run the frontend locally
2. **Read every file in `src/types/deal.ts`** — understand the data model
3. **Read `src/lib/deal-service.ts`** — understand the Supabase integration
4. **Read `src/components/deals/LockedContent.tsx`** — understand the current (fake) access control
5. **Read the backend `schemas.py`** — understand the Pydantic model
6. **Read this entire document** — understand Josh's vision and the business model

### Questions to Answer (bring to first standup May 16)
1. What tables does the frontend expect in Supabase? (hint: look at deal-service.ts)
2. What's the gap between LockedContent.tsx and Josh's 3-layer access model?
3. How would you implement "Request More Info" → lead capture → email to Josh?
4. What's missing from the backend to support the frontend's needs?

---

## Your Mission (8 Weeks, starting May 16)

Transform the existing demo into a **production gated marketplace** that Josh can use to list real opportunities and manage real buyer relationships.

**What you're inheriting:** A working browsing UI with Supabase auth, deal CRUD, maps, and filtering. The frontend is ~70% done for browsing. What's missing is everything that makes it a CONTROLLED platform — access control, NDA, lead capture, admin panel, and backend APIs.

### Week 1-2: Real Access Control + Backend
- Set up NEW Supabase project for DataPro+
- Migrate schema from frontend types → real tables with RLS
- Replace fake LockedContent with real per-user, per-opportunity access tiers
- Build "Request More Info" → account creation → lead capture
- Backend: user CRUD, opportunity CRUD, role management endpoints

### Week 3-4: NDA + Admin Panel
- Digital NDA signing workflow (in-platform, stored per user + per opportunity)
- Admin panel: approve/reject users, manage opportunities, track engagement
- Email notifications to Josh on new leads
- Per-opportunity approval system (approved for Site A ≠ approved for Site B)

### Week 5-6: Intelligence + Referral Layer
- Improve Gemini PDF extraction pipeline (backend already has the endpoint)
- Auto-categorize opportunities (A: Capacity / B: Land / C: Investment)
- "Make an Introduction" referral workflow (Josh's May 4 feature request)
- Referral tracking (who referred whom, deal linkage)

### Week 7-8: Polish + Launch
- Security hardening (IP tracking, session monitoring, link sharing prevention)
- Mobile responsive pass
- Digital twin visualization (3D site viewer — the USP)
- **Goal: Josh lists first real opportunity**

---

## The Future

DataPro+ DealFlow is the first vertical on the Life Atlas platform. The pattern you're building — **gated marketplace + knowledge graph + digital twin** — applies to:

- **Energy infrastructure** (solar farms, wind, grid connections)
- **Manufacturing facilities** (factory capacity, equipment, workforce)
- **Real estate development** (commercial, industrial, mixed-use)
- **Any asset class** where deals require controlled access, due diligence, and broker-mediated introductions

The datacenter market is the beachhead. If this works, the platform scales to every asset class where information asymmetry is the business model.

### Technology Vision

What you build here connects to the broader Life Atlas architecture:

- **Knowledge Graph (Neo4j)** — relationships between sites, buyers, sellers, deals, documents, capabilities. Not just a database of listings — a graph of the entire market.
- **Vector Search (Qdrant)** — "Find sites similar to this one" using embeddings of site descriptions, specs, and documents. Buyer profiles matched to relevant opportunities.
- **Digital Twin** — 3D visualization of datacenter sites (power infrastructure, cooling, connectivity, expansion potential). This is the USP that no competitor has.
- **LPI (Life Programmable Interface)** — every query goes through Life Atlas's sovereign consultation layer. Rate limiting, access control, audit logging, and AI guardrails baked in.

### Revenue Projections

| Revenue Stream | Per-Deal / Per-Month | Notes |
|----------------|---------------------|-------|
| Introduction fees | 1-3% of deal value | EUR 500K – multi-million per deal |
| Listing fees | Per opportunity | Site owners pay to list |
| Subscription | $10K/month | For brokers, developers, hyperscalers |
| Data intelligence | Per report | Market analysis, site comparison |

**The goal is that one deal funds the platform.** Everything after that is margin.

---

## Phase 2: Referral / Introduction Layer (May 4, 2026)

Josh's latest feature request — a network-powered deal sourcing engine:

### Concept
Allow trusted individuals to **introduce buyers or opportunities** to the platform. In return, they participate in a share of the success fee if a deal completes.

### Key Principles
- This is NOT a public referral marketplace or contact database
- It IS controlled, private, curated, managed through Josh & Rich
- Everything still flows through the platform as the introducer
- Positioning: "Introduce relevant parties and participate in opportunities" (NOT "submit contacts and earn money")

### User Flow

**Refer a Buyer:**
1. User clicks "Make an Introduction"
2. Form: Name, Email, Company, Type (Buyer/Investor/Hyperscaler), Relationship level (Direct/Indirect), Free text context
3. Submission goes to admin (Josh) — NOT visible publicly
4. Josh reviews, qualifies, and if relevant: asks user to make proper introduction
5. Josh takes over the process, manages all communication

**Refer an Opportunity:**
Same flow but for Land / Power / Capacity / Investment opportunities.

### Fee Model
- Referrer receives a % of the deal fee
- Example: $100M deal, 1.5% fee ($1.5M), referrer gets 0.25–0.5% ($250K–$500K)
- Manual payouts initially — just tracking capability needed

### Inspiration
BountyHunter (bountyhunterworld.com) — Josh wants people to invest in sharing opportunities with their LinkedIn and personal networks in return for a slice of the fee.

### Why This Matters
This turns the platform from direct-outreach-only into a **network-powered dealflow engine**. Josh's observation: "Everyone I speak to says 'I know people' — this monetises that."

---

## Key Links

- **Existing demo:** datacenter-flow.netlify.app
- **Frontend repo:** github.com/LifeAtlas/datacenter-flow
- **Backend repo:** github.com/LifeAtlas/DataCenterBackend
- **Backend API:** dc-backend.lifeatlas.online

---

## What Makes This Real

This is not a school project. Josh has:
- Live opportunities waiting to list
- Buyers asking for a platform
- Revenue model validated through years of manual brokering
- 5+ high-level datacenter contacts who confirmed "nothing like this exists"

Your code will serve real users, process real deals, and generate real revenue. Treat it accordingly.

# 🕵️‍♂️ NODE-VALIDATOR SWARM | INVISIBLE OPERATIONS

> **Status:** Operational | **Reality Bridge:** Active | **Protocol:** Node-Validator-V1

The **Node-Validator Swarm** is a professional-grade, autonomous lead generation engine designed for high-scale, decentralized data extraction. Operating under the **Invisible Operations** framework, this system utilizes a "Reality Bridge" to bridge decentralized node identifiers with real-world business data.

## 🚀 Core Features

- **Autonomous Swarm Engine**: Scrapes business leads (Roofers, Plumbers, HVAC) across the Top 50 US Cities.
- **Deep-Scrape Logic**: 3-page search depth per query using Playwright and Chromium.
- **Reality Bridge Integration**: Uses `OPERATOR_NODE_ID` for fuel and `COLLECTOR_NODE_ID` for results destination.
- **Dynamic Scaling**: Adjusts operation speed based on node activity and budget.
- **Live Dashboard**: Real-time counter of "TOTAL VALIDATED LEADS" and "NEXT BATCH" progress.
- **Self-Healing**: Automated error catching and manual takeover protocol for CAPTCHAs.

## 🛠️ Deployment Configuration

The system is optimized for **Railway** deployment using Nixpacks for automated environment setup.

### Required Environment Variables

| Variable | Description |
| :--- | :--- |
| `OPERATOR_NODE_ID` | The Solana wallet ID fueling the swarm's operations. |
| `COLLECTOR_NODE_ID` | The Solana wallet ID receiving the validated results. |
| `REDIS_URL` | Redis connection string for state management. |
| `PORT` | The internal server port (default: 5000). |

## 🕹️ Operational Commands

Once the server is **Active**, use the dashboard chat to send commands:

- `/start-swarm`: Initiates the Reality Bridge and begins autonomous scraping.
- `/set-operator <ID>`: Updates the Operator Node fueling the swarm.

## 🔒 Security Protocol

- **Zero-Key Exposure**: All sensitive identifiers are handled via environment variables.
- **Stealth Scrapes**: Uses Playwright for high-fidelity, human-like data extraction.
- **Isolated State**: Powered by Redis for ultra-stable, multi-threaded operations.

---
*Developed under the BMBB Hyper-Scale Initiative.*
# Triggering deployment for Render Background Worker

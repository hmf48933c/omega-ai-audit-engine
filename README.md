# TTB Alcohol Label Verification Assistant

A dual-track application repository designed to assist TTB Compliance Agents in verifying alcohol label requirements using Optical Character Recognition (OCR). 

## V1: Live Rapid Prototype (Streamlit)
Built to immediately address stakeholder requests for batch uploads and simple UI, while utilizing local Tesseract OCR to comply with strict federal outbound firewall constraints.
* **Live Prototype URL:** https://omega-ai-audit-engine-3zzrfffmhfswutzlqdjngk.streamlit.app/

## V2: Production Enterprise Architecture (Azure/Docker Ready)
Located in this repository (`/backend` and `docker-compose.yml`), this represents the decoupled modernization blueprint for a fully funded deployment:
* **Frontend:** React/TailwindCSS UI (Decoupled).
* **Backend:** Asynchronous Python FastAPI (`backend/main.py`) for high-volume batch processing.
* **Intelligent Comparison Engine:** Implements fuzzy matching (Levenshtein distance) for brand names to reduce false positives (e.g., "STONE'S THROW" vs "Stone's Throw"), while enforcing strict case-sensitive matching for the legal Government Warning.
* **Security & Infrastructure:** Fully containerized via Docker for seamless deployment to Azure App Services (FedRAMP Authorized). Completely stateless processing with zero database retention to ensure strict federal compliance.

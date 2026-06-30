# TTB Alcohol Label Verification Assistant - Prototype for Treasury Take-Home Assessment

A prototype application designed to assist TTB Compliance Agents in verifying alcohol label requirements using Optical Character Recognition (OCR).

## Deployed Application
* **Live Prototype URL:** https://omega-ai-audit-engine-3zzrfffmhfswutzlqdjngk.streamlit.app/

## Tech Stack & Architecture
* **Frontend/UI:** Streamlit
* **OCR Engine:** Tesseract OCR (`pytesseract`)
* **Image Processing:** `Pillow`

## Setup and Run Instructions (Local)
1. Ensure system dependencies are installed (requires `tesseract-ocr` on the host machine).
2. Install Python dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run app.py`

## Approach, Tools, & Assumptions
* **Approach:** Built a lightweight, fast web interface focusing on stakeholder requests: processing under 5 seconds, batch upload capabilities, and strict case-sensitive compliance checking.
* **Tools Used:** Streamlit was chosen for rapid UI prototyping and native batch-upload handling. Tesseract OCR was selected for fast, local text extraction without relying on external cloud APIs (addressing stakeholder firewall concerns).
* **Assumptions Made:** Assumes uploaded images are of sufficient quality and lighting for standard OCR extraction. The warning statement check assumes "GOVERNMENT WARNING" must be an exact, all-caps match to pass validation.

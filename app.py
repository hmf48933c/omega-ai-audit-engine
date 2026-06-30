import streamlit as st
import pytesseract
from PIL import Image

# COPYRIGHT © 2026 HARSHAD NAGINDAS MEHTA. ALL RIGHTS RESERVED.
# Prototype developed for Treasury IT Specialist (AI) Evaluation

st.set_page_config(page_title="TTB Label AI", page_icon="🍾", layout="wide")
st.title("🍾 TTB Alcohol Label Verification Assistant")
st.markdown("---")

st.info("Designed for Compliance Agents: Fast OCR verification, simple interface, and full batch upload support.")

# Addresses stakeholder request for batch processing
uploaded_files = st.file_uploader("Upload Label Images (Supports Single or Batch Processing)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    if st.button("🚀 Run AI Verification"):
        for file in uploaded_files:
            st.subheader(f"Verification Results: {file.name}")
            with st.spinner(f"Running Optical Character Recognition on {file.name}..."):
                try:
                    # Open the image and extract text using Tesseract OCR
                    image = Image.open(file)
                    extracted_text = pytesseract.image_to_string(image)
                    
                    st.write("**Compliance Check Summary:**")
                    
                    # Case-sensitive check based on Junior Agent Jenny Park's specific requirement
                    if "GOVERNMENT WARNING" in extracted_text:
                        st.success("✅ **Warning Statement:** Match (ALL CAPS verified)")
                    elif "Government Warning" in extracted_text or "government warning" in extracted_text.lower():
                        st.error("⚠️ **WARNING STATEMENT MISMATCH:** The label uses incorrect casing. TTB guidelines mandate that 'GOVERNMENT WARNING' must be formatted in ALL CAPS and bold.")
                    else:
                        st.warning("⚠️ **Warning Statement:** Not automatically detected. Manual review required.")
                        
                    with st.expander("View Raw OCR Extraction Data"):
                        st.text(extracted_text)
                        
                except Exception as e:
                    st.error(f"Error processing image {file.name}: {str(e)}")
                    
        st.success(f"Successfully processed {len(uploaded_files)} application(s).")

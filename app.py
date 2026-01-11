#!/usr/bin/env python3
"""
KYC Identity Verification System - Web UI
Streamlit-based interface with Swiss Design aesthetic
"""
import streamlit as st
import os
from pathlib import Path
import tempfile
import json
import hashlib
from io import BytesIO
from PIL import Image

from src.identity_extractor import IdentityExtractor
from src.output_formatter import OutputFormatter
from src.validator import IdentityValidator
from src.duplicate_checker import DuplicateChecker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="KYC Identity Verification",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Clean Light Theme with Great Wave of Kanagawa Background
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');

    /* Reset and Base */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Icon styling */
    .material-symbols-rounded {
        font-family: 'Material Symbols Rounded';
        font-weight: normal;
        font-style: normal;
        font-size: 1.1rem;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        vertical-align: middle;
        position: relative;
        top: -1px;
    }
    
    /* Smaller icon for badges/buttons */
    .icon-sm {
        font-size: 0.9rem !important;
        margin-right: 4px;
    }
    
    .icon-lg {
        font-size: 1.5rem !important;
        margin-right: 8px;
    }


    /* Great Wave Background - Subtle/Almost Transparent */
    .main, .stApp, [data-testid="stAppViewContainer"] {
        background: 
            linear-gradient(
                135deg, 
                rgba(255, 255, 255, 0.96) 0%, 
                rgba(248, 250, 252, 0.95) 50%,
                rgba(240, 245, 250, 0.97) 100%
            ),
            url('https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Tsunami_by_hokusai_19th_century.jpg/2560px-Tsunami_by_hokusai_19th_century.jpg') !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
        color: #1A1A1A !important;
    }

    [data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px);
    }

    /* Reduce overall padding */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 1200px !important;
    }

    /* Typography */
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: -0.02em;
        color: #1A1A1A !important;
        margin-bottom: 0.5rem !important;
    }

    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1A365D !important;
        margin-bottom: 0.25rem !important;
        letter-spacing: -0.03em;
    }

    .sub-header {
        font-size: 0.9rem;
        color: #4A5568 !important;
        font-weight: 400;
        margin-bottom: 1.5rem !important;
    }

    /* Glassmorphism Cards */
    .swiss-card {
        background: rgba(255, 255, 255, 0.75) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.5);
        padding: 1rem 1.25rem;
        border-radius: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }

    .swiss-card:hover {
        background: rgba(255, 255, 255, 0.85) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
    }

    /* Result Card */
    .result-card {
        background: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.6);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.75rem;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        border-radius: 20px;
    }

    .status-success {
        background: linear-gradient(135deg, #48BB78 0%, #38A169 100%);
        color: #FFFFFF;
        box-shadow: 0 2px 8px rgba(72, 187, 120, 0.3);
    }

    .status-warning {
        background: linear-gradient(135deg, #ED8936 0%, #DD6B20 100%);
        color: #FFFFFF;
        box-shadow: 0 2px 8px rgba(237, 137, 54, 0.3);
    }

    .status-error {
        background: linear-gradient(135deg, #FC8181 0%, #F56565 100%);
        color: #FFFFFF;
        box-shadow: 0 2px 8px rgba(252, 129, 129, 0.3);
    }

    .status-pending {
        background: linear-gradient(135deg, #4299E1 0%, #3182CE 100%);
        color: #FFFFFF;
        box-shadow: 0 2px 8px rgba(66, 153, 225, 0.3);
    }

    /* Info boxes with glass effect */
    .info-box {
        background: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-left: 4px solid #3182CE;
        padding: 0.75rem 1rem;
        margin: 0.75rem 0;
        border-radius: 0 12px 12px 0;
        font-size: 0.875rem;
        backdrop-filter: blur(5px);
    }

    .info-box-success {
        border-left-color: #48BB78;
        background: rgba(240, 255, 244, 0.8);
    }

    .info-box-warning {
        border-left-color: #ED8936;
        background: rgba(255, 250, 240, 0.8);
    }

    .info-box-error {
        border-left-color: #F56565;
        background: rgba(255, 245, 245, 0.8);
    }

    .info-box-duplicate {
        border-left-color: #805AD5;
        background: rgba(250, 245, 255, 0.8);
    }

    /* Buttons - Japanese wave inspired blue */
    .stButton>button {
        background: linear-gradient(135deg, #2B6CB0 0%, #1A365D 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        border: none !important;
        border-radius: 12px;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        font-size: 0.75rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(43, 108, 176, 0.3);
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(43, 108, 176, 0.4);
    }

    .stButton>button:active {
        transform: translateY(0);
    }

    /* Sidebar styling - fixed height, no scroll */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.92) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(0, 0, 0, 0.08);
    }

    section[data-testid="stSidebar"] > div:first-child {
        overflow: visible !important;
        height: auto !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        overflow: visible !important;
    }

    /* Prevent sidebar scroll */
    [data-testid="stSidebarContent"] {
        overflow: visible !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-size: 0.75rem !important;
        color: #2D3748 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    section[data-testid="stSidebar"] .stMarkdown p {
        color: #4A5568 !important;
    }

    /* Metrics with glass effect */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.75);
        padding: 1rem;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }

    [data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        font-weight: 700;
        color: #1A365D !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        color: #4A5568 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.6);
        padding: 0.5rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }

    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.25rem;
        color: #4A5568 !important;
        font-weight: 500;
        font-size: 0.85rem;
        border-radius: 12px;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2B6CB0 0%, #1A365D 100%) !important;
        color: #FFFFFF !important;
    }

    /* Divider */
    hr {
        border: none;
        border-top: 1px solid rgba(0, 0, 0, 0.08);
        margin: 1rem 0;
    }

    /* Data display */
    .data-label {
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #718096;
        margin-bottom: 0.25rem;
    }

    .data-value {
        font-size: 0.95rem;
        font-weight: 500;
        color: #1A202C;
        margin-bottom: 0.75rem;
        line-height: 1.4;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed rgba(43, 108, 176, 0.3) !important;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        background: rgba(255, 255, 255, 0.5) !important;
    }

    [data-testid="stFileUploader"] section {
        background: transparent !important;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: rgba(43, 108, 176, 0.6) !important;
        background: rgba(255, 255, 255, 0.7) !important;
    }

    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] p {
        color: #4A5568 !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.7) !important;
        border-radius: 12px !important;
        font-size: 0.9rem !important;
        padding: 0.75rem 1rem !important;
        color: #2D3748 !important;
        border: 1px solid rgba(0, 0, 0, 0.08) !important;
    }

    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.85) !important;
    }

    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.6) !important;
        border: 1px solid rgba(0, 0, 0, 0.05) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        backdrop-filter: blur(10px);
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(135deg, #2B6CB0 0%, #1A365D 100%) !important;
        border-radius: 10px;
    }

    /* Input fields */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background: rgba(255, 255, 255, 0.8) !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 10px !important;
        color: #1A202C !important;
        padding: 0.6rem 1rem !important;
    }

    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: rgba(43, 108, 176, 0.5) !important;
        box-shadow: 0 0 0 2px rgba(43, 108, 176, 0.1) !important;
    }

    /* Checkbox styling */
    .stCheckbox label span {
        color: #4A5568 !important;
    }

    /* Download button */
    .stDownloadButton button {
        background: rgba(255, 255, 255, 0.7) !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        color: #2D3748 !important;
    }

    .stDownloadButton button:hover {
        background: rgba(255, 255, 255, 0.9) !important;
        border-color: rgba(43, 108, 176, 0.5) !important;
    }

    /* JSON display */
    .stJson {
        background: rgba(255, 255, 255, 0.7) !important;
        border-radius: 12px !important;
        max-height: 250px;
        overflow-y: auto;
    }

    /* Images with rounded corners */
    .stImage img {
        border-radius: 12px;
        border: 1px solid rgba(0, 0, 0, 0.08);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    /* Caption text */
    .stImage figcaption, .stCaption {
        color: #718096 !important;
        font-size: 0.75rem !important;
    }

    /* Table styling */
    table {
        background: rgba(255, 255, 255, 0.6) !important;
        border-radius: 8px;
    }
    
    th {
        color: #4A5568 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.7rem !important;
        letter-spacing: 0.05em;
        background: rgba(255, 255, 255, 0.5) !important;
    }
    
    td {
        color: #1A202C !important;
        border-color: rgba(0, 0, 0, 0.05) !important;
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(43, 108, 176, 0.3);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(43, 108, 176, 0.5);
    }

    /* Reduce element margins */
    .element-container {
        margin-bottom: 0.5rem !important;
    }

    /* Alerts */
    .stAlert {
        background: rgba(255, 255, 255, 0.75) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(0, 0, 0, 0.08) !important;
        backdrop-filter: blur(10px);
    }

    /* Success message styling */
    .stSuccess {
        background: rgba(240, 255, 244, 0.8) !important;
    }

    /* Error message styling */  
    .stError {
        background: rgba(255, 245, 245, 0.8) !important;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'duplicate_checker' not in st.session_state:
        st.session_state.duplicate_checker = DuplicateChecker()
    # Store current verification result to persist across reruns (single doc mode)
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None
    if 'current_validation_errors' not in st.session_state:
        st.session_state.current_validation_errors = None
    if 'current_image_bytes' not in st.session_state:
        st.session_state.current_image_bytes = None
    if 'current_duplicate_info' not in st.session_state:
        st.session_state.current_duplicate_info = None
    if 'current_filename' not in st.session_state:
        st.session_state.current_filename = None
    # Uploader key counter - increment to reset file uploader
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 0
    # Batch processing results
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = []
    # Track approved items in batch mode (by index)
    if 'approved_items' not in st.session_state:
        st.session_state.approved_items = set()
    # Batch errors and duplicates
    if 'batch_errors' not in st.session_state:
        st.session_state.batch_errors = []
    if 'batch_duplicates' not in st.session_state:
        st.session_state.batch_duplicates = []


def check_api_key():
    """Check if API key is configured or prompt user via terminal."""
    api_key = os.getenv("FIREWORKS_API_KEY")
    
    # Check if key is missing, empty, or placeholder
    if not api_key or not api_key.strip() or "ENTER_PIHKey" in api_key or "your_api_key_here" in api_key:
        # Attempt to get from terminal input (useful for local dev)
        try:
            import getpass
            print("\n" + "!" * 50)
            print("FIREWORKS API KEY MISSING FROM .ENV")
            print("Please enter your API Key below to continue.")
            print("This will NOT be saved to disk (session only).")
            print("!" * 50)
            
            manual_key = getpass.getpass("Enter Fireworks API Key > ")
            
            if manual_key and manual_key.strip():
                os.environ["FIREWORKS_API_KEY"] = manual_key.strip()
                print("API Key accepted for this session.\n")
                return True
        except Exception as e:
            print(f"Could not prompt for API key: {e}")

        # If still invalid, show error in UI
        st.markdown('<div class="info-box info-box-error">', unsafe_allow_html=True)
        st.error("**API KEY REQUIRED** — Configure FIREWORKS_API_KEY in .env file or enter in terminal.")
        st.info("Get your key from https://fireworks.ai/")
        st.markdown('</div>', unsafe_allow_html=True)
        return False
    return True


def force_light_theme():
    """Legacy function - theme is now controlled via CSS."""
    pass  # Dark theme is now applied via CSS


def display_header():
    """Display the application header with icons."""
    col1, col2 = st.columns([1, 6])
    with col1:
        # Use a logo image or a large icon
        st.markdown('<div style="text-align: center; font-size: 3rem;"><span class="material-symbols-rounded" style="font-size: 3.5rem; color: #1A365D;">verified_user</span></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<h1 class="main-header">Identity Verification</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Secure KYC Document Processing & Validation</p>', unsafe_allow_html=True)


def display_sidebar():
    """Display the sidebar configuration and stats."""
    with st.sidebar:
        st.markdown("### <span class='material-symbols-rounded'>tune</span> Control Panel", unsafe_allow_html=True)
        
        # Configuration Group
        with st.expander("Configuration", expanded=True):
            # Model selection
            model_options = {
                "Qwen 3 VL 235B A22B (SOTA)": "accounts/fireworks/models/qwen3-vl-235b-a22b-instruct",
                "Qwen 3 VL 235B Thinking": "accounts/fireworks/models/qwen3-vl-235b-a22b-thinking",
                "Qwen 3 VL 30B A3B (Fast)": "accounts/fireworks/models/qwen3-vl-30b-a3b-instruct",
                "Qwen 3 VL 30B Thinking": "accounts/fireworks/models/qwen3-vl-30b-a3b-thinking",
                "Qwen 2.5 VL 32B (Balanced)": "accounts/fireworks/models/qwen2p5-vl-32b-instruct"
            }

            selected_model_name = st.selectbox(
                "AI Model",
                options=list(model_options.keys()),
                index=4,
                help="Select AI model functionality"
            )
            selected_model = model_options[selected_model_name]

            st.markdown("---")

            # Validation Rules
            c1, c2 = st.columns(2)
            with c1:
                check_expiry = st.checkbox("Expiry", value=True)
            with c2:
                check_duplicates = st.checkbox("Dups", value=True)

        if 'duplicate_checker' in st.session_state:
            if st.button("Reset History", use_container_width=True):
                st.session_state.duplicate_checker.clear_history()
                
                # Clear cached duplicate status in current results
                if 'batch_results' in st.session_state:
                    for item in st.session_state.batch_results:
                        item['duplicate_info'] = None
                
                st.session_state.current_duplicate_info = None
                st.session_state.approved_items = set()
                st.rerun()

        # System Info Expander
        with st.expander("Documentation", expanded=False):
            st.markdown("""
            **<span class='material-symbols-rounded icon-sm'>badge</span> Valid Types:**
            * Passports
            * Driver's Licenses
            * National ID Cards
            
            **<span class='material-symbols-rounded icon-sm'>image</span> Formats:** JPG, PNG (Max 10MB)
            """, unsafe_allow_html=True)

        st.caption("v2.1 © 2026 KYC System")

        return selected_model, check_expiry, check_duplicates


def process_document(uploaded_file, model, check_expiry, check_duplicates=True):
    """Process a single uploaded document with improved error handling."""
    try:
        # Get image bytes
        image_bytes = uploaded_file.getvalue()

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name

        # Initialize extractor
        extractor = IdentityExtractor(model=model)

        # Extract identity information
        with st.spinner(f"Processing {uploaded_file.name}..."):
            result = extractor.verify_document(tmp_path)

        # Clean up temp file
        os.unlink(tmp_path)

        # Check if this is a valid ID document
        if not result.personal_info.full_name or result.personal_info.full_name.strip() == "":
            return None, None, None, {
                "type": "not_id",
                "message": "Could not extract identity information. This may not be a valid ID document."
            }

        # Check if document type is valid
        if result.document_info.document_type == "unknown":
            # Check if we have minimal required info
            if not result.document_info.document_number and not result.personal_info.date_of_birth:
                return None, None, None, {
                    "type": "not_id",
                    "message": "This image does not appear to be a supported identity document (Passport, Driver's License, or National ID)."
                }

        # Check for duplicate IDENTITY (not image) AFTER extraction
        # This uses name, DOB, and document number to detect true duplicates
        duplicate_info = None
        if check_duplicates and 'duplicate_checker' in st.session_state:
            checker = st.session_state.duplicate_checker
            is_duplicate, existing_record = checker.check_duplicate(result)
            if is_duplicate:
                duplicate_info = {
                    "type": "identity_duplicate",
                    "match_type": "identity",
                    "record": existing_record
                }
            else:
                # Also check for similar identities (partial matches)
                similar = checker.find_similar(result, threshold=0.85)
                if similar:
                    duplicate_info = {
                        "type": "similar_identity",
                        "match_type": "similar",
                        "records": similar[:3]  # Top 3 matches
                    }

        # Validate
        validation_errors = IdentityValidator.validate_result(
            result,
            min_age=0,
            check_expiry=check_expiry
        )

        return result, validation_errors, image_bytes, duplicate_info

    except Exception as e:
        error_msg = str(e)
        # Provide more helpful error messages
        if "400" in error_msg:
            return None, None, None, {
                "type": "api_error",
                "message": "The AI model could not process this image. Please ensure it's a clear photo of an ID document."
            }
        elif "timeout" in error_msg.lower():
            return None, None, None, {
                "type": "timeout",
                "message": "Processing took too long. Please try again with a smaller or clearer image."
            }
        else:
            return None, None, None, {
                "type": "error",
                "message": error_msg
            }


@st.dialog("Document Preview")
def view_document_modal(image_bytes, filename):
    try:
        img = Image.open(BytesIO(image_bytes))
        w, h = img.size
        # Smart resizing: Enlarge if width < 800px, otherwise keep natural size (which typically fits container anyway)
        use_full_width = w < 800
        st.image(img, caption=f"{filename} ({w}x{h})", use_container_width=use_full_width)
    except Exception as e:
        st.error(f"Could not load image preview: {e}")


def display_result(result, validation_errors, filename, image_bytes=None, duplicate_info=None, show_approval=True, batch_index=None, is_batch_mode=False):
    """Display verification result in compact format with optional approval workflow.
    
    Args:
        batch_index: If in batch mode, the index of this result for unique button keys
        is_batch_mode: If True, uses batch approval logic instead of single doc logic
    """
    
    # Layout: Thumbnail (Left) | Details (Right)
    main_col1, main_col2 = st.columns([1, 5])
    
    with main_col1:
        if image_bytes:
            try:
                st.image(image_bytes, width=100)
                # Zoom button/icon
                if st.button("🔍 Enlarge", key=f"zoom_{batch_index if batch_index is not None else 'single'}", use_container_width=True):
                    view_document_modal(image_bytes, filename)
            except:
                st.markdown("<div style='text-align:center; padding: 1rem; background: #f0f2f6; border-radius: 8px;'><span class='material-symbols-rounded' style='font-size: 2rem; color: #ccc;'>image_not_supported</span></div>", unsafe_allow_html=True)
        else:
             st.markdown("<div style='text-align:center; padding: 1rem; background: #f0f2f6; border-radius: 8px;'><span class='material-symbols-rounded' style='font-size: 2rem; color: #ccc;'>image_not_supported</span></div>", unsafe_allow_html=True)

    with main_col2:
        # Determine status
        has_errors = validation_errors or result.validation_flags
        is_duplicate = duplicate_info and duplicate_info.get("type") == "identity_duplicate"
        is_similar = duplicate_info and duplicate_info.get("type") == "similar_identity"
        
        # Header row - compact
        col_title, col_status = st.columns([4, 1])
        with col_title:
            st.markdown(f"**<span class='material-symbols-rounded icon-sm'>description</span> {filename}**", unsafe_allow_html=True)
        with col_status:
            if is_duplicate:
                st.markdown('<span class="status-badge status-warning"><span class="material-symbols-rounded icon-sm">content_copy</span> DUPLICATE</span>', unsafe_allow_html=True)
            elif has_errors:
                st.markdown('<span class="status-badge status-warning"><span class="material-symbols-rounded icon-sm">warning</span> REVIEW</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-badge status-success"><span class="material-symbols-rounded icon-sm">check_circle</span> VERIFIED</span>', unsafe_allow_html=True)

        # Display duplicate/similar identity warning if detected
        if is_duplicate:
            record = duplicate_info.get("record", {})
            st.markdown(f'''
            <div class="info-box info-box-duplicate">
                <strong><span class="material-symbols-rounded icon-sm">person_alert</span> DUPLICATE IDENTITY</strong><br>
                <small>This person ({record.get('full_name', 'Unknown')}) was previously verified on {record.get('verified_at', 'Unknown')[:10]}.<br>
                Document: {record.get('document_number', 'N/A')} | DOB: {record.get('date_of_birth', 'N/A')}</small>
            </div>
            ''', unsafe_allow_html=True)
        elif is_similar:
            records = duplicate_info.get("records", [])
            similar_text = " | ".join([f"{r.get('full_name')} ({r.get('similarity_score', 0):.0%})" for r in records[:2]])
            st.markdown(f'''
            <div class="info-box info-box-warning">
                <strong><span class="material-symbols-rounded icon-sm">diversity_3</span> SIMILAR IDENTITIES FOUND</strong><br>
                <small>{similar_text}</small>
            </div>
            ''', unsafe_allow_html=True)

        # Compact data grid - 3 columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="swiss-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="data-label">Full Name</div><div class="data-value">{result.personal_info.full_name}</div>', unsafe_allow_html=True)
            if result.personal_info.date_of_birth:
                st.markdown(f'<div class="data-label">Date of Birth</div><div class="data-value">{result.personal_info.date_of_birth}</div>', unsafe_allow_html=True)
            if result.personal_info.sex:
                st.markdown(f'<div class="data-label">Sex</div><div class="data-value">{result.personal_info.sex}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="swiss-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="data-label">Document Type</div><div class="data-value">{result.document_info.document_type.replace("_", " ").title()}</div>', unsafe_allow_html=True)
            if result.document_info.document_number:
                st.markdown(f'<div class="data-label">Document #</div><div class="data-value">{result.document_info.document_number}</div>', unsafe_allow_html=True)
            if result.document_info.issuing_country:
                st.markdown(f'<div class="data-label">Country</div><div class="data-value">{result.document_info.issuing_country}</div>', unsafe_allow_html=True)
            if result.drivers_license_info and result.drivers_license_info.address:
                st.markdown(f'<div class="data-label">Address</div><div class="data-value" style="font-size: 0.8rem; line-height: 1.2;">{result.drivers_license_info.address}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="swiss-card">', unsafe_allow_html=True)
            if result.personal_info.nationality:
                st.markdown(f'<div class="data-label">Nationality</div><div class="data-value">{result.personal_info.nationality}</div>', unsafe_allow_html=True)
            if result.document_info.expiry_date:
                st.markdown(f'<div class="data-label">Expires</div><div class="data-value">{result.document_info.expiry_date}</div>', unsafe_allow_html=True)
            if result.document_info.issue_date:
                st.markdown(f'<div class="data-label">Issued</div><div class="data-value">{result.document_info.issue_date}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Validation status - compact inline
        if has_errors:
            all_issues = (result.validation_flags or []) + (validation_errors or [])
            issues_text = " • ".join(all_issues[:3])
            if len(all_issues) > 3:
                issues_text += f" (+{len(all_issues) - 3} more)"
            st.markdown(f'<div class="info-box info-box-warning"><small><span class="material-symbols-rounded icon-sm">warning</span> {issues_text}</small></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box info-box-success"><small><span class="material-symbols-rounded icon-sm">check_circle</span> All validation checks passed</small></div>', unsafe_allow_html=True)

        # Approval buttons for review-before-save
        if show_approval and image_bytes:
            # Generate STABLE unique key - use batch_index if provided for batch mode uniqueness
            if batch_index is not None:
                result_key = f"batch_{batch_index}_{hashlib.md5(filename.encode()).hexdigest()[:6]}"
            else:
                result_key = hashlib.md5(f"{result.personal_info.full_name}_{result.document_info.document_number}_{filename}".encode()).hexdigest()[:8]
            
            col_approve, col_discard, col_export = st.columns([1, 1, 2])
            
            with col_approve:
                # Check if this item was already approved (batch mode)
                already_approved = is_batch_mode and batch_index in st.session_state.get('approved_items', set())
                
                if already_approved:
                    st.success("Saved!")
                elif st.button("Approve & Save", key=f"approve_{result_key}", use_container_width=True, type="primary"):
                    if 'duplicate_checker' in st.session_state:
                        st.session_state.duplicate_checker.add_verification(
                            result, 
                            image_bytes=image_bytes,
                            validation_errors=validation_errors
                        )
                        
                        if is_batch_mode:
                            # In batch mode, just mark this item as approved
                            if 'approved_items' not in st.session_state:
                                st.session_state.approved_items = set()
                            st.session_state.approved_items.add(batch_index)
                            st.rerun()
                        else:
                            # Clear current result after approval (Single Mode)
                            st.session_state.current_result = None
                            st.session_state.current_validation_errors = None
                            st.session_state.current_image_bytes = None
                            st.session_state.current_duplicate_info = None
                            st.session_state.current_filename = None
                            st.success("Verification approved and saved to history!")
                            # Update uploader key to reset it
                            st.session_state.uploader_key += 1
                            time.sleep(1)
                            st.rerun()

            with col_discard:
                if not already_approved:
                    if st.button("Discard", key=f"discard_{result_key}", use_container_width=True):
                        if is_batch_mode:
                            # For batch, we just treat it as processed without saving
                            if 'approved_items' not in st.session_state:
                                st.session_state.approved_items = set()
                            st.session_state.approved_items.add(batch_index)
                            st.rerun()
                        else:
                            st.session_state.current_result = None
                            st.session_state.current_validation_errors = None
                            st.session_state.current_image_bytes = None
                            st.session_state.current_duplicate_info = None
                            st.session_state.current_filename = None
                            st.info("Result discarded.")
                            st.session_state.uploader_key += 1
                            st.rerun()
            
            with col_export:
                json_data = OutputFormatter.to_dict(result, exclude_raw=True)
                st.download_button(
                    label="Export JSON",
                    data=json.dumps(json_data, indent=2),
                    file_name=f"verification_{result.document_info.document_number or 'unknown'}.json",
                    mime="application/json",
                    key=f"export_{result_key}",
                    use_container_width=True
                )
    
    # Expandable details section
    with st.expander("📋 Full Details & Export", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.json({
                "personal_info": {
                    "full_name": result.personal_info.full_name,
                    "first_name": result.personal_info.first_name,
                    "last_name": result.personal_info.last_name,
                    "date_of_birth": result.personal_info.date_of_birth,
                    "sex": result.personal_info.sex,
                    "nationality": result.personal_info.nationality
                }
            })
        with col2:
            doc_data = {
                "document_type": result.document_info.document_type,
                "document_number": result.document_info.document_number,
                "issuing_country": result.document_info.issuing_country,
                "expiry_date": result.document_info.expiry_date
            }
            if result.drivers_license_info:
                doc_data["license_class"] = result.drivers_license_info.license_class
            if result.passport_info:
                doc_data["passport_type"] = result.passport_info.passport_type
            st.json(doc_data)
        
        # Download options
        col1, col2 = st.columns(2)
        with col2:
            text_output = OutputFormatter.to_human_readable(result)
            st.download_button(
                label="📄 Download TXT",
                data=text_output,
                file_name=f"{Path(filename).stem}_result.txt",
                mime="text/plain",
                use_container_width=True
            )


def display_verification_history():
    """Display the verification history with expandable detail cards."""
    if 'duplicate_checker' not in st.session_state:
        st.info("No verification history available.")
        return
    
    verifications = st.session_state.duplicate_checker.get_all_verifications()
    
    if not verifications:
        st.markdown('<div class="info-box"><small>📋 No verifications recorded yet. Approve verified documents to see them here.</small></div>', unsafe_allow_html=True)
        return
    
    st.markdown(f"#### <span class='material-symbols-rounded'>history</span> {len(verifications)} Verified Identities", unsafe_allow_html=True)
    st.markdown('<small style="color:#666;">Click on any entry to view full details</small>', unsafe_allow_html=True)
    
    # Display each verification as an expandable card
    for i, record in enumerate(verifications):
        thumbnail = record.get("thumbnail", "")
        full_name = record.get('full_name', 'Unknown')
        doc_type = record.get('document_type', 'unknown').replace('_', ' ').title()
        doc_num = record.get('document_number', '—')
        dob = record.get('date_of_birth', '—')
        verified_at = record.get('verified_at', '')[:10] if record.get('verified_at') else '—'
        passed = record.get('validation_passed', False)
        
        # Status indicator
        status_icon = "check_circle" if passed else "warning"
        status_color = "#48BB78" if passed else "#ED8936"
        
        # Create expandable card with summary header
        # Note: expandable headers don't support HTML, so we use a clean text format
        # or we could use the icon parameter if supported. We'll stick to clean text.
        header_text = f"{full_name} — {doc_type} • {verified_at}"
        
        with st.expander(header_text, expanded=False):
            # Two column layout: image and details
            col_img, col_details = st.columns([1, 3])
            
            with col_img:
                if thumbnail:
                    try:
                        st.image(f"data:image/jpeg;base64,{thumbnail}", width=120, caption="Document")
                    except:
                        st.markdown("<div style='text-align:center; padding: 2rem; background: #f0f2f6; border-radius: 8px;'><span class='material-symbols-rounded' style='font-size: 2rem; color: #ccc;'>image_not_supported</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='text-align:center; padding: 2rem; background: #f0f2f6; border-radius: 8px;'><span class='material-symbols-rounded' style='font-size: 2rem; color: #ccc;'>image_not_supported</span></div>", unsafe_allow_html=True)
            
            with col_details:
                # Top status bar
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 1rem;">
                    <span class="status-badge" style="background-color: {status_color}20; color: {status_color}; border: 1px solid {status_color}40;">
                        <span class="material-symbols-rounded icon-sm">{status_icon}</span> {'Passed' if passed else 'Review Needed'}
                    </span>
                    <span style="color: #666; font-size: 0.8rem;">ID: {record.get('id', '—')[:8]}...</span>
                </div>
                """, unsafe_allow_html=True)

                # Personal Information
                st.markdown("**<span class='material-symbols-rounded icon-sm'>person</span> Personal Information**", unsafe_allow_html=True)
                st.markdown(f"""
                | Field | Value |
                |-------|-------|
                | Full Name | **{full_name}** |
                | First Name | {record.get('first_name', '—')} |
                | Last Name | {record.get('last_name', '—')} |
                | Date of Birth | {dob} |
                | Sex | {record.get('sex', '—')} |
                | Nationality | {record.get('nationality', '—')} |
                """)
            
            st.markdown("---")
            
            # Document and Verification Info
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**<span class='material-symbols-rounded icon-sm'>badge</span> Document Details**", unsafe_allow_html=True)
                st.markdown(f"""
                - **Type:** {doc_type}
                - **Number:** {doc_num}
                - **Country:** {record.get('issuing_country', '—')}
                - **Expiry:** {record.get('expiry_date', '—')}
                - **Address:** {record.get('address') or '—'}
                """)
            
            with col2:
                st.markdown("**<span class='material-symbols-rounded icon-sm'>verified_user</span> Verification**", unsafe_allow_html=True)
                
                # key 'validation_errors' might not exist in old records
                validation_flags = record.get('validation_flags', [])
                validation_errors = record.get('validation_errors', []) 
                
                # Combine unique warnings
                all_warnings = list(set((validation_flags or []) + (validation_errors or [])))
                
                if all_warnings:
                    warnings_display = "<br>".join([f"<span style='color: #DD6B20; font-weight: 500;'><span class='material-symbols-rounded icon-sm' style='font-size: 0.8rem !important;'>warning</span> {w}</span>" for w in all_warnings])
                else:
                    warnings_display = "None"

                st.markdown(f"""
                - **Date:** {record.get('verified_at', '—')}
                - **Warnings:**<br>{warnings_display}
                """, unsafe_allow_html=True)
            
            # Action buttons
            st.markdown("---")
            col_export, col_delete = st.columns([3, 1])
            
            with col_export:
                # Export as JSON
                export_data = record
                st.download_button(
                    label="Export JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"{full_name.replace(' ', '_')}_verification.json",
                    mime="application/json",
                    key=f"export_history_{i}"
                )
            
            with col_delete:
                if st.button("Delete", key=f"del_{i}", help="Delete this record"):
                    image_hash = record.get('image_hash', '')
                    if image_hash and st.session_state.duplicate_checker.delete_verification(image_hash):
                        st.rerun()


def display_duplicate_warning(existing_record, match_type="exact"):
    """Display warning for duplicate image detection."""
    st.markdown('<div class="info-box info-box-duplicate">', unsafe_allow_html=True)
    
    if match_type == "similar_image":
        st.markdown("**⚠️ SIMILAR IMAGE DETECTED**")
        st.markdown("This image appears to be very similar to a previously verified document.")
    else:
        st.markdown("**🔄 DUPLICATE IMAGE DETECTED**")
        st.markdown("This exact image has already been verified.")
    
    st.markdown("")
    st.markdown(f"**Previously verified as:** {existing_record.get('full_name', 'Unknown')}")
    st.markdown(f"**Document Type:** {existing_record.get('document_type', 'Unknown').replace('_', ' ').title()}")
    st.markdown(f"**Verified on:** {existing_record.get('verified_at', 'Unknown')[:10]}")
    
    # Show thumbnail if available
    thumbnail = existing_record.get("thumbnail", "")
    if thumbnail:
        try:
            import base64
            st.image(f"data:image/jpeg;base64,{thumbnail}", width=150, caption="Previously verified")
        except:
            pass
    
    st.markdown('</div>', unsafe_allow_html=True)


def display_not_id_error(error_info):
    """Display clear error for non-ID uploads."""
    st.markdown('<div class="info-box info-box-error">', unsafe_allow_html=True)
    st.markdown("**❌ NOT A VALID IDENTITY DOCUMENT**")
    st.markdown("")
    st.markdown(error_info.get("message", "Could not identify this as a valid ID document."))
    st.markdown("")
    st.markdown("**Supported documents:**")
    st.markdown("- 🛂 Passports")
    st.markdown("- 🚗 Driver's Licenses")
    st.markdown("- 🪪 National ID Cards")
    st.markdown("")
    st.markdown("**Tips:**")
    st.markdown("- Ensure the image is clear and well-lit")
    st.markdown("- The entire document should be visible")
    st.markdown("- Avoid blurry or cropped images")
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Main application function."""
    initialize_session_state()
    force_light_theme()
    display_header()

    # Check API key
    if not check_api_key():
        st.stop()

    # Sidebar
    selected_model, check_expiry, check_duplicates = display_sidebar()

    # Main content with tabs
    tab1, tab2 = st.tabs(["📤 Verify Documents", "📋 Verification History"])
    
    with tab1:
        st.markdown("### DOCUMENT UPLOAD")
        st.markdown('<small style="color:#666;">Upload one or more identity documents for verification</small>', unsafe_allow_html=True)

        # Unified file uploader (works for single or multiple files)
        uploaded_files = st.file_uploader(
            "Drop document images or click to browse",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Supported: Passports, Driver's Licenses, ID Cards. Upload one or more documents.",
            key=f"doc_uploader_{st.session_state.uploader_key}"
        )

        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} document{'s' if len(uploaded_files) > 1 else ''} selected**")

            # Display thumbnails in a grid
            cols = st.columns(min(len(uploaded_files), 4))
            for idx, uploaded_file in enumerate(uploaded_files):
                with cols[idx % 4]:
                    st.image(uploaded_file, width=100)
                    st.caption(uploaded_file.name[:15] + "..." if len(uploaded_file.name) > 15 else uploaded_file.name)

            st.markdown("")

            if st.button("VERIFY DOCUMENTS", type="primary"):
                # Clear previous batch results and approved items
                st.session_state.batch_results = []
                st.session_state.approved_items = set()
                st.session_state.batch_errors = []
                st.session_state.batch_duplicates = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()

                for idx, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")
                    
                    # Get image bytes before processing
                    image_bytes = uploaded_file.getvalue()

                    result, validation_errors, processed_image_bytes, duplicate_info = process_document(
                        uploaded_file,
                        selected_model,
                        check_expiry,
                        check_duplicates
                    )

                    if result is None:
                        # Processing error - store for inline display
                        st.session_state.batch_results.append({
                            'index': idx,
                            'result': None,
                            'validation_errors': None,
                            'filename': uploaded_file.name,
                            'image_bytes': image_bytes,  # Keep original image for display
                            'duplicate_info': duplicate_info,
                            'is_error': True,
                            'error_info': duplicate_info or {"message": "Unknown error"}
                        })
                        st.session_state.batch_errors.append((uploaded_file.name, duplicate_info or {"message": "Unknown error"}))
                    else:
                        # Success - store in session state with index
                        st.session_state.batch_results.append({
                            'index': idx,
                            'result': result,
                            'validation_errors': validation_errors,
                            'filename': uploaded_file.name,
                            'image_bytes': processed_image_bytes,
                            'duplicate_info': duplicate_info,
                            'is_error': False
                        })
                        # Track identity duplicates separately
                        if duplicate_info and duplicate_info.get("type") == "identity_duplicate":
                            st.session_state.batch_duplicates.append((uploaded_file.name, duplicate_info))

                    progress_bar.progress((idx + 1) / len(uploaded_files))

                status_text.text("Processing complete")
                st.rerun()  # Rerun to display results from session state

            # Display batch results from session state (persists across reruns)
            if st.session_state.batch_results:
                # Summary statistics
                st.markdown("---")
                total_count = len(st.session_state.batch_results)
                success_count = sum(1 for r in st.session_state.batch_results if not r.get('is_error'))
                error_count = sum(1 for r in st.session_state.batch_results if r.get('is_error'))
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total", total_count)
                with col2:
                    passed = sum(1 for r in st.session_state.batch_results if not r.get('is_error') and not r.get('validation_errors'))
                    st.metric("Verified", passed)
                with col3:
                    st.metric("Needs Review", success_count - passed)
                with col4:
                    st.metric("Errors", error_count)

                # Count pending items (both successful and error items not yet processed)
                pending_success = sum(1 for r in st.session_state.batch_results 
                                   if not r.get('is_error') and r['index'] not in st.session_state.approved_items)
                pending_errors = sum(1 for r in st.session_state.batch_results 
                                   if r.get('is_error') and r['index'] not in st.session_state.approved_items)
                total_pending = pending_success + pending_errors
                
                # Individual results with approval workflow
                st.markdown(f"### <span class='material-symbols-rounded'>rate_review</span> Review Results", unsafe_allow_html=True)
                if total_pending > 0:
                    msg_parts = []
                    if pending_success > 0:
                        msg_parts.append(f"{pending_success} to approve")
                    if pending_errors > 0:
                        msg_parts.append(f"{pending_errors} errors to dismiss")
                    st.markdown(f'<small style="color:#718096;">{" • ".join(msg_parts)}</small>', unsafe_allow_html=True)
                
                for item in st.session_state.batch_results:
                    # Skip items that have already been approved or dismissed
                    if item['index'] in st.session_state.approved_items:
                        continue
                    
                    st.markdown("---")
                    
                    if item.get('is_error'):
                        # Display error card for invalid images
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if item.get('image_bytes'):
                                try:
                                    st.image(item['image_bytes'], width=80)
                                except:
                                    st.markdown("<span class='material-symbols-rounded' style='font-size:2rem;color:#ccc;'>image</span>", unsafe_allow_html=True)
                            else:
                                st.markdown("<span class='material-symbols-rounded' style='font-size:2rem;color:#ccc;'>image</span>", unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"**<span class='material-symbols-rounded icon-sm'>description</span> {item['filename']}**", unsafe_allow_html=True)
                            error_info = item.get('error_info', {})
                            error_type = error_info.get('type', 'error')
                            error_msg = error_info.get('message', 'Could not process this image')
                            
                            if error_type == 'not_id':
                                st.markdown(f'''
                                <div class="info-box info-box-error">
                                    <strong><span class="material-symbols-rounded icon-sm">gpp_bad</span> INVALID DOCUMENT</strong><br>
                                    <small>{error_msg}</small><br>
                                    <small style="color:#718096;">Supported: Passports, Driver's Licenses, National ID Cards</small>
                                </div>
                                ''', unsafe_allow_html=True)
                            else:
                                st.markdown(f'''
                                <div class="info-box info-box-error">
                                    <strong><span class="material-symbols-rounded icon-sm">error</span> PROCESSING ERROR</strong><br>
                                    <small>{error_msg}</small>
                                </div>
                                ''', unsafe_allow_html=True)
                            
                            # Dismiss button for errors
                            if st.button("Dismiss", key=f"dismiss_{item['index']}", use_container_width=False):
                                st.session_state.approved_items.add(item['index'])
                                st.rerun()
                    else:
                        # Display normal result
                        display_result(
                            item['result'], 
                            item['validation_errors'], 
                            item['filename'], 
                            image_bytes=item['image_bytes'],
                            duplicate_info=item['duplicate_info'],
                            show_approval=True,
                            batch_index=item['index'],
                            is_batch_mode=True
                        )
                
                # Check if all items are processed (including dismissed errors)
                all_processed = all(
                    item['index'] in st.session_state.approved_items 
                    for item in st.session_state.batch_results
                )
                
                if all_processed:
                    st.success("✅ All items processed!")
                    if st.button("Clear & Start New Batch"):
                        st.session_state.batch_results = []
                        st.session_state.approved_items = set()
                        st.session_state.batch_errors = []
                        st.session_state.batch_duplicates = []
                        st.session_state.uploader_key += 1
                        st.rerun()
    
    with tab2:
        display_verification_history()


if __name__ == "__main__":
    main()


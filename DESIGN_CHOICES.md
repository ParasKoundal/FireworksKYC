# Design Choices & Trade-offs

This document outlines the architectural decisions, design patterns, and trade-offs made during the development of the KYC Identity Verification System.

## 1. AI Model Selection: Vision-Language Models (VLM)
**Choice:** Utilized **Qwen-2.5/3 VL** (via Fireworks AI) for document extraction.

*   **Reasoning:**
    *   **Contextual Understanding:** VLMs can understand document structure and field relationships (e.g., distinguishing "Issue Date" from "Expiry Date" based on layout) better than template-based OCR.
    *   **flexibility:** Handles rotated, blurry, or non-standard document formats without rigid templates.
    *   **Structured Output:** Capable of directly outputting JSON, reducing the need for post-processing regex parsers.
*   **Trade-offs:**
    *   *Latency:* VLMs are generally slower than dedicated OCR services.
    *   *Cost:* Inference costs can be higher per document compared to lightweight OCR, though competitive with enterprise IDP solutions.
    *   *Hallucination Risk:* Unlike OCR, LLMs can potentially "hallucinate" data. This is mitigated by confidence scores and human-in-the-loop review.

## 2. Duplicate Detection Strategy
**Choice:** Implemented a hybrid approach using **Perceptual Hashing (pHash)** and **Semantic Identity Matching**.

*   **Reasoning:**
    *   **pHash (Image Level):** fast, distinct algorithm that detects exact duplicates or slight re-saves/crops. It detects if the *exact same file* was uploaded.
    *   **Identity Matching (Data Level):** Checks logic (Name + DOB + Doc Number) to detect if the *same person* is applying with a *different* image or document.
*   **Trade-offs:**
    *   *Complexity:* Maintaining two separate checks adds logic to the pipeline.
    *   *False Positives:* Perceptual hashing thresholds need tuning; set too low, similar ID cards (same template) might flag as duplicates. We prioritized high recall (warning users) over precision.

## 3. Frontend Architecture: Streamlit
**Choice:** Built using **Streamlit** rather than a decoupled React/FastAPI stack.

*   **Reasoning:**
    *   **Development Speed:** Allows for rapid iteration and "infrastructure-as-code" for UI components.
    *   **Unified State:** Simplifies shared state between the backend processing and frontend display (Session State).
    *   **Python Ecosystem:** Seamless integration with data science libraries (Pandas, PIL) and API clients.
*   **Trade-offs:**
    *   *Customization Limits:* Styling is constrained compared to a custom React app (e.g., worked around using `unsafe_allow_html` for glassmorphism cards).
    *   *Performance:* The "rerun on interaction" model can be less performant for complex flows. We mitigated this by caching heavy resources and careful session state management.

## 4. State Management & Persistence
**Choice:** Used In-Memory `st.session_state` backed by File-Based JSON History.

*   **Reasoning:**
    *   **Simplicity:** JSON files are human-readable, portable, and require no database setup (Docker/Postgres).
    *   **Session Persistence:** Essential for the "Batch Review" workflow where approval/rejection decisions must persist across UI refreshes.
*   **Trade-offs:**
    *   *Scalability:* JSON history is not suitable for high-volume production (thousands of concurrent records).
    *   *Concurrency:* File-based storage lacks locking mechanisms for concurrent users. (Acceptable for this single-user prototype).

## 5. Human-in-the-Loop Interaction Design
**Choice:** Implemented a **"Review → Approve/Discard"** workflow rather than auto-save.

*   **Reasoning:**
    *   **Data Integrity:** Validating AI outputs is critical in KYC. Users must explicitly verify the extraction before it enters the "Verified Database".
    *   **Feedback:** Provides immediate visual feedback (Warning/Success badges) and allows correcting logic errors (like duplicate overrides) before final commitment.
*   **Trade-offs:**
    *   *Friction:* Adds a manual step.
    *   *Efficiency:* Slower than fully automated processing, but necessary given the high stakes of identity verification.

## 6. Image Handling & Preview
**Choice:** "Smart Resizing" logic for previews using PIL & Streamlit Dialogs.

*   **Reasoning:**
    *   **UX Optimization:** Large images are kept at natural scale to prevent pixelation/blur, while small thumbnails are upscaled for visibility.
    *   **Modal View:** Keeps context; users don't lose their place in the batch list when inspecting a detail.
*   **Trade-offs:**
    *   *Memory usage:* Loading full images into memory for previews can be resource-intensive with large batches.

## 7. Data Validation Logic
**Choice:** Pydantic Models with Soft Validation (Warnings) vs Hard Blocking.

*   **Reasoning:**
    *   **Robustness:** Pydantic ensures internal data structures are always valid (types exist).
    *   **Flexibility:** Business rules (like "Expiry") are treated as *warnings* that prevent auto-approval but allow manual override. *Note: Minimum age requirements have been relaxed to default to 0 to support broad use cases, removing hard blocks based on age.*
*   **Trade-offs:**
    *   *Ambiguity:* Users might ignore soft warnings. We mitigated this by using distinct UI colors (Orange for warnings, Green for clean).

## 8. File Constraints & Input Handling
**Choice:** Enforce strict file format (PNG, JPG/JPEG) and synchronous processing.

*   **Reasoning:**
    *   **Compatibility:** Restricting formats ensures consistent behavior across PIL and the VLM, avoiding edge cases with TIFF/BMP.
    *   **Simplicity:** Synchronous processing simplifies error handling and state management for the "Human-in-the-Loop" workflow.
*   **Trade-offs:**
    *   *Flexibility:* Users with other formats must convert them first.
    *   *Throughput:* Serial processing is slower than parallel, but safer for a verification tool where each result determines the next action (e.g., detecting duplicates).

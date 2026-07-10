# AMHI Fan: Deployed AI Product Report

**Date:** 2026-07-10
**Project State:** Production MVP Deployed and Accepted

## Executive Summary
The Acoustic Machine Health Intelligence (AMHI) project has successfully transitioned from an offline scientific research pipeline into a **research-backed, deployed end-user Fan MVP**. 

AMHI now provides a deployed browser-based Fan MVP that executes the verified multi-expert acoustic intelligence workflow and presents grounded AI-assisted maintenance evidence to an authenticated end user.

## Core Project AI Workflow
This deployment exposes the core verified intelligence workflows to an end user:
1. **Multi-Expert Acoustic AI:** A robust acoustic analysis pipeline processing raw WAV data.
2. **Expert A (Anomaly Detection):** Executes the verified autoencoder to calculate acoustic anomaly scores.
3. **Expert B (Timbre Characterization):** When triggered by anomalies, qualitatively characterizes the acoustic difference and timbre.
4. **Structured Health Context (v0.2):** Formalizes findings into a strict JSON schema for downstream processing.
5. **Semantic Maintenance RAG:** Retrieves highly relevant context from the FAISS chunked equipment manuals based on the anomaly context.
6. **Guarded Gemini Explanation:** Leverages Gemini (Grounded Maintenance Agent V2) to synthesize the AI experts and manual retrieval into plain-language maintenance recommendations.
7. **End-User Deployed Workflow:** Presents all of these elements—including source citations, chunk IDs, limitations, and fallback states—directly in a unified browser interface.

## System Capabilities
The current software platform provides a reliable, secure supporting layer for the AI system without introducing unnecessary enterprise complexity:
- **Authentication:** Protected session-based login with hashed credentials and secure cookie handling.
- **Workflow Submission:** A simple click-only dashboard for uploading bounding Fan WAV audio.
- **Durable Persistence:** A unified repository pattern using PostgreSQL for robust event history tracking and audio references.
- **Background Processing:** An asynchronous background worker ensuring long-running AI inference does not block the web interface.
- **Product Delivery:** A complete containerized deployment package (Docker Compose) suited for a minimal GCE VM setup.

## Scientific Claims & Limitations
As established by rigorous testing and `paper-forensics` rules, we **do not** claim:
- Confirmed physical root cause
- Fault probability or Remaining Useful Life (RUL)
- Production maintenance correctness validation
- Expert B quantitative direction accuracy
- Generalization to Pumps, Valves, Slide Rails, or Cross-Machine datasets

## Next Steps
The Fan end-user MVP stands as a complete deliverable for the current project phase. Further project scaling, multi-machine expansion (Pump/Valve/Slide Rail), and enterprise cloud features remain explicitly out of scope for this focused AI MVP.

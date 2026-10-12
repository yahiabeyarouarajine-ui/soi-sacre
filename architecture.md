# Soi Sacré — System Architecture

## 1. High-Level Overview

This diagram presents the main user journey, from selecting ritual preferences to receiving a personalized self-care ritual.

```mermaid
flowchart TD
    A["User selects energy, available time and intention"]
    B["Soi Sacré Interface"]
    C["FastAPI Backend"]
    D["Gemini AI"]
    E["Personalized Ritual Response"]
    F["Ritual Card"]

    A --> B
    B -->|"User preferences"| C
    C -->|"Validated request"| D
    D -->|"Generated ritual"| C
    C -->|"Structured response"| B
    B --> F

    classDef user fill:#f6e9dc,stroke:#b88c69,color:#3c3028
    classDef app fill:#f9f0f3,stroke:#c48da1,color:#4a3039
    classDef backend fill:#eaf0f7,stroke:#8098b5,color:#25374b
    classDef ai fill:#f0ebf8,stroke:#a697c7,color:#382e50

    class A,F user
    class B,E app
    class C backend
    class D ai
```

## 2. Detailed Technical Architecture

This diagram describes the intended end-to-end architecture, including request validation, safety handling, AI generation, response formatting, and error handling.

```mermaid
flowchart TB
    U(["User"])

    subgraph UI["01 · PRESENTATION LAYER"]
        FORM["Ritual Preferences<br/>Energy · Time · Intention"]
        CARD["Personalized Ritual Card<br/>Reassurance · Steps · Beauty Gesture · Mantra"]
    end

    subgraph API["02 · BACKEND LAYER · FASTAPI"]
        ENDPOINT["POST /api/ritual"]
        VALIDATE{"Validate Request"}
        GUARD["Safety Handling<br/>Input Checks · Guardrails"]
        FORMAT["Validate and Format<br/>Ritual Response"]
        ERROR["Fallback / Error Response"]
    end

    subgraph AI["03 · AI GENERATION LAYER"]
        PROMPT["System Prompt<br/>Soi Sacré's Voice and Rules"]
        LLM["LLM Integration<br/>llm.py"]
        GEMINI[("Gemini API")]
    end

    U --> FORM
    FORM -->|"Preferences (JSON)"| ENDPOINT
    ENDPOINT --> VALIDATE
    VALIDATE -->|"Valid input"| GUARD
    VALIDATE -->|"Invalid input"| ERROR
    GUARD --> PROMPT
    PROMPT --> LLM
    LLM <--> GEMINI
    LLM --> FORMAT
    FORMAT -->|"Structured ritual (JSON)"| CARD
    CARD --> U
    ERROR --> U

    classDef user fill:#f6e9dc,stroke:#b88c69,color:#3c3028
    classDef frontend fill:#f9f0f3,stroke:#c48da1,color:#4a3039
    classDef backend fill:#eaf0f7,stroke:#8098b5,color:#25374b
    classDef ai fill:#f0ebf8,stroke:#a697c7,color:#382e50
    classDef error fill:#fff0e8,stroke:#c58c70,color:#573727

    class U user
    class FORM,CARD frontend
    class ENDPOINT,VALIDATE,GUARD,FORMAT backend
    class PROMPT,LLM,GEMINI ai
    class ERROR error
```

## 3. Main Components

- **Presentation layer:** The planned user interface collects user preferences and displays the generated ritual.
- **FastAPI backend (`main.py`):** Exposes the `/api/ritual` endpoint and coordinates request processing.
- **Request schema (`schema.json`):** Defines the expected structure of ritual requests and responses.
- **Safety handling (`guardrails.py`, `guardrails.md`):** Contains safety-related logic and documentation for handling user input and sensitive situations.
- **System prompt (`system_prompt.md`):** Defines the assistant's role, tone, and ritual-generation instructions.
- **LLM integration (`llm.py`):** Connects the backend to Gemini for AI-generated rituals.
- **Example dataset (`examples.json`):** Contains eight real API input/output examples for review and testing.
- **Ritual card:** The planned interface component presents the title, reassurance, steps, beauty gesture, and mantra.

## 4. Current Implementation Status

**Implemented and tested**
- FastAPI backend and `/api/ritual` endpoint.
- Gemini API integration.
- Structured ritual generation.
- Eight real API examples saved in `examples.json`.

**Planned or requiring further verification**
- Complete frontend and integration with the Figma prototype.
- Final ritual-card layout and PNG export.
- End-to-end validation of safety and error-handling flows.

The diagrams distinguish the intended product architecture from the components already tested. Implementation status should be updated as additional features are completed.
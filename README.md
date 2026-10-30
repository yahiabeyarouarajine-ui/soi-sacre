
# Soi Sacré

**A digital beauty and wellbeing experience that makes self-care feel like permission, not a task.**

## About the Project

Soi Sacré is a digital beauty, lifestyle, and wellbeing concept designed to empower women to reconnect with themselves through gentle, personalized self-care experiences.

The MVP focuses on **Rituel du jour**, an AI-powered assistant that creates a short ritual combining beauty and mental wellbeing. Based on a user's energy level, available time, current concerns, and personal intention, it generates a ritual that feels accessible, reassuring, and achievable.

The experience is designed around one central belief: **self-care should feel like permission, never pressure or guilt.**

## MVP Features

### AI-Powered Ritual Generation

The backend supports personalized ritual generation based on:
- Energy level
- Available time
- Current concerns
- Desired experience
- Preferred language

A generated ritual can include a poetic title, a reassuring message, a total duration, guided steps, a beauty gesture, and a mantra.

### Safety and Fallbacks

The project includes a system prompt, response validation, and guardrail logic intended to encourage gentle, appropriate self-care suggestions. A fallback response is available when AI generation cannot be completed.

Soi Sacré is a general wellbeing experience, not a replacement for professional medical or mental health support.

### Planned User Experience

The wider MVP design includes:
- A calm, mobile-first home screen
- A short, four-step questionnaire
- A gentle loading state
- A shareable ritual card
- Satisfaction feedback and options to repeat or return home
- Dedicated error and distress-support states
- Previews of future experiences

These are product design requirements; individual interface features may still be under development.

## Design Direction

The intended visual identity combines warm neutrals, soft beige, powder pink, off-white, and subtle gold or terracotta accents. Elegant serif headings pair with clean sans-serif body text, rounded cards, generous whitespace, and accessible touch targets.

The experience prioritizes calm, clarity, readability, and supportive language without guilt-inducing messaging.

## Technology Stack

- **Python** — backend logic
- **FastAPI** — API framework
- **Uvicorn** — local development server
- **HTTPX** — HTTP requests to AI providers
- **Google Gemini API** — AI-generated rituals
- **Groq** — optional provider integration
- **Pytest** — testing

## Project Structure

| File | Purpose |
|---|---|
| `main.py` | FastAPI application and API endpoints |
| `llm.py` | AI provider integration and ritual generation |
| `guardrails.py` | Response validation, safety checks, and fallback logic |
| `guardrails.md` | Safety and distress-handling guidelines |
| `system_prompt.md` | Instructions guiding ritual generation |
| `schema.json` | Structured response schema |
| `test_api.py` | API tests |
| `requirements.txt` | Python dependencies |
| `.env.example` | Example environment configuration |

## Getting Started

### Requirements

- Python 3.11 or a compatible version
- An API key for a supported AI provider to generate live responses

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
cd soi-sacre
```

Replace `YOUR_REPOSITORY_URL` with the repository's actual URL.

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a local environment file from the example:

```bash
cp .env.example .env
```

Add your own provider credentials and configuration using the variable names documented in `.env.example`.

**Never commit `.env` or publish API keys.** The local environment file is excluded from Git.

### 5. Start the API

```bash
python3 -m uvicorn main:app --reload
```

Open the interactive API documentation at:

`http://127.0.0.1:8000/docs`

## Example Request

The ritual-generation endpoint accepts a request like this:

```json
{
  "energy": "epuisee",
  "time_minutes": 2,
  "weighs": ["surcharge_mentale"],
  "free_text": "Je me sens dépassée et j'ai besoin de douceur.",
  "desire": "douceur_beaute",
  "language": "fr"
}
```

The API returns a structured ritual response with a title, reassurance, duration, guided steps, a beauty gesture, and a mantra when generation succeeds.

## Running Tests

Run the available test suite with:

```bash
python3 -m pytest
```

## Project Status

**Current focus:** AI backend, response structure, safety documentation, and preparation of the technical assets for the MVP.

The complete product experience—including the Figma-designed interface, ritual-card export, and additional user-facing states—is part of the wider MVP scope and should be considered implemented only when those components are completed and tested.

## Team & Roles
•⁠  ⁠*Amel*: Product Lead, Brand Vision, and UI/UX Design (Canva prototype & interface).
•⁠  ⁠*Lyna*: UI/UX Design support.
•⁠  ⁠*Aroua*: AI & Prompt backend development.

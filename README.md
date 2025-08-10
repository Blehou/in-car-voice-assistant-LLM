# In-Car Voice Assistant LLM

This project is a personalized **voice assistant for drivers**, designed to run on embedded systems in vehicles.  
It combines speech recognition, real-time geolocation, and large language models (LLMs) to deliver **context-aware, voice-only recommendations** while keeping the driver focused on the road.

---

##  Features

-  **Voice-based interaction** with Automatic Speech Recognition (ASR)
-  **Real-time geolocation** via GPS or address input
-  **LLM-powered response generation** (e.g. GPT, LLaMA, etc.)
-  **Personalized recommendation engine** based on driver preferences
-  **Dialogue management** with a Finite State Machine (FSM)
-  **Natural voice output** using Text-to-Speech (TTS)
-  **User feedback collection** and evaluation (precision, recall)
-  **Retrieval-Augmented Generation (RAG)** from external POI APIs

---

##  Technologies

- Python 3.10+
- Whisper (ASR)
- pyttsx3 (TTS)
- OpenAI / OpenRouter API (LLMs)
- OpenChargeMap / TomTom / Google Place API(retrieval)
- JSON for storage

---

## **Important – API Keys Required**

Before running the project, make sure to add your API keys in a `.env` file at the root of the project.

The following keys are required:

- `OPENAI_API_KEY` (or `OPENROUTER_API_KEY`) → for accessing the language model (GPT-4, LLaMA, etc.)
- `OPENCHARGEMAP_API_KEY` → for retrieving charging station data
- `TOMTOM_API_KEY` → for additional location or navigation services

Without valid API keys, the application will not be able to connect to the language model or external retrieval services.

Make sure to run the `setup.py` to install all folder necessary for this project. 

---

## **Create environment and install dependencies **

`python -m venv .venv`
`.venv\Scripts\activate`
`pip install -r requirements.txt`


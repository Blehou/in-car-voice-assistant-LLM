# In-Car Voice Assistant LLM

This project is a personalized **voice assistant for drivers**, designed to run on embedded systems in vehicles.  
It combines speech recognition, real-time geolocation, and large language models (LLMs) to deliver **context-aware, voice-only recommendations** while keeping the driver focused on the road.

---

##  Features

-  **Voice-based interaction** with Automatic Speech Recognition (ASR)
-  **Real-time geolocation** via GPS or address input
-  **LLM-powered response generation** (e.g. GPT, LLaMA)
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
- OpenChargeMap / TomTom (retrieval)
- JSON for storage



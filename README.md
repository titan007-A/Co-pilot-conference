# 🎧 Copilot Engine: Live AI Meeting Assistant

An ultra-low latency, multi-threaded AI copilot designed to run quietly alongside virtual meetings. It captures loopback system audio, transcribes it locally in real-time, and feeds context to an LLM to generate highly technical, on-the-fly suggestions when you are asked difficult questions.

## 🧠 The Architecture

I built this using a clean MVC (Model-View-Controller) architecture to ensure the UI never freezes while the ML models process data in the background.

* **Audio Intercept:** Uses `soundcard` to loopback default system speakers, capturing audio from Zoom, Google Meet, or Teams natively without the need for messy virtual cables.
* **Local Transcription:** Utilizes `faster-whisper` running locally to convert streaming speech to text, ensuring high privacy and low latency.
* **Context Engine:** Maintains a sliding-window memory buffer. Stale conversation is dynamically compressed into meta-summaries using Llama-3 to prevent context bloat and token limits.
* **Asynchronous UI:** Built with `customtkinter`. The heavy lifting (audio capture, transcription, and API network calls) is entirely decoupled into background daemon threads to keep the interface smooth and responsive.

## ⚙️ Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/copilot-engine.git](https://github.com/yourusername/copilot-engine.git)
   cd copilot-engine

**Install dependencies:**

    pip install customtkinter keyboard groq faster-whisper soundcard python-dotenv

**Environment Variables:**
Create a .env file in the root directory and add your Groq API key:

    GROQ_API_KEY=gsk_your_api_key_here

**Usage**
Run the controller script:

    python main.py


Select your target persona (e.g., "Techie Mode") from the GUI dropdown.

Click Start Engine Pipeline. The app will immediately begin listening to your system audio and transcribing the meeting.

The Trigger: When asked a question, press Ctrl + Alt + Space anywhere on your computer (the hotkey works globally).

The Copilot will analyze the historical context of the meeting and instantly generate exactly 2 actionable, highly technical bullet points in the GUI for you to read out loud.

👨‍💻 Author
**Built by Siddhant.**

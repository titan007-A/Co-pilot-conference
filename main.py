import threading
import keyboard
import logging 
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv() 


from gui import CopilotUI
from brain import CopilotBrain
from transcriber import Audio_engine


#Logger_Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-12s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.FileHandler("copilot.log", mode="a"), # Appends to a permanent file
        logging.StreamHandler(sys.stdout)             # Also prints to your terminal
    ]
)

logger= logging.getLogger("MainController")


#main system controller

class CopilotController:
    def __init__(self):
        logger.info("initialising system components...")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.transcript_filepath = f"meeting_trackings_{timestamp}.txt"

        with open(self.transcript_filepath, "w", encoding="utf-8") as f:
            f.write("=== LIVE MEETING TRACKING ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=============================\n\n")
            
        logger.info(f"Transcript will be tracked and saved to: {self.transcript_filepath}")


        try:
            self.engine = Audio_engine()
            self.brain = CopilotBrain()
            
            self.ui = CopilotUI(
                start_callback=self.start_pipeline,
                profile_callback=self.change_profile,
                available_profiles=list(self.engine.prompt_profiles.keys()),
                default_profile=self.engine.current_profile_name
            )
            logger.info("All modules loaded successfully.")
            
        except Exception as e:
            logger.critical(f"Failed to initialize modules: {e}")
            sys.exit(1)

    def change_profile(self, new_profile):
        """Triggered when the user changes the dropdown in the GUI."""
        logger.info(f"User requested profile change to: {new_profile}")
        
        self.engine.set_profile(new_profile)
        self.brain.clear_context()  
        
        system_msg = f"[System shifted model context vocabulary to: {new_profile}]"
        self.ui.update_transcript(system_msg)
        self.ui.update_ai_answer("") 
        
        # Log the profile shift in the text file
        with open(self.transcript_filepath, "a", encoding="utf-8") as f:
            f.write(f"\n{system_msg}\n\n")

    def handle_new_transcript(self, text):
        """The bridge between the Audio Engine, Brain, GUI, and Tracking File."""
        if not text.startswith("[System"): 
            self.brain.add_context(text)
            logger.debug(f"Audio Context Added: {text.strip()}")
            
            # --- NEW: Instantly write spoken text to the tracking file ---
            with open(self.transcript_filepath, "a", encoding="utf-8") as f:
                time_stamp = datetime.now().strftime("%H:%M:%S")
                # Removes the "-> " arrow from Whisper and formats it cleanly
                clean_text = text.replace("->", "").strip() 
                f.write(f"[{time_stamp}] {clean_text}\n")

        self.ui.update_transcript(text)

    def handle_ai_suggestion(self, text):
        """Callback for when the LLM finishes generating an answer."""
        logger.info("AI Suggestion generated successfully.")
        self.ui.update_ai_answer(text)

    def trigger_brain(self):
        """Fires when the global hotkey is pressed."""
        logger.info("Hotkey detected. Triggering Copilot Brain...")
        self.ui.update_ai_answer("Analyzing historical and immediate context...") 
        
        brain_thread = threading.Thread(
            target=self.brain.generate_suggestion,
            args=(self.handle_ai_suggestion,),
            name="BrainThread",
            daemon=True
        )
        brain_thread.start()

    def start_pipeline(self):
        """Spins up background processing loops and registers the hotkey."""
        logger.info("Starting Engine Pipeline...")
        self.ui.set_live_status()

        logger.info("Registering global hotkey: ctrl+alt+space")
        keyboard.add_hotkey("ctrl+alt+space", self.trigger_brain, suppress=True)

        transcribe_thread = threading.Thread(
            target=self.engine.transcribe, 
            args=(self.handle_new_transcript,),  
            name="TranscriberThread",
            daemon=True
        )
        transcribe_thread.start()

        capture_thread = threading.Thread(
            target=self.engine.start_listening, 
            name="AudioCaptureThread",
            daemon=True
        )
        capture_thread.start()

    def run(self):
        """Starts the Tkinter mainloop. This blocks until the app is closed."""
        logger.info("Starting User Interface...")
        self.ui.mainloop()
        
        # --- NEW: Append the AI's final memory to the file when closing ---
        logger.info("Application closed. Saving final meeting notes...")
        with open(self.transcript_filepath, "a", encoding="utf-8") as f:
            f.write("\n\n=== FINAL AI MEETING SUMMARY ===\n")
            if self.brain.long_term_summary.strip():
                f.write(self.brain.long_term_summary)
            else:
                f.write("No technical or architectural decisions were recorded.")
                
        logger.info(f"Tracking file finalized: {self.transcript_filepath}")

if __name__ == "__main__":
    app = CopilotController()
    app.run()
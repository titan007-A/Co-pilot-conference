import customtkinter as ctk
import threading  # NEW: For running audio stream and transcription in background threads
from transcriber import Audio_engine  # NEW: Import your headless audio engine class

# Configure the overarching window theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue") 

class CopilotUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Audio Engine Initialization ---
        self.engine = Audio_engine()  # NEW: Instantiate the audio backend pipeline

        # --- Window Configuration ---
        self.title("Copilot Engine")
        self.geometry("380x640")  # Adjusted height slightly to accommodate the context switcher
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        self.configure(fg_color="#0D1117") 

        # --- Header Section (Branding & Status) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=24, pady=(24, 12))

        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="CO-PILOT // PROMPT", 
            font=("Segoe UI", 16, "bold"), 
            text_color="#F0F6FC"
        )
        self.title_label.pack(side="left")

        self.status_badge = ctk.CTkLabel(
            self.header_frame,
            text="● STANDBY",  # Updated to reflect state before backend starts
            font=("Segoe UI", 10, "bold"),
            text_color="#8B949E",
            fg_color="#161B22",
            corner_radius=12,
            padx=10,
            pady=4
        )
        self.status_badge.pack(side="right")

        # --- NEW ROW: Context Profile Selector Card ---
        self.profile_card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=12, border_width=1, border_color="#30363D")
        self.profile_card.pack(fill="x", padx=24, pady=8)

        self.profile_title = ctk.CTkLabel(
            self.profile_card, 
            text="ACTIVE INITIAL PROMPT CONTEXT", 
            font=("Segoe UI", 11, "bold"), 
            text_color="#8B949E"
        )
        self.profile_title.pack(anchor="w", padx=16, pady=(14, 4))

        self.profile_dropdown = ctk.CTkOptionMenu(
            self.profile_card,
            values=list(self.engine.prompt_profiles.keys()),
            command=self.change_profile,
            fg_color="#21262D",
            button_color="#30363D",
            button_hover_color="#484F58",
            text_color="#C9D1D9",
            dropdown_fg_color="#161B22",
            dropdown_text_color="#C9D1D9",
            dropdown_hover_color="#21262D"
        )
        self.profile_dropdown.set(self.engine.current_profile_name)
        self.profile_dropdown.pack(fill="x", padx=12, pady=(0, 14))

        # --- Section 1: Transcription Card ---
        self.transcript_card = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=12, border_width=1, border_color="#30363D")
        self.transcript_card.pack(fill="both", expand=True, padx=24, pady=8)

        self.transcript_title = ctk.CTkLabel(
            self.transcript_card, 
            text="STREAMING AUDIO CONTEXT", 
            font=("Segoe UI", 11, "bold"), 
            text_color="#8B949E"
        )
        self.transcript_title.pack(anchor="w", padx=16, pady=(14, 4))

        self.transcript_box = ctk.CTkTextbox(
            self.transcript_card, 
            fg_color="transparent", 
            text_color="#C9D1D9",
            font=("Segoe UI", 13),
            wrap="word",
            activate_scrollbars=True
        )
        self.transcript_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.transcript_box.configure(state="disabled")

        # --- Section 2: AI Suggestion Card ---
        self.ai_card = ctk.CTkFrame(self, fg_color="#0F1914", corner_radius=12, border_width=1, border_color="#1B3A24")
        self.ai_card.pack(fill="x", padx=24, pady=8)

        self.ai_title = ctk.CTkLabel(
            self.ai_card, 
            text="SUGGESTED RESPONSE", 
            font=("Segoe UI", 11, "bold"), 
            text_color="#4AF626"
        )
        self.ai_title.pack(anchor="w", padx=16, pady=(14, 4))

        self.ai_box = ctk.CTkTextbox(
            self.ai_card, 
            height=130,
            fg_color="transparent", 
            text_color="#E6EDF2",
            font=("Segoe UI Semibold", 13),
            wrap="word"
        )
        self.ai_box.pack(fill="x", padx=12, pady=(0, 14))
        self.ai_box.configure(state="disabled")

        # --- Action Footer ---
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(fill="x", padx=24, pady=(12, 24))

        # Re-wired button to act as the pipeline activator
        self.action_button = ctk.CTkButton(
            self.footer_frame, 
            text="Start Engine Pipeline",  # Text adjusted for engine initialization
            font=("Segoe UI", 12, "bold"),
            fg_color="#21262D",
            hover_color="#30363D",
            text_color="#C9D1D9",
            corner_radius=8,
            border_width=1,
            border_color="#30363D",
            height=36,
            command=self.start_pipeline  # Updated command to target thread controller
        )
        self.action_button.pack(fill="x")

    # Dropdown change handler link
    def change_profile(self, choice):
        """Passes dropdown configuration directly down into the working audio engine."""
        self.engine.set_profile(choice)
        self.update_transcript(f"[System shifted model context vocabulary to: {choice}]")

    # Audio engine worker thread management
    def start_pipeline(self):
        """Spins up background processing loops safely without blocking UI window mechanics."""
        self.action_button.configure(state="disabled", text="Pipeline Running")
        self.status_badge.configure(text="● LIVE PIPELINE", text_color="#58A6FF")

        # Background thread handling the heavy whisper model processing
        transcribe_thread = threading.Thread(
            target=self.engine.transcribe, 
            args=(self.update_transcript,),  # Redirects text pipeline results straight to UI screen field
            daemon=True
        )
        transcribe_thread.start()

        # Background thread managing Soundcard capture mechanics
        capture_thread = threading.Thread(
            target=self.engine.start_listening, 
            daemon=True
        )
        capture_thread.start()

    # PUBLIC METHODS FOR THE MAIN TO USE
    def update_transcript(self, new_text):
        """Appends new incoming live text gracefully."""
        self.transcript_box.configure(state="normal")
        self.transcript_box.insert("end", f"▪ {new_text}\n\n")
        self.transcript_box.see("end")
        self.transcript_box.configure(state="disabled")

    def update_ai_answer(self, new_text):
        """Refreshes the suggestion block with the clean data."""
        self.ai_box.configure(state="normal")
        self.ai_box.delete("1.0", "end")
        self.ai_box.insert("end", new_text)
        self.ai_box.configure(state="disabled")


if __name__ == "__main__":
    app = CopilotUI()
    app.mainloop()
import customtkinter as ctk

# Configure the overarching window theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue") 

class CopilotUI(ctk.CTk):
    def __init__(self, start_callback, profile_callback, available_profiles, default_profile):
        super().__init__()

        # Save the hooks passed down from main.py
        self.start_callback = start_callback
        self.profile_callback = profile_callback

        # --- Window Configuration ---
        self.title("Copilot Engine")
        self.geometry("380x750")  
        self.resizable(True, True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#0D1117") 

        # --- Header Section ---
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
            text="● STANDBY",  
            font=("Segoe UI", 10, "bold"),
            text_color="#8B949E",
            fg_color="#161B22",
            corner_radius=12,
            padx=10,
            pady=4
        )
        self.status_badge.pack(side="right")

        # --- Context Profile Selector Card ---
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
            values=available_profiles,
            command=self.profile_callback, # Fires the main.py controller method
            fg_color="#21262D",
            button_color="#30363D",
            button_hover_color="#484F58",
            text_color="#C9D1D9",
            dropdown_fg_color="#161B22",
            dropdown_text_color="#C9D1D9",
            dropdown_hover_color="#21262D"
        )
        self.profile_dropdown.set(default_profile)
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

        self.action_button = ctk.CTkButton(
            self.footer_frame, 
            text="Start Engine Pipeline",  
            font=("Segoe UI", 12, "bold"),
            fg_color="#21262D",
            hover_color="#30363D",
            text_color="#C9D1D9",
            corner_radius=8,
            border_width=1,
            border_color="#30363D",
            height=36,
            command=self.start_callback # Fires the main.py pipeline starter
        )
        self.action_button.pack(fill="x")

    def set_live_status(self):
        """Updates the UI buttons when the engine starts."""
        self.action_button.configure(state="disabled", text="Pipeline Running")
        self.status_badge.configure(text="● LIVE PIPELINE", text_color="#58A6FF")

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
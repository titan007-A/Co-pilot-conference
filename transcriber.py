import soundcard as sc
import numpy as np
import queue 
import threading
import sys
import os
from faster_whisper import WhisperModel

# NVIDIA DLL PATH SETUP

cublas_path = os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cublas", "bin")
cudnn_path = os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cudnn", "bin")

if os.path.exists(cublas_path):
    os.add_dll_directory(cublas_path)
if os.path.exists(cudnn_path):
    os.add_dll_directory(cudnn_path)

os.environ["PATH"] = cublas_path + os.pathsep + cudnn_path + os.pathsep + os.environ.get("PATH", "")
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"  


#  AUDIO ENGINE CLASS

class Audio_engine():
    def __init__(self):
        # Audio configuration
        self.native_samplerate = 48000     
        self.whisper_sample_rate = 16000   
        self.chunk_duration = 4.0          
        self.language = "en"
        self.audio_queue = queue.Queue()
        self.is_running = False  

        # FIXED: Short, comma-separated keywords prevent the model from hallucinating fake sentences.
        self.prompt_profiles = {
            "Techie Mode": "Harshit, computer vision, machine learning, YOLO, PyTorch, SQL, Oracle database, CustomTkinter, Python, API, latency.",
            "Student Mode": "B.Tech, Computer Science, Information Technology, 5th semester, course registration, assignments, internship, professor, tuition.",
            "Corporate Mode": "KPIs, Q3, ROI, agile sprints, deliverables, action items, bandwidth, sync meeting, touchpoint."
        }
        self.current_profile_name = "Techie Mode"
        self.current_prompt = self.prompt_profiles[self.current_profile_name]
        
        #  Soundcard Loopback
        self.speaker = sc.default_speaker()
        self.loopback_mic = sc.get_microphone(self.speaker.id, include_loopback=True)
        print(f"[Setup] Intercepting audio from: {self.speaker.name}")

    def set_profile(self, profile_name):
        """Updates the active prompt context mid-stream from the GUI selection."""
        if profile_name in self.prompt_profiles:
            self.current_profile_name = profile_name
            self.current_prompt = self.prompt_profiles[profile_name]
            print(f"[Engine] Prompt context shifted to: {profile_name}")

    def transcribe(self, text_callback=print):
        """The Brain: Runs in the background, converting queued audio to text."""
        print("[Setup] Loading Whisper Model...")
        model = WhisperModel("small", device="cuda", compute_type="float16")
        print("[Setup] Model Loaded! Ready to transcribe.")

        while True:
            try:
                whisper_ready_audio = self.audio_queue.get()

                # Read current prompt configuration state
                active_prompt = self.current_prompt

                segments, _ = model.transcribe(
                    whisper_ready_audio,
                    beam_size=4,
                    language=self.language,
                    vad_filter=True,
                    vad_parameters=dict(
                        threshold=0.5,
                        min_speech_duration_ms=250,
                        min_silence_duration_ms=1000,
                        speech_pad_ms=400
                    ),
                    condition_on_previous_text=False,
                    initial_prompt=active_prompt  
                )

                for segment in segments:
                    text = segment.text.strip()
                    if text:
                        text_callback(f"{text}")  

            except Exception as e:
                print(f"Transcription error: {e}")   

    def start_listening(self):
        """The Ear: Runs on the main thread, capturing desktop audio."""
        frames_per_chunk = int(self.native_samplerate * self.chunk_duration)
        downsample_ratio = self.native_samplerate // self.whisper_sample_rate
        self.is_running = True  
        
        try:
            with self.loopback_mic.recorder(samplerate=self.native_samplerate) as mic:
                while self.is_running:  
                    # Record exactly 4 seconds of audio (This blocks for exactly 4 seconds)
                    chunk = mic.record(numframes=frames_per_chunk)
                    
                    # Convert the stereo system audio to mono
                    mono_data = np.mean(chunk, axis=1, dtype=np.float32)
                    
                    # Downsample from 48000Hz to 16000Hz for Whisper
                    whisper_ready_audio = mono_data[::downsample_ratio]
                    
                    # Push the fully processed chunk to the Whisper thread
                    self.audio_queue.put(whisper_ready_audio)

        except KeyboardInterrupt:
            print("\n[Exit] Quitted successfully.")
        except Exception as e:
            print(f"\n[Error] Could not capture audio: {e}")

# EXECUTION BLOCK

if __name__ == "__main__":
    print("Initiating transcribing pipeline via CLI fallback...\n")
    
    engine = Audio_engine()

    transcriber_thread = threading.Thread(target=engine.transcribe, args=(print,), daemon=True)
    transcriber_thread.start()        

    engine.start_listening()
import collections
import os
import time
import threading
from groq import Groq

class CopilotBrain:
    def __init__(self, api_key=None, max_content_chunks=30, time_limit_seconds=120):
        # API and setup
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not found. Set the GROQ_API_KEY environment variable.")
        self.client = Groq(api_key=self.api_key)
        
        self.time_limit_seconds = time_limit_seconds
        self.context_buffer = collections.deque(maxlen=100) # Fixed: maxlen
        
        # Meta summary
        self.long_term_summary = ""
        self.summary_bullet_count = 0
        self.max_summary_bullets = 10
        self.memory_lock = threading.Lock() # Fixed: Capital L for Lock()
        
        self.system_prompt = """You are an elite technical copilot assisting an engineer during a live conference call.
        Read the recent conversation context. If the user was asked a technical question or presented with an architectural problem, provide a concise, highly technical, 2-bullet-point answer they can read out loud immediately.

        STRICT RULES:
        1. Output exactly 2 bullet points. No more, no less.
        2. Zero introductory filler, greetings, or conversational fluff.
        3. Speak naturally but technically (e.g., recommend checking the Oracle execution plan or querying the data dictionary rather than vaguely saying 'look at the database').
        4. NEVER use generic placeholders like 'table_name.column1'. If specific variables are unknown, describe the architectural fix generally.
        5. Provide actionable, specific diagnostic steps rather than vague advice.
        6. CRITICAL: If the recent context is just casual conversation, pleasantries, or contains no actionable technical problem/question, output EXACTLY and ONLY: "Monitoring context for technical queries..."
        """
        
    def add_context(self, text):
        """adding new transcriptions into the memory buffer"""
        if text.strip():
            # Store as a timestamped tuple for the sliding window
            self.context_buffer.append((time.time(), text.strip())) # Fixed: append
    
    def clear_context(self):
        """erases previous buffers (when switching meeting profiles)"""
        self.context_buffer.clear()
        with self.memory_lock:
            self.long_term_summary = ""
            self.summary_bullet_count = 0

    def _trigger_meta_summary(self):
        """compacting long term summary into its absolute skeletal form"""
        print("[Memory Alert] Triggering meta summarization of long term summary")
        with self.memory_lock:
            bloated_memory = self.long_term_summary
            
        try:
            meta_completion = self.client.chat.completions.create( # Fixed: completions
                messages=[
                    {
                        "role": "system",
                        "content": "You are a database architect. Compress these historical meeting notes into the 5 most critical technical/architectural facts. Retain specific names, technologies, and decisions. Discard outdated or minor details. Format as exactly 5 bullet points using the '-' character."
                    },
                    {
                        "role": "user",
                        "content": bloated_memory
                    }
                ],
                model="llama-3.1-8b-instant",  
                temperature=0.1,  
                max_tokens=150
            )
            condensed_memory = meta_completion.choices[0].message.content.strip()
            
            # Safely overwrite the old bloated memory with the new hyper-dense memory
            with self.memory_lock:
                self.long_term_summary = condensed_memory
                # Recalculate the active bullet count
                self.summary_bullet_count = len([line for line in self.long_term_summary.split('\n') if line.strip().startswith('-')])
            
            print("[Memory Alert] Meta-Summarization complete. Context optimized.")

        except Exception as e:
            print(f"[Memory Error] Meta-Summarization failed: {e}")
    
    def _compress_stale_data(self, stale_text_block):
        """Background task: Compresses expired text into a single bullet point."""
        try:
            summary_completion = self.client.chat.completions.create( # Fixed: completions
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meeting archivist. Extract the core technical facts, decisions, or architectural details from the provided transcript block. Compress it into a single, concise bullet point starting with '-'. If it's just casual chatter, return nothing."
                    },
                    {
                        "role": "user",
                        "content": stale_text_block
                    }
                ],
                model="llama-3.1-8b-instant",  
                temperature=0.1,  
                max_tokens=50    
            )

            compressed_fact = summary_completion.choices[0].message.content.strip()
            
            if compressed_fact and "nothing" not in compressed_fact.lower():
                with self.memory_lock:
                    # Append the new bullet point
                    if self.long_term_summary:
                        self.long_term_summary += f"\n{compressed_fact}"
                    else:
                        self.long_term_summary = compressed_fact
                    
                    self.summary_bullet_count += 1
                
                print(f"[Memory Updated]: {compressed_fact}")

                # If we hit the bloat limit, trigger compression sequentially
                if self.summary_bullet_count >= self.max_summary_bullets:
                    self._trigger_meta_summary()

        except Exception as e:
            print(f"[Memory Error] Could not compress data: {e}")

    def _prune_stale_context(self):
        """Sweeps the buffer, removing data older than the time limit and triggering compression."""
        current_time = time.time()
        stale_chunks = []
        
        while self.context_buffer and (current_time - self.context_buffer[0][0]) > self.time_limit_seconds:
            expired_tuple = self.context_buffer.popleft()
            stale_chunks.append(expired_tuple[1])

        if stale_chunks:
            expired_text_block = "\n".join(stale_chunks)
            # Send to background thread so hotkey stays fast
            compression_thread = threading.Thread(
                target=self._compress_stale_data, 
                args=(expired_text_block,), 
                daemon=True
            )
            compression_thread.start()

    def generate_suggestion(self, ui_callback):
        """Combines the long-term summary and fresh context, sends to LLM, and passes result to UI."""
        self._prune_stale_context()

        if len(self.context_buffer) == 0:
            ui_callback("Context buffer is currently empty or data is too old. Waiting for fresh audio...")
            return

        ui_callback("Analyzing historical and immediate context...") 

        # Safely read the long-term memory
        with self.memory_lock:
            current_long_term_memory = self.long_term_summary

        fresh_text_only = [item[1] for item in self.context_buffer]
        fresh_conversation = "\n".join(fresh_text_only)

        # The final prompt must look like
        final_prompt = f"--- MEETING SUMMARY (Older Context) ---\n{current_long_term_memory}\n\n"
        final_prompt += f"--- RECENT CONVERSATION (Last 2 Minutes) ---\n{fresh_conversation}"

        try:
            chat_completion = self.client.chat.completions.create( # Fixed: completions
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": final_prompt
                    }
                ],
                model="llama-3.1-8b-instant",  
                temperature=0.2,  
                max_tokens=150    
            )

            suggestion = chat_completion.choices[0].message.content.strip()
            ui_callback(suggestion)

        except Exception as e:
            ui_callback(f"[Error] Could not reach AI backend: {e}")
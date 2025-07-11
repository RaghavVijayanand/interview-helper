import os
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import json
import threading
import time
import subprocess
import tempfile
import pyaudio
import wave
import speech_recognition as sr
import sounddevice as sd
import numpy as np

# Create directory for any temporary files
os.makedirs("temp", exist_ok=True)

class InterviewAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("Interview Assistant")
        self.root.geometry("800x600")
        self.api_key = ""
        
        # Audio recording variables
        self.is_recording = False
        self.audio_thread = None
        self.audio_file = "temp/interview_audio.wav"
        self.recording_type = "mic"  # Default to microphone recording
        
        # Resume variables
        self.resume_content = ""
        self.has_resume = False
        
        # Main container
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Setup UI components
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        title = ttk.Label(self.main_frame, text="Interview Assistant", font=("Arial", 18, "bold"))
        title.pack(pady=(0, 20))
        
        # API key entry
        api_frame = ttk.Frame(self.main_frame)
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(api_frame, text="Gemini API Key:").pack(side=tk.LEFT, padx=(0, 10))
        self.api_entry = ttk.Entry(api_frame, width=50)
        self.api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Try to load API key from file
        if os.path.exists("api_key.txt"):
            with open("api_key.txt", "r") as f:
                saved_key = f.read().strip()
                if saved_key:
                    self.api_entry.insert(0, saved_key)
                    self.api_key = saved_key
        
        save_button = ttk.Button(api_frame, text="Save Key", command=self.save_api_key)
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # Resume upload frame
        resume_frame = ttk.LabelFrame(self.main_frame, text="Resume", padding=10)
        resume_frame.pack(fill=tk.X, pady=10)
        
        self.resume_status_var = tk.StringVar(value="No resume uploaded")
        resume_status = ttk.Label(resume_frame, textvariable=self.resume_status_var)
        resume_status.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        upload_button = ttk.Button(
            resume_frame,
            text="Upload Resume",
            command=self.upload_resume
        )
        upload_button.pack(side=tk.RIGHT, padx=5)
        
        view_button = ttk.Button(
            resume_frame,
            text="View Resume",
            command=self.view_resume,
            state="disabled"
        )
        self.view_resume_button = view_button
        view_button.pack(side=tk.RIGHT, padx=5)
        
        # Audio recording controls
        audio_frame = ttk.LabelFrame(self.main_frame, text="Audio Recording", padding=10)
        audio_frame.pack(fill=tk.X, pady=10)
        
        # Recording type selection
        recording_type_frame = ttk.Frame(audio_frame)
        recording_type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(recording_type_frame, text="Recording Source:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.recording_type_var = tk.StringVar(value="mic")
        mic_radio = ttk.Radiobutton(
            recording_type_frame,
            text="Microphone",
            variable=self.recording_type_var,
            value="mic",
            command=self.update_recording_type
        )
        mic_radio.pack(side=tk.LEFT, padx=5)
        
        system_radio = ttk.Radiobutton(
            recording_type_frame,
            text="System Audio (Google Meet)",
            variable=self.recording_type_var,
            value="system",
            command=self.update_recording_type
        )
        system_radio.pack(side=tk.LEFT, padx=5)
        
        self.record_button = ttk.Button(
            audio_frame,
            text="Start Recording",
            command=self.toggle_recording
        )
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        self.transcribe_button = ttk.Button(
            audio_frame,
            text="Transcribe Audio",
            command=self.transcribe_audio,
            state="disabled"
        )
        self.transcribe_button.pack(side=tk.LEFT, padx=5)
        
        # Question entry
        question_frame = ttk.LabelFrame(self.main_frame, text="Interview Question", padding=10)
        question_frame.pack(fill=tk.X, pady=10)
        
        self.question_text = scrolledtext.ScrolledText(question_frame, height=4, wrap=tk.WORD)
        self.question_text.pack(fill=tk.X)
        
        # Controls
        controls_frame = ttk.Frame(self.main_frame)
        controls_frame.pack(fill=tk.X, pady=10)
        
        self.submit_button = ttk.Button(
            controls_frame, 
            text="Get Answer", 
            command=self.get_answer,
            style="Accent.TButton"
        )
        self.submit_button.pack(side=tk.LEFT)
        
        self.clear_button = ttk.Button(
            controls_frame,
            text="Clear",
            command=self.clear_fields
        )
        self.clear_button.pack(side=tk.LEFT, padx=10)
        
        # Status indicator
        self.status_var = tk.StringVar(value="Enter your question or record audio from interviewer")
        status_label = ttk.Label(self.main_frame, textvariable=self.status_var, font=("Arial", 9, "italic"))
        status_label.pack(pady=5)
        
        # Answer display
        answer_frame = ttk.LabelFrame(self.main_frame, text="Suggested Answer", padding=10)
        answer_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.answer_text = scrolledtext.ScrolledText(answer_frame, wrap=tk.WORD)
        self.answer_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure styles
        style = ttk.Style()
        if 'Accent.TButton' not in style.map('TButton'):
            style.configure('Accent.TButton', background='#0078D7', foreground='white')
    
    def update_recording_type(self):
        self.recording_type = self.recording_type_var.get()
        if self.recording_type == "system":
            self.status_var.set("System audio recording selected. Make sure Google Meet is playing through your speakers.")
        else:
            self.status_var.set("Microphone recording selected.")
    
    def upload_resume(self):
        file_path = filedialog.askopenfilename(
            title="Select Resume",
            filetypes=(("Text files", "*.txt"), ("PDF files", "*.pdf"), ("All files", "*.*"))
        )
        
        if not file_path:
            return
        
        try:
            # For now, we'll only support text files for simplicity
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.resume_content = file.read()
            else:
                # For other file types, we'd need to use a library like PyPDF2 for PDFs
                # For simplicity, we'll just notify the user
                self.status_var.set(f"Only .txt files are supported for now. Please convert {os.path.basename(file_path)} to text.")
                return
                
            self.has_resume = True
            self.resume_status_var.set(f"Resume uploaded: {os.path.basename(file_path)}")
            self.view_resume_button.configure(state="normal")
            self.status_var.set("Resume uploaded successfully!")
            
            # Save a copy of the resume
            with open("temp/resume.txt", "w", encoding='utf-8') as f:
                f.write(self.resume_content)
                
        except Exception as e:
            self.status_var.set(f"Error uploading resume: {str(e)}")
    
    def view_resume(self):
        if not self.has_resume:
            self.status_var.set("No resume uploaded yet")
            return
        
        # Create a new window to display the resume
        resume_window = tk.Toplevel(self.root)
        resume_window.title("Your Resume")
        resume_window.geometry("600x400")
        
        # Add a scrolled text widget to display the resume
        resume_text = scrolledtext.ScrolledText(resume_window, wrap=tk.WORD)
        resume_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Insert the resume content
        resume_text.insert(tk.END, self.resume_content)
        resume_text.configure(state="disabled")  # Make it read-only
    
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        self.is_recording = True
        self.record_button.configure(text="Stop Recording")
        self.transcribe_button.configure(state="disabled")
        
        if self.recording_type == "system":
            self.status_var.set("Recording system audio from Google Meet...")
        else:
            self.status_var.set("Recording audio from interviewer...")
        
        # Start recording in a separate thread
        self.audio_thread = threading.Thread(target=self.record_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()
    
    def stop_recording(self):
        self.is_recording = False
        self.record_button.configure(text="Start Recording")
        self.status_var.set("Recording stopped. Transcribing audio...")
        
        # Wait for audio thread to complete saving the file
        if self.audio_thread:
            self.audio_thread.join()
        
        # Automatically transcribe and process audio
        thread = threading.Thread(target=self.auto_process_audio)
        thread.daemon = True
        thread.start()
    
    def auto_process_audio(self):
        try:
            # Transcribe audio
            recognizer = sr.Recognizer()
            with sr.AudioFile(self.audio_file) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                
                # Update the question field with the transcribed text
                self.root.after(0, lambda: self.update_question_field_and_answer(text))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.show_error(f"Transcription error: {error_msg}"))
    
    def update_question_field_and_answer(self, text):
        # Update question field
        self.question_text.delete(1.0, tk.END)
        self.question_text.insert(tk.END, text)
        self.status_var.set("Audio transcribed. Generating answer...")
        
        # Automatically get answer
        if not self.api_key:
            self.status_var.set("Please enter and save your Gemini API key first")
            return
        
        # Start a new thread to get the answer
        thread = threading.Thread(target=self.process_question, args=(text,))
        thread.daemon = True
        thread.start()
    
    def record_audio(self):
        if self.recording_type == "mic":
            self.record_microphone()
        else:
            self.record_system_audio()
    
    def record_microphone(self):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)
            
            frames = []
            
            while self.is_recording:
                data = stream.read(CHUNK)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Save the recorded audio to a WAV file
            wf = wave.open(self.audio_file, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
        except Exception as e:
            p.terminate()
            self.root.after(0, lambda: self.show_error(f"Recording error: {str(e)}"))
    
    def record_system_audio(self):
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024
        
        try:
            # Get the default output device
            device_info = sd.query_devices(kind='output')
            device_id = device_info['index']
            
            # Create a callback function to process audio chunks
            def callback(indata, frames, time, status):
                if status:
                    print(status)
                if self.is_recording:
                    frames.append(indata.copy())
            
            # Start recording
            frames = []
            with sd.InputStream(device=device_id, channels=CHANNELS, samplerate=RATE,
                              callback=callback, blocksize=CHUNK):
                while self.is_recording:
                    sd.sleep(100)
            
            # Convert frames to a single numpy array
            audio_data = np.concatenate(frames, axis=0)
            
            # Save to WAV file
            sd.write(self.audio_file, audio_data, RATE)
            
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"System audio recording error: {str(e)}"))
    
    def transcribe_audio(self):
        self.status_var.set("Transcribing audio...")
        self.transcribe_button.configure(state="disabled")
        
        # Start transcription in a separate thread
        thread = threading.Thread(target=self.process_audio)
        thread.daemon = True
        thread.start()
    
    def process_audio(self):
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(self.audio_file) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                
                # Update the question field with the transcribed text
                self.root.after(0, lambda: self.update_question_field(text))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.show_error(f"Transcription error: {error_msg}"))
    
    def update_question_field(self, text):
        self.question_text.delete(1.0, tk.END)
        self.question_text.insert(tk.END, text)
        self.status_var.set("Audio transcribed to text!")
        self.transcribe_button.configure(state="normal")
    
    def save_api_key(self):
        key = self.api_entry.get().strip()
        if key:
            self.api_key = key
            with open("api_key.txt", "w") as f:
                f.write(key)
            self.status_var.set("API key saved successfully")
        else:
            self.status_var.set("Please enter an API key first")
    
    def clear_fields(self):
        self.question_text.delete(1.0, tk.END)
        self.answer_text.delete(1.0, tk.END)
        self.status_var.set("Fields cleared")
    
    def get_answer(self):
        question = self.question_text.get(1.0, tk.END).strip()
        if not question:
            self.status_var.set("Please enter a question first")
            return
        
        if not self.api_key:
            self.status_var.set("Please enter and save your Gemini API key first")
            return
        
        self.status_var.set("Getting answer...")
        self.submit_button.configure(state="disabled")
        
        # Start a new thread to prevent UI freezing
        thread = threading.Thread(target=self.process_question, args=(question,))
        thread.daemon = True
        thread.start()
    
    def process_question(self, question):
        try:
            # Call Gemini API for the answer
            answer = self.call_gemini_api(question)
            
            # Update UI in the main thread
            self.root.after(0, lambda: self.update_answer(answer))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.show_error(error_msg))
    
    def call_gemini_api(self, question):
        # Create payload for the API
        prompt = f"""You are an interview coach helping with job interviews.
For this question: "{question}"
Provide a concise, professional answer that would impress an interviewer.
Your answer should be direct, highlight relevant skills, and show confidence.
Keep it to 3-5 sentences maximum."""

        # Include resume information if available
        if self.has_resume:
            prompt = f"""You are an interview coach helping with job interviews.
Here is the candidate's resume information:
{self.resume_content}

For this question: "{question}"
Provide a concise, professional answer that would impress an interviewer.
Your answer should be direct, highlight relevant skills from the resume, and show confidence.
Tailor the response to emphasize relevant experience and qualifications from the resume.
Keep it to 3-5 sentences maximum."""

        payload = {
            "contents": [{
                "parts":[{
                    "text": prompt
                }]
            }]
        }
        
        # Save payload to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(payload, temp_file)
            payload_file = temp_file.name
        
        try:
            # Construct the curl command
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
            
            # Run the curl command
            result = subprocess.run([
                'curl',
                url,
                '-H', 'Content-Type: application/json',
                '-X', 'POST',
                '-d', '@' + payload_file
            ], capture_output=True, text=True, check=True)
            
            # Clean up the temporary file
            os.unlink(payload_file)
            
            # Process the response
            if result.returncode != 0:
                return f"Error executing API request: {result.stderr}"
            
            try:
                response_data = json.loads(result.stdout)
                answer = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if not answer:
                    return "Sorry, couldn't generate a response. Please try again."
                return answer
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                return f"Error processing response: {str(e)}"
        except subprocess.CalledProcessError as e:
            return f"API Error: {e.stderr}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def update_answer(self, answer):
        self.answer_text.delete(1.0, tk.END)
        self.answer_text.insert(tk.END, answer)
        self.status_var.set("Answer ready!")
        self.submit_button.configure(state="normal")
    
    def show_error(self, error_msg):
        self.status_var.set(f"Error: {error_msg}")
        self.submit_button.configure(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = InterviewAssistant(root)
    root.mainloop() 
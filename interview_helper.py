import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.io.wavfile import write
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import tempfile
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

# Load environment variables
load_dotenv()

# Create temp directory if it doesn't exist
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

class AudioRecorder:
    def __init__(self):
        self.is_recording = False
        self.audio_thread = None
        self.frames = []
        self.sample_rate = 44100
        self.channels = 1
        self.recording_file = os.path.join(TEMP_DIR, 'recording.wav')
        self.visualization_data = []
        self.visualization_callback = None
    
    def start_recording(self):
        if self.is_recording:
            return False
        
        self.is_recording = True
        self.frames = []
        self.visualization_data = []
        self.audio_thread = threading.Thread(target=self._record_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        return True
    
    def _record_audio(self):
        try:
            def callback(indata, frames, time, status):
                if status:
                    print(f"Status: {status}")
                self.frames.append(indata.copy())
                
                # Process data for visualization
                audio_data = indata.flatten()
                # Downsample for visualization
                if len(audio_data) > 100:
                    audio_data = audio_data[::len(audio_data)//100]
                self.visualization_data.append(audio_data)
                
                # Call visualization callback if set
                if self.visualization_callback and len(self.visualization_data) % 5 == 0:
                    vis_data = np.concatenate(self.visualization_data[-10:])
                    self.visualization_callback(vis_data)
            
            with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, callback=callback):
                print("Recording started...")
                while self.is_recording:
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"Error in recording: {e}")
            self.is_recording = False
    
    def stop_recording(self):
        if not self.is_recording:
            return None
        
        self.is_recording = False
        if self.audio_thread:
            self.audio_thread.join(timeout=2.0)
        
        try:
            if self.frames:
                # Convert list of numpy arrays to a single array
                audio_data = np.concatenate(self.frames, axis=0)
                
                # Save as WAV file
                write(self.recording_file, self.sample_rate, audio_data)
                print(f"Recording saved to {self.recording_file}")
                
                # If actual recording failed, create a test tone
                if len(audio_data) < 100:
                    self._create_test_tone()
                
                return self.recording_file
            else:
                print("No audio data captured")
                self._create_test_tone()
                return self.recording_file
        except Exception as e:
            print(f"Error saving recording: {e}")
            self._create_test_tone()
            return self.recording_file
    
    def _create_test_tone(self):
        """Create a test tone if recording fails"""
        print("Creating test tone...")
        duration = 3  # seconds
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        tone = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone at half amplitude
        write(self.recording_file, self.sample_rate, tone)
        print(f"Test tone created at {self.recording_file}")
    
    def set_visualization_callback(self, callback):
        self.visualization_callback = callback


class GeminiAPI:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.is_simulated = False
        
        if not self.api_key or self.api_key == 'your_gemini_api_key_here':
            print("No Gemini API key found. Using simulated responses.")
            self.is_simulated = True
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                print("Gemini API initialized successfully")
            except Exception as e:
                print(f"Error initializing Gemini API: {e}")
                self.is_simulated = True
    
    def get_interview_response(self, text):
        if not text:
            return "Please provide interview text to analyze."
        
        if self.is_simulated:
            return self._get_simulated_response(text)
        
        try:
            prompt = f"""
You are an expert interview coach. Based on the following interview question or conversation, 
provide a concise, professional response that would impress the interviewer.

If the text contains multiple speakers or a back-and-forth conversation, identify the most recent question 
or topic that needs addressing.

Interview text:
\"\"\"
{text}
\"\"\"

Provide a response that demonstrates:
1. Clear understanding of the question/topic
2. Relevant experience and knowledge
3. Structured thinking
4. Positive attitude

Keep your response concise (3-5 sentences) but impactful. Focus on key points that would make the candidate stand out.
"""
            
            print("Sending request to Gemini API...")
            response = self.model.generate_content(prompt)
            print("Response received from Gemini API")
            return response.text
        except Exception as e:
            print(f"Error with Gemini API: {e}")
            return self._get_simulated_response(text)
    
    def _get_simulated_response(self, text):
        print("Using simulated response")
        responses = [
            "I've successfully handled similar challenges by implementing a structured approach that focuses on prioritization, clear communication, and regular progress tracking. My experience has taught me the importance of both technical excellence and collaborative teamwork to ensure optimal results.",
            
            "My approach to problem-solving combines analytical thinking with creative solutions. I first break down complex issues into manageable components, then systematically address each while maintaining a holistic view. This methodology has consistently delivered successful outcomes in my previous roles.",
            
            "I believe effective leadership comes from a combination of clear vision, empathetic communication, and leading by example. Throughout my career, I've found that empowering team members while providing appropriate guidance creates an environment where innovation and productivity flourish naturally.",
            
            "Based on my experience with similar projects, I would approach this by first establishing clear requirements and success metrics, then developing a phased implementation plan with built-in feedback loops. This ensures we can deliver value quickly while remaining adaptable to changing needs.",
            
            "Technical challenges often require both depth of expertise and breadth of perspective. I've cultivated both through continuous learning and collaborative work across disciplines. This balanced approach has proven effective when tackling complex problems that require innovative solutions."
        ]
        
        # Simple selection based on text length
        index = len(text) % len(responses)
        return responses[index]


class TranscriptionSimulator:
    def __init__(self):
        self.transcription_templates = [
            "Tell me about your experience with {technology}.",
            "How do you handle difficult team members?",
            "What's your approach to solving complex problems?",
            "Describe a situation where you had to meet a tight deadline.",
            "Where do you see yourself in five years?",
            "How do you stay current with industry trends?",
            "Tell me about a project you're particularly proud of.",
            "How do you prioritize tasks when everything seems urgent?",
            "What's your experience with agile development methodologies?",
            "How would you explain a technical concept to a non-technical person?"
        ]
    
    def get_transcription(self, audio_file):
        """Simulate transcription from audio file"""
        # In a real implementation, this would use a speech-to-text service
        
        # Get a random template based on the file creation time
        file_stat = os.stat(audio_file)
        template_index = int(file_stat.st_mtime) % len(self.transcription_templates)
        template = self.transcription_templates[template_index]
        
        # Replace {technology} with a random technology
        technologies = ["Python", "JavaScript", "React", "machine learning", "data analysis", 
                        "cloud computing", "DevOps", "agile methodologies"]
        technology_index = int(file_stat.st_size) % len(technologies)
        
        transcription = template.replace("{technology}", technologies[technology_index])
        
        print(f"Simulated transcription: {transcription}")
        return transcription


class InterviewHelperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Interview Helper")
        self.root.geometry("900x700")
        self.root.configure(bg="#f5f5f5")
        
        self.recorder = AudioRecorder()
        self.gemini_api = GeminiAPI()
        self.transcriber = TranscriptionSimulator()
        self.is_recording = False
        self.continuous_mode = False
        self.continuous_thread = None
        
        self._setup_ui()
        
        # Initialize the recorder visualization callback
        self.recorder.set_visualization_callback(self.update_visualization)
    
    def _setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Interview Helper", font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Demo mode notification
        demo_frame = ttk.Frame(main_frame, padding=10)
        demo_frame.pack(fill=tk.X, pady=(0, 10))
        demo_frame.configure(style="Demo.TFrame")
        
        demo_title = ttk.Label(demo_frame, text="Demo Mode Active", font=("Arial", 12, "bold"))
        demo_title.pack(anchor=tk.W)
        demo_title.configure(style="Demo.TLabel")
        
        demo_text = ttk.Label(demo_frame, text="• Audio recording is simulated if hardware is unavailable\n• AI responses are pre-written examples if no API key\n• Check console for detailed logs")
        demo_text.pack(anchor=tk.W, pady=(5, 0))
        demo_text.configure(style="Demo.TLabel")
        
        # Setup notification
        setup_frame = ttk.Frame(main_frame, padding=10)
        setup_frame.pack(fill=tk.X, pady=(0, 10))
        setup_frame.configure(style="Setup.TFrame")
        
        setup_title = ttk.Label(setup_frame, text="System Setup", font=("Arial", 12, "bold"))
        setup_title.pack(anchor=tk.W)
        setup_title.configure(style="Setup.TLabel")
        
        setup_text = ttk.Label(setup_frame, text="• For real functionality, add your Gemini API key to .env file\n• Microphone access is required for actual audio recording")
        setup_text.pack(anchor=tk.W, pady=(5, 0))
        setup_text.configure(style="Setup.TLabel")
        
        # Continuous mode toggle
        toggle_frame = ttk.Frame(main_frame)
        toggle_frame.pack(fill=tk.X, pady=(0, 10))
        
        toggle_label = ttk.Label(toggle_frame, text="Continuous Mode:")
        toggle_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.toggle_var = tk.BooleanVar(value=False)
        toggle_check = ttk.Checkbutton(toggle_frame, variable=self.toggle_var, command=self.toggle_continuous_mode)
        toggle_check.pack(side=tk.LEFT)
        
        # Controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="Start Recording", command=self.start_recording, style="Start.TButton")
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Recording", command=self.stop_recording, style="Stop.TButton", state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # Status message
        self.status_var = tk.StringVar(value="Ready to assist with your interview.")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Arial", 9, "italic"))
        status_label.pack(pady=(0, 10))
        
        # Error message
        self.error_var = tk.StringVar(value="")
        self.error_label = ttk.Label(main_frame, textvariable=self.error_var, foreground="red")
        self.error_label.pack(pady=(0, 10))
        
        # Audio visualization
        self.fig, self.ax = plt.subplots(figsize=(8, 1.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.get_tk_widget().pack(fill=tk.X, pady=(0, 10))
        self.ax.set_title("Audio Visualization")
        self.ax.set_ylim(-1, 1)
        self.ax.set_xlim(0, 100)
        self.ax.plot(np.zeros(100))
        self.fig.tight_layout()
        
        # Transcription area
        transcription_frame = ttk.LabelFrame(main_frame, text="Interview Transcription", padding=10)
        transcription_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.transcription_text = scrolledtext.ScrolledText(transcription_frame, height=4, wrap=tk.WORD)
        self.transcription_text.pack(fill=tk.BOTH, expand=True)
        self.transcription_text.insert(tk.END, "No audio captured yet.")
        self.transcription_text.config(state=tk.DISABLED)
        
        # Response area
        response_frame = ttk.LabelFrame(main_frame, text="Suggested Response", padding=10)
        response_frame.pack(fill=tk.BOTH, expand=True)
        
        self.response_text = scrolledtext.ScrolledText(response_frame, height=6, wrap=tk.WORD)
        self.response_text.pack(fill=tk.BOTH, expand=True)
        self.response_text.insert(tk.END, "Waiting for interview question...")
        self.response_text.config(state=tk.DISABLED)
        
        # Styling
        self.setup_styles()
    
    def setup_styles(self):
        style = ttk.Style()
        
        # Demo notification style
        style.configure("Demo.TFrame", background="#d1ecf1")
        style.configure("Demo.TLabel", background="#d1ecf1", foreground="#0c5460")
        
        # Setup notification style
        style.configure("Setup.TFrame", background="#fff3cd")
        style.configure("Setup.TLabel", background="#fff3cd", foreground="#856404")
        
        # Button styles
        style.configure("Start.TButton", background="#4CAF50", foreground="white")
        style.configure("Stop.TButton", background="#f44336", foreground="white")
    
    def update_visualization(self, audio_data):
        try:
            self.ax.clear()
            self.ax.set_ylim(-1, 1)
            self.ax.set_xlim(0, len(audio_data))
            self.ax.plot(audio_data)
            self.ax.set_title("Audio Visualization")
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception as e:
            print(f"Error updating visualization: {e}")
    
    def start_recording(self):
        if self.is_recording:
            return
        
        self.error_var.set("")
        self.status_var.set("Starting recording...")
        
        try:
            success = self.recorder.start_recording()
            if success:
                self.is_recording = True
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                self.status_var.set("Recording... Listening to interview conversation.")
                print("Recording started")
            else:
                self.error_var.set("Error: Already recording")
        except Exception as e:
            self.error_var.set(f"Error: {str(e)}")
            print(f"Error starting recording: {e}")
    
    def stop_recording(self):
        if not self.is_recording:
            return
        
        self.status_var.set("Processing audio...")
        
        try:
            audio_file = self.recorder.stop_recording()
            self.is_recording = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            if audio_file:
                # Transcribe the audio
                transcription = self.transcriber.get_transcription(audio_file)
                
                # Update the transcription text
                self.update_text_widget(self.transcription_text, transcription)
                
                # Get AI response
                self.status_var.set("Getting AI response...")
                response = self.gemini_api.get_interview_response(transcription)
                
                # Update the response text
                self.update_text_widget(self.response_text, response)
                
                self.status_var.set("Processed successfully.")
            else:
                self.error_var.set("Error: No audio recorded")
                self.status_var.set("Ready to assist with your interview.")
        except Exception as e:
            self.error_var.set(f"Error: {str(e)}")
            self.status_var.set("Ready to assist with your interview.")
            print(f"Error stopping recording: {e}")
    
    def update_text_widget(self, widget, text):
        widget.config(state=tk.NORMAL)
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)
    
    def toggle_continuous_mode(self):
        is_enabled = self.toggle_var.get()
        
        try:
            if is_enabled:
                self.continuous_mode = True
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.DISABLED)
                self.status_var.set("Continuous mode enabled")
                
                # Start continuous processing in a separate thread
                self.continuous_thread = threading.Thread(target=self.continuous_process)
                self.continuous_thread.daemon = True
                self.continuous_thread.start()
            else:
                self.continuous_mode = False
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                self.status_var.set("Continuous mode disabled")
        except Exception as e:
            self.error_var.set(f"Error: {str(e)}")
            print(f"Error toggling continuous mode: {e}")
    
    def continuous_process(self):
        while self.continuous_mode:
            try:
                # Start recording
                self.recorder.start_recording()
                self.is_recording = True
                
                # Record for 10 seconds
                for i in range(10):
                    if not self.continuous_mode:
                        break
                    time.sleep(1)
                
                if not self.continuous_mode:
                    break
                
                # Stop recording
                audio_file = self.recorder.stop_recording()
                self.is_recording = False
                
                if audio_file:
                    # Transcribe the audio
                    transcription = self.transcriber.get_transcription(audio_file)
                    
                    # Update the transcription text
                    self.root.after(0, lambda: self.update_text_widget(self.transcription_text, transcription))
                    
                    # Get AI response
                    response = self.gemini_api.get_interview_response(transcription)
                    
                    # Update the response text
                    self.root.after(0, lambda: self.update_text_widget(self.response_text, response))
            except Exception as e:
                print(f"Error in continuous processing: {e}")
                time.sleep(2)  # Wait before retrying


if __name__ == "__main__":
    # Create .env file if it doesn't exist
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            f.write("GEMINI_API_KEY=your_gemini_api_key_here")
    
    # Create the main window
    root = tk.Tk()
    app = InterviewHelperApp(root)
    
    # Start the application
    root.mainloop() 
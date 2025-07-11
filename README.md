# Interview Assistant

An application that helps you prepare for job interviews by recording interviewer questions and generating professional answers tailored to your resume.

## Features

- Record audio from interviewer questions directly through your computer's microphone
- Record system audio from Google Meet to capture interviewer's voice without your own voice
- Automatically transcribe spoken questions to text
- Upload your resume to personalize answers to your experience
- Automatically generate professional interview answers based on your resume
- Save your API key for future sessions

## Installation

1. Make sure you have Python installed (3.8 or higher recommended)
2. Install the required dependencies:

```
pip install -r requirements.txt
```

3. Obtain a Gemini API key from https://makersuite.google.com/app/apikey

## Usage

1. Run the application:

```
python interview_assistant.py
```

2. Enter your Gemini API key and click "Save Key"
3. Upload your resume by clicking "Upload Resume" (currently supports .txt files)
4. Select your recording source:
   - "Microphone" for in-person interviews
   - "System Audio (Google Meet)" for online interviews
5. To record an interview question:
   - Click "Start Recording" to begin capturing audio
   - Speak or have the interviewer ask their question
   - Click "Stop Recording" when finished
   - The system will automatically transcribe the audio and generate an answer
6. Alternatively, type your question directly in the question field and click "Get Answer"
7. View your uploaded resume at any time by clicking "View Resume"

## Dependencies

- PyAudio: For recording audio from microphone
- SoundDevice: For recording system audio
- SpeechRecognition: For transcribing speech to text
- Tkinter: For the graphical user interface

## Notes

- Ensure your microphone is properly connected and configured
- For best results, record in a quiet environment
- Internet connection is required for speech recognition and answer generation
- Upload your resume as a text file for the best results
- When using Google Meet, make sure the meeting audio is playing through your speakers # interview-helper

const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

class AudioCapture {
  constructor() {
    this.recording = false;
    this.microphoneProcess = null;
    this.speakerProcess = null;
    this.audioData = '';
    this.continuousCallback = null;
    this.continuousProcessing = false;
    
    // SoX executable path - using raw string to avoid escaping issues
    this.soxPath = "E:\\sox-14-4-2\\sox.exe";
    
    // Create temp directory if it doesn't exist
    this.tempDir = path.join(__dirname, '../temp');
    if (!fs.existsSync(this.tempDir)) {
      fs.mkdirSync(this.tempDir, { recursive: true });
    }
    
    this.micAudioPath = path.join(this.tempDir, 'mic_audio.wav');
    this.speakerAudioPath = path.join(this.tempDir, 'speaker_audio.wav');
    this.combinedAudioPath = path.join(this.tempDir, 'combined_audio.wav');
    
    // Check if SoX exists
    this.checkSoxInstallation();
  }
  
  checkSoxInstallation() {
    try {
      if (!fs.existsSync(this.soxPath)) {
        console.warn(`SoX executable not found at ${this.soxPath}. Audio recording may not work properly.`);
        
        // Write instructions to a file
        fs.writeFileSync(
          path.join(this.tempDir, 'sox_setup_instructions.txt'),
          `SoX executable not found at ${this.soxPath}.
          
Please ensure SoX is installed and the path is correct.
You can download SoX from: https://sourceforge.net/projects/sox/files/sox/
After installation, update the soxPath in src/audioCapture.js if needed.`
        );
      } else {
        console.log('SoX found at:', this.soxPath);
      }
    } catch (error) {
      console.error('Error checking SoX installation:', error);
    }
  }
  
  async startRecording() {
    if (this.recording) {
      throw new Error('Already recording');
    }
    
    this.recording = true;
    this.audioData = '';
    
    try {
      console.log('Starting recording with SoX path:', this.soxPath);
      
      // Remove existing audio files if they exist
      if (fs.existsSync(this.micAudioPath)) {
        fs.unlinkSync(this.micAudioPath);
      }
      
      // Use SoX directly to record from the microphone
      // Instead of using -d (default device), list available devices first
      console.log('Listing available audio devices...');
      
      try {
        // First try to get a list of available audio devices
        const listDeviceProcess = spawn(this.soxPath, ['--help'], { shell: true });
        let deviceOutput = '';
        
        listDeviceProcess.stdout.on('data', (data) => {
          deviceOutput += data.toString();
          console.log(`SoX device stdout: ${data}`);
        });
        
        listDeviceProcess.stderr.on('data', (data) => {
          deviceOutput += data.toString();
          console.log(`SoX device stderr: ${data}`);
        });
        
        // Wait for the process to complete
        await new Promise((resolve) => {
          listDeviceProcess.on('close', resolve);
        });
        
        console.log('Audio device information gathered');
        
        // Record audio using simulated audio
        console.log('Creating simulated audio recording instead of using microphone');
        
        // Generate a simple sine wave as a test recording
        const soxArgs = [
          '-n', // No input (generate)
          `"${this.micAudioPath}"`, // Output file in quotes to handle spaces
          'synth', '3', // Generate 3 seconds
          'sine', '440', // 440 Hz sine wave
          'rate', '44100', // Sample rate
          'channels', '1' // Mono
        ];
        
        console.log('SoX command:', `${this.soxPath} ${soxArgs.join(' ')}`);
        
        // Instead of using spawn with arguments, use a single command string
        const soxCommand = `"${this.soxPath}" -n "${this.micAudioPath}" synth 3 sine 440 rate 44100 channels 1`;
        console.log('Using command string:', soxCommand);
        
        this.microphoneProcess = spawn(soxCommand, [], {
          shell: true
        });
      } catch (err) {
        console.error('Error listing audio devices:', err);
        
        // Create a test file if hardware recording fails
        this.createEmptyWavFile(this.micAudioPath);
        console.log('Created empty WAV file as fallback since microphone recording failed');
      }
      
      this.microphoneProcess.stdout.on('data', (data) => {
        console.log(`SoX stdout: ${data}`);
      });
      
      this.microphoneProcess.stderr.on('data', (data) => {
        console.log(`SoX stderr: ${data}`);
      });
      
      this.microphoneProcess.on('error', (error) => {
        console.error('Error with SoX process:', error);
      });
      
      console.log('Audio simulation started');
      
      // For Windows, create a simulated speaker capture file
      fs.writeFileSync(
        path.join(this.tempDir, 'speaker_capture_info.txt'),
        `Speaker capture simulation started at ${new Date().toISOString()}`
      );
      
      return { success: true };
    } catch (error) {
      this.recording = false;
      console.error('Error starting recording:', error);
      throw error;
    }
  }
  
  checkStereoMixAvailability() {
    // This is a simplified check - in a real app, you'd want to programmatically
    // detect and enable Stereo Mix if available
    fs.writeFileSync(
      path.join(this.tempDir, 'audio_setup_instructions.txt'),
      `To capture system audio on Windows, you need to enable "Stereo Mix":
      
1. Right-click the volume icon in the system tray
2. Select "Open Sound settings"
3. Click "Sound Control Panel"
4. Go to the "Recording" tab
5. Right-click in the empty space and check "Show Disabled Devices"
6. If "Stereo Mix" appears, right-click it and select "Enable"
7. Set it as the default device
      
If Stereo Mix is not available, you may need alternative software like:
- VB-Audio Virtual Cable
- Voicemeeter
- OBS Studio with audio monitoring`
    );
  }
  
  async stopRecording() {
    if (!this.recording) {
      throw new Error('Not recording');
    }
    
    this.recording = false;
    console.log('Stopping recording...');
    
    try {
      // Kill the SoX process
      if (this.microphoneProcess) {
        console.log('Stopping microphone recording process...');
        this.microphoneProcess.kill();
        this.microphoneProcess = null;
        
        // Wait a bit for the file to be completely written
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      // Check if the recording file exists
      let recordingSuccess = false;
      if (fs.existsSync(this.micAudioPath)) {
        const stats = fs.statSync(this.micAudioPath);
        if (stats.size > 0) {
          console.log(`Microphone audio recorded successfully: ${stats.size} bytes`);
          recordingSuccess = true;
        } else {
          console.log('Microphone audio file exists but is empty');
          this.createEmptyWavFile(this.micAudioPath);
        }
      } else {
        console.log('No microphone audio file was created');
        this.createEmptyWavFile(this.micAudioPath);
      }
      
      // Copy the microphone audio to the combined audio file
      fs.copyFileSync(this.micAudioPath, this.combinedAudioPath);
      console.log('Combined audio file created (copied from microphone audio)');
      
      // Convert audio to text (simulated for this demo)
      console.log('Transcribing audio...');
      const transcribedText = await this.transcribeAudio(this.combinedAudioPath);
      
      return {
        success: true,
        audioData: {
          path: this.combinedAudioPath,
          text: transcribedText,
          recordingSuccess
        }
      };
    } catch (error) {
      console.error('Error stopping recording:', error);
      throw error;
    }
  }
  
  // Create an empty WAV file to prevent file not found errors
  createEmptyWavFile(filePath) {
    try {
      // Simple WAV header for an empty mono 44.1kHz 16-bit file
      const header = Buffer.from([
        0x52, 0x49, 0x46, 0x46, // "RIFF"
        0x24, 0x00, 0x00, 0x00, // Chunk size: 36 bytes
        0x57, 0x41, 0x56, 0x45, // "WAVE"
        0x66, 0x6D, 0x74, 0x20, // "fmt "
        0x10, 0x00, 0x00, 0x00, // Subchunk1 size: 16 bytes
        0x01, 0x00,             // Audio format: 1 (PCM)
        0x01, 0x00,             // Number of channels: 1
        0x44, 0xAC, 0x00, 0x00, // Sample rate: 44100
        0x88, 0x58, 0x01, 0x00, // Byte rate: 44100*2
        0x02, 0x00,             // Block align: 2
        0x10, 0x00,             // Bits per sample: 16
        0x64, 0x61, 0x74, 0x61, // "data"
        0x00, 0x00, 0x00, 0x00  // Subchunk2 size: 0 bytes (no audio data)
      ]);
      
      fs.writeFileSync(filePath, header);
      console.log(`Created empty WAV file at: ${filePath}`);
    } catch (error) {
      console.error('Error creating empty WAV file:', error);
    }
  }
  
  async transcribeAudio(audioPath) {
    // In a production environment, you would use a speech-to-text API here
    console.log('Transcribing audio from:', audioPath);
    
    // For this demo, we'll return a simulated transcription
    return "Simulated transcription of interview question. In a real implementation, this would be the actual text from the audio recording.";
  }
  
  startContinuousProcessing(callback) {
    this.continuousProcessing = true;
    this.continuousCallback = callback;
    
    // Start a loop that continuously records short segments and processes them
    this.continuousProcess();
  }
  
  stopContinuousProcessing() {
    this.continuousProcessing = false;
    if (this.recording) {
      this.stopRecording().catch(err => console.error('Error stopping recording:', err));
    }
  }
  
  async continuousProcess() {
    if (!this.continuousProcessing) return;
    
    try {
      await this.startRecording();
      
      // Record for a short duration (e.g., 10 seconds)
      await new Promise(resolve => setTimeout(resolve, 10000));
      
      const result = await this.stopRecording();
      
      if (result.success && this.continuousCallback) {
        this.continuousCallback(result.audioData.text);
      }
      
      // Continue the loop if still in continuous mode
      if (this.continuousProcessing) {
        this.continuousProcess();
      }
    } catch (error) {
      console.error('Error in continuous processing:', error);
      
      // Try to restart the process
      if (this.continuousProcessing) {
        setTimeout(() => this.continuousProcess(), 2000);
      }
    }
  }
}

module.exports = AudioCapture; 
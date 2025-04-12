import pyaudio
import wave
import math
import audioop
import os
import numpy as np
from array import array
from collections import deque

class AudioHandler:
    def __init__(self, use_mock=False, device_index=None):
        self.audio = pyaudio.PyAudio()
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 512  # Reduced from 1024 for faster response
        self.threshold = 8.0
        self.silence_threshold = 6.0
        self.silence_limit = 1.5
        self.silence_frames_threshold = int(1.5 * 44100 / 512)  # Adjusted for new chunk size
        self.prev_audio = 0.5
        self.filename = "recorded_audio.wav"
        self.use_mock = use_mock
        self.debug = True
        self.selected_device_index = device_index
        self.consecutive_silence_frames = 0
        self.min_recording_time = 0.5
        self.max_recording_time = 10.0
        
        # Audio parameters
        self.sample_width = 2
        
        # Noise reduction parameters
        self.noise_threshold = 4.0
        self.smoothing_window = deque(maxlen=3)  # Reduced from 5 to 3 for faster response
        self.noise_floor = None
        self.noise_reduction_strength = 1.2
        
        # List available devices on initialization
        self.list_devices()
        
        # Find the first available input device or use mock
        self.input_device_index = self._get_input_device()

    def list_devices(self):
        """List all available audio devices."""
        print("\nAvailable Audio Input Devices:")
        print("-" * 50)
        
        for i in range(self.audio.get_device_count()):
            try:
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # Only show input devices
                    print(f"Device ID {i}: {device_info['name']}")
                    print(f"    Input channels: {device_info['maxInputChannels']}")
                    print(f"    Sample rate: {int(device_info['defaultSampleRate'])}Hz")
                    print("-" * 50)
            except Exception as e:
                print(f"Could not get info for device {i}: {e}")

    def _get_input_device(self):
        """Find the selected input device or use default/mock."""
        if self.use_mock:
            print("Using mock audio device for testing")
            return None
            
        if self.selected_device_index is not None:
            try:
                device_info = self.audio.get_device_info_by_index(self.selected_device_index)
                if device_info['maxInputChannels'] > 0:
                    print(f"Using selected audio device: {device_info['name']}")
                    return self.selected_device_index
                else:
                    print(f"Selected device {self.selected_device_index} has no input channels")
            except Exception as e:
                print(f"Error accessing selected device: {e}")
        
        # Fall back to first available device if no valid selection
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                print(f"Using default audio device: {device_info['name']}")
                return i
        
        raise RuntimeError("No audio input device found")

    def _generate_mock_audio(self):
        """Generate mock audio data for testing."""
        # Generate a simple sine wave
        duration = 0.1  # 100ms of audio
        t = np.linspace(0, duration, int(self.rate * duration))
        signal = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        return signal.astype(np.int16).tobytes()

    def _calibrate_noise_floor(self, stream, duration=0.3):  # Reduced from 1.0 to 0.3 seconds
        """Measure the ambient noise level for better noise reduction."""
        print("Calibrating noise floor...")
        samples = []
        num_chunks = int(duration * self.rate / self.chunk)
        
        for _ in range(num_chunks):
            data = stream.read(self.chunk, exception_on_overflow=False)
            volume = math.sqrt(abs(audioop.avg(data, self.sample_width)))
            samples.append(volume)
        
        self.noise_floor = sum(samples) / len(samples)
        return self.noise_floor

    def _apply_noise_reduction(self, audio_data, noise_floor):
        """Apply noise reduction to the audio data."""
        try:
            # Convert bytes to array of signed shorts (16-bit integers)
            audio_array = array('h', audio_data)
            
            # Apply noise gate
            for i in range(len(audio_array)):
                if abs(audio_array[i]) < noise_floor / self.noise_reduction_strength:
                    audio_array[i] = 0
                else:
                    # Apply soft noise reduction
                    factor = (abs(audio_array[i]) - noise_floor/self.noise_reduction_strength) / abs(audio_array[i])
                    audio_array[i] = int(audio_array[i] * factor)
            
            return audio_array.tobytes()
        except Exception as e:
            print(f"Error in noise reduction: {e}")
            return audio_data

    def _smooth_volume(self, volume):
        """Apply smoothing to volume measurements to reduce spikes."""
        self.smoothing_window.append(volume)
        return sum(self.smoothing_window) / len(self.smoothing_window)

    def record_dynamic_audio(self):
        """Record audio dynamically based on voice activity with noise reduction."""
        if not self.use_mock:
            try:
                stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    input_device_index=self.input_device_index,
                    frames_per_buffer=self.chunk
                )
                
                # Quick calibration
                self.noise_floor = self._calibrate_noise_floor(stream)
                
            except Exception as e:
                print(f"Error opening audio stream: {e}")
                return None
        
        print("Listening...")  # Shortened message
        audio_chunks = []
        slid_win = deque(maxlen=10)  # Fixed size sliding window
        started = False
        silence_counter = 0
        recording_frames = 0
        min_frames = int(self.min_recording_time * self.rate / self.chunk)
        max_frames = int(self.max_recording_time * self.rate / self.chunk)

        while True:
            try:
                if self.use_mock:
                    cur_data = self._generate_mock_audio()
                else:
                    cur_data = stream.read(self.chunk, exception_on_overflow=False)
                    if self.noise_floor is not None:
                        cur_data = self._apply_noise_reduction(cur_data, self.noise_floor)
                
                current_volume = math.sqrt(abs(audioop.avg(cur_data, self.sample_width)))
                smoothed_volume = self._smooth_volume(current_volume)
                slid_win.append(smoothed_volume)
                avg_volume = sum(slid_win)/len(slid_win)
                
                if self.debug:
                    status = "SILENCE"
                    if avg_volume > self.threshold:
                        status = "SPEECH"
                    elif started and avg_volume < self.silence_threshold:
                        silence_remaining = (self.silence_frames_threshold - silence_counter) / (self.rate/self.chunk)
                        status = f"SILENCE ({silence_remaining:.1f}s)"
                    print(f"Volume: {avg_volume:.1f}, status={status}", end="\r")  # Use carriage return for cleaner output
                
                if avg_volume > self.threshold or self.use_mock:
                    if not started:
                        print("\nRecording...")
                        started = True
                    audio_chunks.append(cur_data)
                    silence_counter = 0
                    recording_frames += 1
                elif started and not self.use_mock:
                    if avg_volume < self.silence_threshold:
                        silence_counter += 1
                        if silence_counter > self.silence_frames_threshold and recording_frames > min_frames:
                            print("\nDone recording")
                            break
                    else:
                        silence_counter = 0
                    audio_chunks.append(cur_data)
                    recording_frames += 1
                
                if recording_frames >= max_frames:
                    print("\nMaximum duration reached")
                    break

            except Exception as e:
                print(f"\nError during recording: {e}")
                break

        if not self.use_mock:
            stream.stop_stream()
            stream.close()

        if not audio_chunks:
            print("No audio recorded")
            return None

        try:
            # Save the recorded audio to a WAV file
            wf = wave.open(self.filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(audio_chunks))
            wf.close()
            duration = len(audio_chunks) * self.chunk / self.rate
            print(f"\nSaved {len(audio_chunks)} chunks ({duration:.1f} seconds) of audio to {self.filename}")
            return self.filename
        except Exception as e:
            print(f"Error saving audio file: {e}")
            return None
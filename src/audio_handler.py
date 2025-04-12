import pyaudio
import wave
import math
import audioop
import os

class AudioHandler:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.format = pyaudio.paFloat32
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.threshold = 10000
        self.silence_threshold = 8000
        self.silence_limit = 1.5
        self.prev_audio = 0.5
        self.filename = "recorded_audio.wav"

    def record_dynamic_audio(self):
        """Record audio dynamically based on voice activity"""
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )

        print("Waiting for speech...")
        audio_chunks = []
        slid_win = []
        started = False
        silence_counter = 0
        rel = self.rate/self.chunk

        while True:
            try:
                cur_data = stream.read(self.chunk)
                current_volume = math.sqrt(abs(audioop.avg(cur_data, 4)))
                slid_win.append(current_volume)
                
                avg_volume = sum(slid_win)/len(slid_win)
                
                if avg_volume > self.threshold:
                    if not started:
                        print("Recording started...")
                        started = True
                    audio_chunks.append(cur_data)
                    silence_counter = 0
                elif started:
                    if avg_volume < self.silence_threshold:
                        silence_counter += 1
                        if silence_counter > self.silence_limit * rel:
                            print("Recording stopped")
                            break
                    audio_chunks.append(cur_data)
                
                if len(slid_win) > rel:
                    slid_win.pop(0)

            except Exception as e:
                print(f"Error during recording: {e}")
                break

        stream.stop_stream()
        stream.close()

        # Save the recorded audio to a WAV file
        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(audio_chunks))
        wf.close()

        return self.filename
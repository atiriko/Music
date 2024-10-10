import pyaudio
import wave

# Constants
CHUNK = 1024
FORMAT = pyaudio.paInt16
RATE = 44100
RECORD_SECONDS = 30
WAVE_OUTPUT_FILENAME = "output.wav"

def record_audio():
    p = pyaudio.PyAudio()

    p.get_device_count()
    for i in range(p.get_device_count()):
        print(i,p.get_device_info_by_index(i)["name"])

    print(p.get_default_output_device_info())
    print(p.get_device_info_by_index(4))
    # exit()
    # Try both 1 and 2 channels
    for channels in [1, 2]:
        try:
            # Open the default input device
            stream = p.open(
                format=FORMAT,
                channels=channels,
                rate=RATE,
                output=True,
                frames_per_buffer=CHUNK,
                input_device_index=4  # Try default device
            )

            print(f"Recording {channels} channel(s)")

            frames = []

            # Record audio for RECORD_SECONDS seconds
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)

            print("* done recording")

            # Close and terminate everything properly
            stream.stop_stream()
            stream.close()

            # Save audio file
            wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()

            print(f"Audio recorded and saved to {WAVE_OUTPUT_FILENAME}")
            return
        except Exception as e:
            print(f"Error with {channels} channels: {e}")

    # If all attempts fail, raise an exception
    raise RuntimeError("Unable to record audio with any channel configuration")

if __name__ == "__main__":
    try:
        record_audio()
    except Exception as e:
        print(f"An error occurred: {e}")

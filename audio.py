import zmq
import pyaudio




pa = pyaudio.PyAudio()

stream = pa.open(format= pyaudio.paFloat32,
                 channels=1,
                 rate= 44100,
                 input=True,
                 frames_per_buffer=1024)


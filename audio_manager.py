import numpy as np
import sounddevice as sd
from pyogg import OpusEncoder, OpusDecoder
import zmq
import threading
import queue
import pickle
from time import sleep
import weakref

from user import User

# Configurações
SAMPLE_RATE = 16000
CHUNK = 640
DTYPE  = 'float32'
CHANNELS = 1

class AudioManager():
    def __init__(self, user: User):
        self.user = weakref.ref(user)

        self.encoder = OpusEncoder()
        self.encoder.set_application("voip")  # Modo de baixa latência
        self.encoder.set_sampling_frequency(SAMPLE_RATE)
        self.encoder.set_channels(CHANNELS)
        
        self.decoder = OpusDecoder()
        self.decoder.set_channels(CHANNELS)
        self.decoder.set_sampling_frequency(SAMPLE_RATE)

        self.audio_queue = queue.Queue()

    def encode(self, audio: np.ndarray) -> bytes:
        """Compacta áudio para bytes."""
        return self.encoder.encode(audio.tobytes())

    def decode(self, data: bytes) -> np.ndarray:
        """Descompacta bytes para áudio."""
        decoded_bytes = self.decoder.decode(data)
        return np.frombuffer(decoded_bytes, dtype=np.float32)

    def setup_audio(self):
        # Configura captura de áudio
        self.input_stream = sd.InputStream(
            sample_rate=SAMPLE_RATE,
            blocksize=CHUNK,
            dtype= DTYPE ,
            channels=CHANNELS,
            callback=self.input_callback
        )
        
        # Configura reprodução de áudio
        self.output_stream = sd.OutputStream(
            sample_rate=SAMPLE_RATE,
            blocksize=CHUNK,
            dtype =DTYPE ,
            channels=CHANNELS,
            callback=self.output_callback
        )
        
        self.input_stream.start()
        self.output_stream.start()

    def stop(self):
        self.input_stream.stop()
        self.output_stream.stop()
        self.input_stream.close()
        self.output_stream.close()

    def input_callback(self, indata, frames, time, status):
        """Callback de captura de áudio"""
        self.user.publisher.send_multipart([b'audio', self.user.username.encode('utf-8'), self.encode(indata.copy())])
        
        # # Adiciona áudio local na mixagem (opcional)
        # self.audio_queue.put(indata.copy())

    def output_callback(self, outdata, frames, time, status):
        """Callback de reprodução de áudio com mixagem"""
        try:
            mix = np.zeros((CHUNK, CHANNELS), dtype=DTYPE)
            count = 0
            
            # Processa todos os chunks disponíveis
            while True:
                chunk = self.audio_queue.get_nowait()
                mix += chunk[:CHUNK]  # Garante tamanho correto
                count += 1
        except queue.Empty:
            pass
        
        # Prevenção de clipping
        if count > 0:
            mix /= self.user.peers
            mix = np.clip(mix, -1.0, 1.0)
        
        outdata[:] = mix

    def receive_audio(self, data: bytes):
        audio = self.decode(data)
        self.audio_queue.put(audio)

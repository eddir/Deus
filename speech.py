from abc import ABC, abstractmethod

from speechkit import Session, SpeechSynthesis, ShortAudioRecognition


class SpeechKit(ABC):
    def __init__(self, language):
        self.language = language

    @abstractmethod
    def recognize(self, audio_bytes):
        pass

    @abstractmethod
    def synthesize(self, text):
        pass


class YandexSpeechKit(SpeechKit):
    @property
    def voice(self):
        return {
            'ru-RU': 'zahar',
            'en-US': 'john',
        }[self.language]

    def __init__(self, api_key, language):
        session = Session.from_api_key(api_key, x_client_request_id_header=True, x_data_logging_enabled=True)
        self.synthesizer = SpeechSynthesis(session)
        self.recognizer = ShortAudioRecognition(session)
        super().__init__(language)

    def recognize(self, audio_bytes, sample_rate=48000):
        return self.recognizer.recognize(
            audio_bytes,
            format='lpcm',
            sampleRateHertz=sample_rate,
            lang=self.language
        ).strip()

    def synthesize(self, text):
        return self.synthesizer.synthesize_stream(
            text=text.strip(),
            voice=self.voice,
            lang=self.language,
            format='lpcm',
            sampleRateHertz='16000'
        )


class GoogleSpeechAPI(SpeechKit):
    def synthesize(self, text):
        pass

    def recognize(self, audio_bytes):
        pass
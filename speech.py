import os
from abc import ABC, abstractmethod

from speechkit import Session, SpeechSynthesis, ShortAudioRecognition
from google.cloud import speech
from google.cloud import texttospeech as tts


class SpeechKit(ABC):
    def __init__(self, language):
        self.language = language

    @staticmethod
    def create(provider, api_key, language, sample_rate):
        if provider == 'yandex':
            return YandexSpeechKit(api_key, language, sample_rate)
        elif provider == 'google':
            return GoogleSpeechAPI(api_key, language, sample_rate)
        else:
            raise ValueError(f'Unknown provider: {provider}')

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

    def __init__(self, api_key, language, sample_rate):
        session = Session.from_api_key(api_key, x_client_request_id_header=True, x_data_logging_enabled=True)
        self.synthesizer = SpeechSynthesis(session)
        self.recognizer = ShortAudioRecognition(session)
        self.sample_rate = sample_rate
        super().__init__(language)

    def recognize(self, audio_bytes):
        return self.recognizer.recognize(
            audio_bytes,
            format='lpcm',
            sampleRateHertz=self.sample_rate,
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
    # pycharm doesn't understand protobuf enums
    def __init__(self, api_key_location, language, sample_rate):
        # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "C:\\Users\\eddir\\google.json"
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = api_key_location
        self.recognizer = speech.SpeechClient()
        self.recognition_config = speech.RecognitionConfig(
            # encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            # sample_rate_hertz=sample_rate,
            language_code=language,
            enable_word_time_offsets=True
        )
        self.synthesize_config = tts.VoiceSelectionParams(
            language_code=language, name=language + '-Wavenet-B'
        )
        self.sample_rate = sample_rate
        super().__init__(language)

    def synthesize(self, text):
        text_input = tts.SynthesisInput(text=text)
        audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.sample_rate
        )

        client = tts.TextToSpeechClient()
        response = client.synthesize_speech(
            input=text_input, voice=self.synthesize_config, audio_config=audio_config
        )

        return response.audio_content

    def recognize(self, audio_bytes):
        result = self.recognizer.recognize(
            config=self.recognition_config,
            audio=speech.RecognitionAudio(content=audio_bytes)
        )
        if len(result.results) > 0:
            return result.results[0].alternatives[0].transcript
        else:
            return ''

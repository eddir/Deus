import audioop
import json
import logging
import os
import sys
import threading
import traceback

# fix https://github.com/protocolbuffers/protobuf/issues/3002
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# fix no console on windows mode
for _name in ('stdin', 'stdout', 'stderr'):
    if getattr(sys, _name) is None:
        setattr(sys, _name, open(os.devnull, 'r' if _name == 'stdin' else 'w'))

from speech import SpeechKit

from openai.error import RateLimitError
import tkinter as tk
import io
import wave
from tkinter import messagebox, filedialog

import openai as openai
import pyaudio
# todo: change back to tiktoken when fix openai/tiktoken/issues/43
# tiktoken shows better performance and needs much less dependencies
# from tiktoken import Tokenizer
from transformers import GPT2Tokenizer

# init global logger to save logs in file
logger = logging.getLogger('Assistant')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

try:
    # noinspection PyUnresolvedReferences
    os.chdir(sys._MEIPASS)
except AttributeError:
    pass

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

I18N = {
    "en-US": {
        "title": "Deus",
        "recording": "Recording...",
        "config": "Config",
        "key_explanation": "Specify one of the keys in the appropriate field. \n"
                           "If you use Yandex Speech API, then enter the string key \n"
                           "If you use Google Speech API, then select the path to the json file with the key \n",
        "openai_api_key": "OpenAI API Key",
        "speech_api_key": "Yandex Speech API Key",
        "speech_key_location": "Speech API Key Location (json file)",
        "speech_provider": "Speech provider",
        "threshold": "Microphone threshold",
        "language": "Language",
        "hide_buttons": "Hide buttons",
        "save": "Save",
        "cancel": "Cancel",
        "error": "Error",
        "openai_overload": "Currently OpenAI API is overloaded. Please try again later.",
        "openai_api_key_invalid": "OpenAI API Key is invalid. Please check it and try again.",
        "speech_api_key_invalid": "Speech API Key is invalid. Please check it and try again.",
        "threshold_invalid": "Threshold is invalid. Please check it and try again.",
        "you": "You",
        "deus": "Deus",
    },
    "ru-RU": {
        "title": "Деус",
        "recording": "Запись...",
        "config": "Настройки",
        "key_explanation": "Укажите один из ключей в нужном поле. \n"
                           "Если вы используете Yandex Speech API, то впишите строковый ключ \n"
                           "Если вы используете Google Speech API, то выберите путь к json файлу с ключом \n",
        "openai_api_key": "OpenAI API ключ",
        "speech_api_key": "Speech API ключ",
        "speech_key_location": "Google Speech API ключ (json файл)",
        "speech_provider": "Речевой провайдер",
        "threshold": "Чувствительность микрофона",
        "language": "Язык",
        "hide_buttons": "Скрыть кнопки",
        "save": "Сохранить",
        "cancel": "Отмена",
        "error": "Ошибка",
        "openai_overload": "Сейчас OpenAI API перегружен. Пожалуйста, попробуйте позже.",
        "openai_api_key_invalid": "OpenAI API Key неверный. Пожалуйста, проверьте его и попробуйте снова.",
        "speech_api_key_invalid": "Speech API Key неверный. Пожалуйста, проверьте его и попробуйте снова.",
        "threshold_invalid": "Порог неверный. Пожалуйста, проверьте его и попробуйте снова.",
        "you": "Вы",
        "deus": "Деус",
    }
}


class AssistantApp:

    @property
    def i18n(self):
        if self.language in I18N:
            return I18N[self.language]
        else:
            return I18N["en-US"]

    def __init__(self, master):
        try:
            self.SPEECH_KEY = str("")
            self.SPEECH_KEY_LOCATION = str("")
            self.openai_entry = None
            self.speech_key_entry = None
            self.speech_key_location_entry = None
            self.speech_provider_value = None
            self.hide_buttons_var = None
            self.language = "en-US"
            self.hide_buttons = True
            self.speech_provider = "google"
            self.threshold_entry = None
            self.speech = None
            self.config_window = None
            self.threshold = 500
            self.recordingSampleRate = 16000

            self.label = None
            self.frames = [tk.PhotoImage(file='./deus.gif', format='gif -index %i' % i) for i in range(102)]
            self.conversation = []

            self.mode = "chat"

            self.master = master
            self.font_size = 18
            self.max_width = self.master.winfo_screenwidth()

            # master.minsize(400, 200)
            master.title(self.i18n["title"])
            master.maxsize(width=master.winfo_screenwidth(), height=master.winfo_screenheight())
            master.iconbitmap("logo.ico")

            # Setting black background and white text
            self.background_color = '#37474f'
            self.background_second_color = '#455a64'
            self.input_text_color = '#e0e0e0'
            self.master.configure(bg=self.background_color)

            scrollbar = tk.Scrollbar(self.master, bg=self.background_color)
            scrollbar.grid(row=0, column=1, sticky='ns')
            # make the scrollbar be unvisible
            scrollbar.grid_remove()

            self.input_text = tk.Text(self.master,
                                      yscrollcommand=scrollbar.set,
                                      font=("Helvetica", self.font_size),
                                      width=self.max_width,
                                      wrap='word',
                                      spacing1=10,
                                      spacing2=10,
                                      bg=self.background_color,
                                      fg=self.input_text_color)
            self.input_text.grid(row=0, column=0, sticky='nsew')
            self.master.rowconfigure(0, weight=1)  # set row 0 to fill remaining space

            # beautiful button for recording in the bottom right corner
            self.reset_button = tk.Button(self.master, text="Reset", command=self.reset, bg='#b0bec5')
            self.master.columnconfigure(0, weight=1)  # set column 1 to fill remaining space
            self.record_button = tk.Button(self.master, text="Record", command=self.record, bg='#b0bec5')
            self.switcher = tk.Button(self.master, text="Switch", command=self.switch, bg='#b0bec5')

            scrollbar.config(command=self.input_text.yview)
            self.input_text.bind('<Control-MouseWheel>', self.on_mousewheel)
            self.master.bind('<space>', self.start_recording)
            self.master.bind('<r>', self.reset)
            self.master.bind('<s>', self.switch)
            self.master.bind('<c>', self.show_config_prompt)
            self.master.bind('<h>', self.help)
            self.master.bind('<?>', self.help)
            self.master.bind('<Button-3>', self.help)

            self.switch()

            self.language_entry_value = tk.StringVar(master=self.master, value=self.language)
            self.load_config()

            if not self.hide_buttons:
                self.reset_button.grid(row=1, column=0, sticky='w', padx=5, pady=5)
                self.record_button.grid(row=1, column=0, sticky='e', padx=5, pady=5)
                self.switcher.grid(row=1, column=0, sticky='s', padx=15, pady=5)
                self.master.columnconfigure(0, weight=1)  # set column 0 to fill remaining space

        except Exception as e:
            self.fatal("Couldn't initialize the application", str(e))

    def auth(self, openai_key=None):
        try:
            key = self.SPEECH_KEY if self.speech_provider == "yandex" else self.SPEECH_KEY_LOCATION
            self.speech = SpeechKit.create(self.speech_provider, key, self.language, self.recordingSampleRate)
        except Exception as e:
            self.error(self.i18n['speech_api_key_invalid'], str(e))
            self.show_config_prompt()
        try:
            openai.api_key = openai_key
            # check if api key is valid
            openai.Engine.list()
        except Exception as e:
            self.error(self.i18n['openai_api_key_invalid'], str(e))
            self.show_config_prompt()

    def fatal(self, title, message):
        logger.error(message)
        logger.error(traceback.format_exc())
        messagebox.showerror(title, message)
        self.master.destroy()
        self.master.quit()

    @staticmethod
    def error(title, message):
        logger.error(message)
        messagebox.showerror(title, message)

    def load_config(self):
        try:
            with open(os.getenv('APPDATA') + '\\deus\\config.json', 'r') as f:
                config = json.load(f)
                self.SPEECH_KEY = config.get('yc_key')
                self.SPEECH_KEY_LOCATION = config.get('gc_key')
                openai_key = config.get('openai_key', None)
                self.speech_provider = config.get('speech_provider', 'google')
                self.language = config.get('language', 'en-US')
                self.language_entry_value.set(self.language)
                self.threshold = config.get('threshold', 500)
                self.hide_buttons = config.get('hide_buttons', True)
                self.auth(openai_key)
        except FileNotFoundError:
            # show prompt to enter api keys
            self.show_config_prompt()

    def show_config_prompt(self, event=None):
        # create new window
        self.config_window = tk.Toplevel(self.master)
        self.config_window.title(self.i18n['config'])
        self.config_window.maxsize(width=self.config_window.winfo_screenwidth(),
                                   height=self.config_window.winfo_screenheight())
        self.config_window.configure(bg=self.background_color)

        color_config = {
            'bg': self.background_color,
            'fg': self.input_text_color,
            'activebackground': self.input_text_color,
            'activeforeground': self.background_color,
            'highlightbackground': self.input_text_color,
            'highlightcolor': self.input_text_color,
            'highlightthickness': 0,
        }

        # create label for OpenAI API key
        openai_label = tk.Label(self.config_window, text=self.i18n['openai_api_key'],
                                bg=self.background_color, fg=self.input_text_color)
        openai_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
        # create entry for OpenAI API key
        self.openai_entry = tk.Entry(self.config_window, bg=self.background_color, fg=self.input_text_color,
                                     textvariable=tk.StringVar(self.config_window, value=openai.api_key))
        self.openai_entry.grid(row=0, column=1, sticky='w', padx=5, pady=5)

        # explain how to get appropiate api keys
        key_explanation = tk.Label(self.config_window, text=self.i18n['key_explanation'],
                                   bg=self.background_color, fg=self.input_text_color, anchor='w', justify='left')
        key_explanation.grid(row=1, column=0, sticky='w', padx=5, pady=5)

        # create label for Yandex Cloud API key
        yc_label = tk.Label(self.config_window, text=self.i18n['speech_api_key'],
                            bg=self.background_color, fg=self.input_text_color)
        yc_label.grid(row=2, column=0, sticky='w', padx=5, pady=5)
        # create entry for Yandex Cloud API key
        self.speech_key_entry = tk.Entry(self.config_window, bg=self.background_color, fg=self.input_text_color,
                                         textvariable=tk.StringVar(self.config_window, value=self.SPEECH_KEY))
        self.speech_key_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        # speech key location for google cloud
        speech_key_location_label = tk.Label(self.config_window, text=self.i18n['speech_key_location'],
                                             bg=self.background_color, fg=self.input_text_color)
        speech_key_location_label.grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.speech_key_location_entry = tk.Entry(self.config_window, bg=self.background_color,
                                                  fg=self.input_text_color,
                                                  textvariable=tk.StringVar(
                                                      self.config_window, value=self.SPEECH_KEY_LOCATION))
        self.speech_key_location_entry.grid(row=3, column=1, sticky='w', padx=5, pady=5)
        button_browse = tk.Button(self.config_window, text="Browse", command=self.open_file_dialog)
        button_browse.config(**color_config)
        button_browse.grid(row=3, column=3, sticky='w', padx=5, pady=5)

        # select yandex or google speech provider dropdown
        speech_provider_label = tk.Label(self.config_window, text=self.i18n['speech_provider'],
                                         bg=self.background_color, fg=self.input_text_color)
        speech_provider_label.grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.speech_provider_value = tk.StringVar(self.config_window, value=self.speech_provider)
        speech_provider_dropdown = tk.OptionMenu(self.config_window, self.speech_provider_value, 'google', 'yandex')
        speech_provider_dropdown.config(**color_config)
        speech_provider_dropdown.grid(row=4, column=1, sticky='w', padx=5, pady=5)

        # select language from dropdown
        language_label = tk.Label(self.config_window, text=self.i18n['language'],
                                  bg=self.background_color, fg=self.input_text_color)
        language_label.grid(row=5, column=0, sticky='w', padx=5, pady=5)
        language_dropdown = tk.OptionMenu(self.config_window, self.language_entry_value,
                                          'ar-SA', 'bg-BG', 'ca-ES', 'cs-CZ', 'da-DK', 'de-DE', 'el-GR', 'en-US',
                                          'es-ES', 'fa-IR', 'fi-FI', 'fr-FR', 'he-IL', 'hi-IN', 'hr-HR', 'hu-HU',
                                          'id-ID', 'it-IT', 'ja-JP', 'ko-KR', 'lt-LT', 'lv-LV', 'ms-MY', 'nb-NO',
                                          'nl-NL', 'pl-PL', 'pt-BR', 'ro-RO', 'ru-RU', 'sk-SK', 'sl-SI', 'sv-SE',
                                          'th-TH', 'tr-TR', 'uk-UA', 'vi-VN', 'zh-CN')
        language_dropdown.config(**color_config)
        language_dropdown.grid(row=5, column=1, sticky='w', padx=5, pady=5)

        # micrphone sensitivity
        threshold_label = tk.Label(self.config_window, text=self.i18n['threshold'],
                                   bg=self.background_color, fg=self.input_text_color)
        threshold_label.grid(row=6, column=0, sticky='w', padx=5, pady=5)

        self.threshold_entry = tk.Entry(self.config_window, bg=self.background_color, fg=self.input_text_color,
                                        textvariable=tk.IntVar(self.config_window, value=self.threshold))
        self.threshold_entry.grid(row=6, column=1, sticky='w', padx=5, pady=5)

        # checkbox to hide buttons
        self.hide_buttons_var = tk.IntVar(self.config_window, value=self.hide_buttons)
        hide_buttons_checkbox = tk.Checkbutton(self.config_window, text=self.i18n['hide_buttons'],
                                               variable=self.hide_buttons_var)
        hide_buttons_checkbox.config(**color_config)
        hide_buttons_checkbox.grid(row=7, column=0, sticky='w', padx=5, pady=5)

        # create button to save config
        save_button = tk.Button(self.config_window, text=self.i18n['save'], command=self.save_config,
                                bg='#b0bec5')
        save_button.grid(row=8, column=0, sticky='w', padx=5, pady=5)

        # create button to cancel config
        cancel_button = tk.Button(self.config_window, text=self.i18n['cancel'], command=self.cancel_config,
                                  bg='#b0bec5')
        cancel_button.grid(row=8, column=1, sticky='w', padx=5, pady=5)

    def open_file_dialog(self):
        filename = filedialog.askopenfilename()
        self.speech_key_location_entry.delete(0, tk.END)
        self.speech_key_location_entry.insert(0, filename)

    def save_config(self):
        try:
            self.SPEECH_KEY = self.speech_key_entry.get()
            openai.api_key = self.openai_entry.get()
            self.speech_provider = self.speech_provider_value.get()
            self.language = str(self.language_entry_value.get())
            self.threshold = int(self.threshold_entry.get())
            self.hide_buttons = bool(self.hide_buttons_var.get())

            if not os.path.exists(os.getenv('APPDATA') + '\\deus'):
                os.makedirs(os.getenv('APPDATA') + '\\deus')

            self.SPEECH_KEY_LOCATION = self.speech_key_location_entry.get()
            if self.SPEECH_KEY_LOCATION:
                # copy speech key to appdata
                with open(self.SPEECH_KEY_LOCATION, 'r') as f:
                    key_data = f.read()

                self.SPEECH_KEY_LOCATION = os.getenv('APPDATA') + '\\deus\\google.json'

                with open(self.SPEECH_KEY_LOCATION, 'w') as f:
                    f.write(key_data)

            with open(os.getenv('APPDATA') + '\\deus\\config.json', 'w') as f:
                json.dump({
                    'yc_key': self.SPEECH_KEY,
                    'gc_key': self.SPEECH_KEY_LOCATION,
                    'openai_key': openai.api_key,
                    'speech_provider': self.speech_provider,
                    'language': self.language,
                    'threshold': self.threshold,
                    'hide_buttons': self.hide_buttons
                }, f)

            self.config_window.destroy()
            self.auth(openai.api_key)
        except Exception as e:
            self.fatal("Couldn't save config", str(e))

    def cancel_config(self):
        self.config_window.destroy()

    def start_recording(self, event=None):
        t = threading.Thread(target=lambda: self.record())
        t.start()

    def record(self):
        while True:
            try:
                self.input_text.config(bg=self.background_second_color)
                self.master.title(self.i18n['title'] + ' - ' + self.i18n['recording'])
                self.master.update()

                sample_rate = self.recordingSampleRate
                # Записываем аудио продолжительностью 3 секунды
                audio_data = self.record_audio(seconds=30, sample_rate=sample_rate, threshold=self.threshold)
                self.master.title(self.i18n['title'])
                self.input_text.config(bg=self.background_color)
                self.master.update()

                if len(audio_data) > 0:
                    text = self.speech.recognize(audio_data)

                    if len(text) > 0:
                        self.master.update()

                        self.conversation.append({"role": "user", "content": text})
                        self.cut_conversation()
                        self.update_text()

                        response = self.chat_gpt()
                        self.conversation.append({"role": "assistant", "content": response})

                        self.update_text()
                        self.play_audio(self.speech.synthesize(response))
                        continue
                return
            except RateLimitError:
                messagebox.showerror("Error", self.i18n['rate_limit_error'])
                return
            except Exception as e:
                self.fatal("Error", "%s - %s" % (type(e).__name__, e))
                return

    def switch(self, event=None):
        if self.mode == "chat":
            self.mode = "eye"
            # убираем текстовое поле, вставляем гифку
            self.input_text.grid_forget()

            self.label = tk.Label(self.master, width=440, height=352, bg='black')
            self.label.grid(row=0, column=0, sticky='nsew')
            self.master.after(0, self.update_gif, 0)
            self.master.configure(bg='black')

            self.master.rowconfigure(0, weight=1)  # set row 0 to fill remaining space
            self.master.columnconfigure(0, weight=1)  # set column 0 to fill remaining space
            self.master.update()
        else:
            self.mode = "chat"
            self.label.grid_forget()
            self.input_text.grid(row=0, column=0, sticky='nsew')
            self.master.rowconfigure(0, weight=1)
            self.master.configure(bg=self.background_color)

    def reset(self, event=None):
        self.conversation = []
        self.update_text()

    @staticmethod
    def help(event=None):
        # alert with text
        messagebox.showinfo("Help",
                            "Press 'r' to reset conversation\n"
                            "Press 's' to switch between chat and eye mode\n"
                            "Press 'c' to open config\n"
                            "Press 'space' to start recording")

    def update_gif(self, ind):
        if self.mode == "eye":
            frame = self.frames[ind]
            ind += 1
            if ind > 30:  # With this condition it will play gif infinitely
                ind = 0
            self.label.configure(image=frame)
            self.master.after(100, self.update_gif, ind)

    def update_text(self):
        text = ""
        for message in self.conversation:
            if message["role"] == "user":
                text += "%s: %s \n" % (self.i18n['you'], message["content"])

            if message["role"] == "assistant":
                text += "%s: %s \n" % (self.i18n['deus'], message["content"])

        self.input_text.delete(1.0, tk.END)
        self.input_text.insert(tk.END, text)
        self.input_text.see(tk.END)
        self.master.update()

    @staticmethod
    def play_audio(audio_data):
        """
        Проигрывает аудиофайл
        """
        # создаем объект для воспроизведения аудио
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            output=True
        )

        # воспроизводим аудиофайл
        stream.write(audio_data)

        # закрываем поток
        stream.stop_stream()
        stream.close()
        p.terminate()

    @staticmethod
    def record_audio(seconds, sample_rate, chunk_size=4000, num_channels=1, wait=10, threshold=500) -> bytes:
        """
        Записывает аудио данной продолжительности и возвращает бинарный объект с данными

        :param threshold: пороговое значение для начала записи
        :param wait: время ожидания перед началом записи
        :param integer seconds: Время записи в секундах
        :param integer sample_rate: частота дискретизации, такая же
            какую вы указали в параметре sampleRateHertz
        :param integer chunk_size: размер семпла записи
        :param integer num_channels: количество каналов, в режимер синхронного
            распознавания спичкит принимает моно дорожку,
            поэтому стоит оставить значение `1`
        :return: Возвращает объект BytesIO с аудио данными в формате WAV
        :rtype: bytes
        """

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=num_channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size
        )
        frames = []
        try:
            recording_state = 0
            for _ in range(1, int(sample_rate / chunk_size * seconds)):
                # todo: change to while True to not limit recording time because of silence
                data = stream.read(chunk_size)
                # Start recording when the audio input exceeds a threshold
                # and stop recording when it drops below a threshold
                rms = audioop.rms(data, 2)
                if recording_state == 0:
                    if rms > threshold:
                        recording_state = 1
                    else:
                        wait -= 1
                        if wait <= 0:
                            return bytes()
                        continue
                if recording_state > 0:
                    if rms <= threshold:
                        recording_state += 1
                        if recording_state > 3:
                            break
                    else:
                        recording_state = 1
                frames.append(data)
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

        container = io.BytesIO()
        wf = wave.open(container, 'wb')
        wf.setnchannels(num_channels)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
        container.seek(0)
        return container.getvalue()

    def on_mousewheel(self, event):
        if event.delta > 0:
            self.font_size += 2
        else:
            self.font_size -= 2

        self.input_text.config(font=("Helvetica", self.font_size))

    def chat_gpt(self):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.conversation,
            temperature=0.6,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        logger.info("%d from this" % (response['usage']['total_tokens']))
        return response['choices'][0]['message']['content']

    def cut_conversation(self):
        conversation = self.conversation
        # if list given - convert to string
        if type(conversation) == list:
            # conversation is key: value string
            string = ""
            for message in conversation:
                string += f"{message['role']}: {message['content']}"
        elif type(conversation) == str:
            string = conversation
        else:
            raise Exception("Unknown conversation type")

        # if tokens length is more than 1024 - cut it
        while len(tokenizer.encode(string)) > 3000:
            if type(conversation) == list:
                # cut from the beginning
                conversation.pop(0)
                string = ""
                for message in conversation:
                    string += f"{message['role']}: {message['content']}"
            else:
                # cut from the beginning
                conversation = conversation[conversation.find("\n") + 1:]
                string = conversation

        self.conversation = conversation


def main():
    root = tk.Tk()
    AssistantApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()

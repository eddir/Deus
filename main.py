import audioop
import logging
import threading
import tkinter as tk
import io
import wave
from tkinter import messagebox

import openai as openai
import pyaudio
import tiktoken as tiktoken
from speechkit import Session, SpeechSynthesis, ShortAudioRecognition

# init global logger to save logs in file
logger = logging.getLogger('Assistant')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

enc = tiktoken.encoding_for_model("text-davinci-003")


class AssistantApp:

    def __init__(self, master):
        try:
            self.openai_entry = None
            self.yc_entry = None
            self.recognizeShortAudio = None
            self.synthesizeAudio = None
            self.config_window = None
            self.label = None
            self.frames = [tk.PhotoImage(file='./deus.gif', format='gif -index %i' % i) for i in range(102)]
            self.conversation = []

            self.mode = "chat"

            self.master = master
            self.font_size = 18
            self.max_width = self.master.winfo_screenwidth()

            # master.minsize(400, 200)
            master.title("Deus")
            master.maxsize(width=master.winfo_screenwidth(), height=master.winfo_screenheight())

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
            # self.reset_button = tk.Button(self.master, text="Reset", command=self.reset, bg='#b0bec5')
            # self.reset_button.grid(row=1, column=0, sticky='w', padx=5, pady=5)
            # self.master.columnconfigure(0, weight=1)  # set column 1 to fill remaining space
            # self.record_button = tk.Button(self.master, text="Record", command=self.record, bg='#b0bec5')
            # self.record_button.grid(row=1, column=0, sticky='e', padx=5, pady=5)
            # self.switcher = tk.Button(self.master, text="Switch", command=self.switch, bg='#b0bec5')
            # self.switcher.grid(row=1, column=0, sticky='s', padx=15, pady=5)
            # self.master.columnconfigure(0, weight=1)  # set column 0 to fill remaining space

            scrollbar.config(command=self.input_text.yview)
            self.input_text.bind('<Control-MouseWheel>', self.on_mousewheel)
            self.master.bind('<space>', self.start_recording)
            self.master.bind('<r>', self.reset)
            self.master.bind('<s>', self.switch)
            # right mouse click on any place of the window
            self.master.bind('<Button-3>', self.help)

            self.switch()

            self.YC_KEY_SECRET = str("")
            self.load_config()

        except Exception as e:
            self.fatal("Couldn't initialize the application", str(e))

    def auth(self, yc_key=None, openai_key=None):
        try:
            session = Session.from_api_key(yc_key, x_client_request_id_header=True, x_data_logging_enabled=True)
            self.synthesizeAudio = SpeechSynthesis(session)
            self.recognizeShortAudio = ShortAudioRecognition(session)
        except Exception as e:
            self.error("Couldn't authorize in Yandex Cloud", str(e))
            self.show_config_prompt()
        try:
            openai.api_key = openai_key
            # check if api key is valid
            openai.Engine.list()
        except Exception as e:
            self.error("Couldn't authorize in OpenAI", str(e))
            self.show_config_prompt()

    def fatal(self, title, message):
        logger.error(message)
        messagebox.showerror(title, message)
        self.master.destroy()
        self.master.quit()

    @staticmethod
    def error(title, message):
        logger.error(message)
        messagebox.showerror(title, message)

    def load_config(self):
        try:
            with open('credentials.txt', 'r') as f:
                yc_key = f.readline().strip()
                openai_key = f.readline().strip()
                self.auth(yc_key, openai_key)
        except FileNotFoundError:
            # show prompt to enter api keys
            self.show_config_prompt()

    def show_config_prompt(self):
        # create new window
        self.config_window = tk.Toplevel(self.master)
        self.config_window.title("Config")
        self.config_window.maxsize(width=self.config_window.winfo_screenwidth(),
                                   height=self.config_window.winfo_screenheight())
        self.config_window.configure(bg=self.background_color)

        # create label for Yandex Cloud API key
        yc_label = tk.Label(self.config_window, text="Yandex Cloud API key",
                            bg=self.background_color, fg=self.input_text_color)
        yc_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)

        # create entry for Yandex Cloud API key
        self.yc_entry = tk.Entry(self.config_window, bg=self.background_color, fg=self.input_text_color)
        self.yc_entry.grid(row=0, column=1, sticky='w', padx=5, pady=5)

        # create label for OpenAI API key
        openai_label = tk.Label(self.config_window, text="OpenAI API key",
                                bg=self.background_color, fg=self.input_text_color)
        openai_label.grid(row=1, column=0, sticky='w', padx=5, pady=5)

        # create entry for OpenAI API key
        self.openai_entry = tk.Entry(self.config_window, bg=self.background_color, fg=self.input_text_color)
        self.openai_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        # create button to save config
        save_button = tk.Button(self.config_window, text="Save", command=self.save_config, bg='#b0bec5')
        save_button.grid(row=2, column=0, sticky='w', padx=5, pady=5)

        # create button to cancel config
        cancel_button = tk.Button(self.config_window, text="Cancel", command=self.cancel_config, bg='#b0bec5')
        cancel_button.grid(row=2, column=1, sticky='w', padx=5, pady=5)

    def save_config(self):
        try:
            self.YC_KEY_SECRET = self.yc_entry.get()
            openai.api_key = self.openai_entry.get()
            self.config_window.destroy()

            with open('credentials.txt', 'w') as f:
                f.write(self.YC_KEY_SECRET + ' \n' + openai.api_key)

            self.auth(self.YC_KEY_SECRET, openai.api_key)
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
                self.master.update()

                sample_rate = 16000
                # Записываем аудио продолжительностью 3 секунды
                audio_data = self.record_audio(seconds=30, sample_rate=sample_rate)

                if len(audio_data) > 0:
                    text = self.recognize(audio_data, sample_rate)

                    self.input_text.config(bg=self.background_color)
            self.master.update()

            self.conversation.append({"role": "user", "content": text})
            self.cut_conversation()

            response = self.chat_gpt()
            self.conversation.append({"role": "assistant", "content": response})

                    self.update_text()
                    self.speech(response)
                else:
                    return
            except Exception as e:
                self.fatal("Error", str(e))
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
                text += "Вы: " + message["content"] + " \n"

            if message["role"] == "assistant":
                text += "Ассистент: " + message["content"] + " \n"

        self.input_text.delete(1.0, tk.END)
        self.input_text.insert(tk.END, text)
        self.input_text.see(tk.END)
        self.master.update()

    def recognize(self, audio_data, sample_rate):
        """
        Распознает речь. Возвращает текст
        """
        return self.recognizeShortAudio.recognize(audio_data, format='lpcm', sampleRateHertz=sample_rate)

    def speech(self, text):
        """
        Произносит текст
        :param text:
        :return:
        """
        audio_data = self.synthesizeAudio.synthesize_stream(
            text=text,
            voice='zahar', format='lpcm', sampleRateHertz='16000'
        )
        # воспроизводим аудиофайл
        self.play_audio(audio_data)

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
    def record_audio(seconds, sample_rate, chunk_size=4000, num_channels=1, wait=10) -> bytes:
        """
        Записывает аудио данной продолжительности и возвращает бинарный объект с данными

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
                data = stream.read(chunk_size)
                # Start recording when the audio input exceeds a threshold
                # and stop recording when it drops below a threshold
                threshold = 500
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
        while len(enc.encode(string)) > 3000:
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

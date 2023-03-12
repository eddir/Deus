<p align="center">
<img src="https://raw.githubusercontent.com/eddir/Deus/readme/.github/readme/deus.png" loading="eager"  alt="The Deus logo"/>
<br>
<b>Deus assistant from the lovely Israel TV series <a href="https://en.wikipedia.org/wiki/Deus_(TV_series)">דאוס</a></b>
</p>

[English version below](#english)

# דאוס

בשנת 2008 הייתה משדרת בערוץ הילדים סדרת מדע בדיונית מפורסמת בשם "דאוס". הוא מספרת על הבניית המוח המלאכותי. ועכשיו, 15 שנים מאוחר יותר, אנו חיים את האירועים הללו כבר בחיים האמיתיים. אנו יכולים להרגיש כמו גיבורי הסדרה ההיא. החלטתי להפוך את החלום למציאות. חלומות מתגשמים, ידידי.
## תיאור

דאוס היא עוזרת דיגיטלית שנועדה לבצע מגוון משימות. העוזרת היא יישום חלונות המשתמש בזיהוי ובהקרנת דיבור כדי לתקשר עם המשתמש. המראה של העוזרת דומה למראה של העוזרת האנושית העין-בעין מסדרת הטלוויזיה. העוזרת היא מבוססת על המודל ChatGPT, שהוא מודל GPT-2 שהוכשר על ידי צוות OpenAI על סט נתונים גדול של שיחות. העוזרת יכולה לענות על שאלות, לבצע משימות ואפילו לספר סיפורים באמצעות הקרנת דיבור. לנוחיותך, העוזרת יכולה להשתמש בשירותי Google Cloud Text-to-Speech API או Yandex SpeechKit API כדי להקרין ולזהות דיבור. ייתכן שתצטרך גם לספק מפתחות API שלך עצמך כדי שהעוזרת תעבוד כראוי:

* [Google Cloud Text-to-Speech API](https://cloud.google.com/text-to-speech) או [Yandex SpeechKit API](https://cloud.yandex.com/services/speechkit)
* [OpenAI API](https://platform.openai.com/) למודל ChatGPT

כל שירות יש לו מודל תמחור שלו. אנא קרא את התיעוד של כל שירות כדי ללמוד עוד על התמחור. עבור משתמשים חדשים הם מציעים תקופת ניסיון חינם עם מספר מוגבל של בקשות.

## דרישות

* Windows 8 או גרסה מאוחרת יותר (נבדק על Windows 11 64-bit)
* חיבור אינטרנט יציב
* מיקרופון
* דפסים או אוזניות

## התקנה

השג את הגרסה האחרונה מ[קישור ההורדה](https://github.com/eddir/Deus/releases/download/0.2.0/Deus.exe) והריץ אותה.

בפעם הראשונה, העוזר יבקש ממך לספק את מפתחות האפי שלך. אתה יכול למצוא את המפתחות
[קונסולת ענן גוגל](https://console.cloud.google.com/) (קובץ ג ' סון) או 
[יאנדקס ענן קונסולת](https://console.cloud.yandex.com/) (תלוי בשירות שתבחר). 
אתה יכול גם למצוא את מפתח הצ ' אט-פי-איי ב [לוח המחוונים של אופנאי] (https://platform.openai.com/).

אתה יכול לבחור את השירות שאתה רוצה להשתמש בו לסינתזת דיבור והכרה ושפה. אם הסתבכת בזיהוי דיבור, תוכל לנסות להפחית את הרגישות של מנוע זיהוי הדיבור על ידי שינוי ערך סף המיקרופון. ככל שהערך נמוך יותר, כך מנוע זיהוי הדיבור יהיה רגיש יותר.

אם אתה מכיר את שורת הפקודה ומעדיף ליצור הפעלה עצמאית בעצמך, תוכל להשתמש בפקודה הבאה:

```bash
pyinstaller --noconfirm --onefile --windowed --icon "./logo.ico" --name "Deus" --collect-all "transformers" --collect-all "tqdm" --collect-all "regex" --collect-all "requests" --collect-all "packaging" --collect-all "filelock" --collect-all "numpy" --collect-all "tokenizers" --collect-all "google-cloud-core" --add-data "./deus.gif;." --add-data "./logo.ico;."  "./main.py"
```

ההפעלה תיווצר בתיקייה `dist`.

## שימוש

לחץ על מקש הרווח כדי להתחיל את העוזר. הוא יקשיב לקול שלך וינסה להבין מה שאמרת.
אם העוזר הבין אותך, הוא ינסה לענות על השאלה שלך.

אם ברצונך לאפס את השיחה, לחץ על מקש ה-`r`. אם ברצונך לפתוח את ההגדרות, לחץ על מקש ה-`c`.
לעזרה, לחץ על מקש ה-`h` או לחץ עם העכבר הימני על חלון העוזר.

באפשרותך להחליף את מראה העוזר על ידי לחיצה על מקש ה-`s`.

## רישיון

MIT License

# English

## Disclaimer

_This project is not affiliated with the creator of the TV series, the actors, the production company, or any other 
entity related to the TV series. This project is a fan-made project. The project is not intended to be used for any 
commercial, illegal, malicious, harmful or immoral purposes._

_The software is provided "as is", without warranty of any kind, express or implied, including but not limited to the 
warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or
copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or
otherwise, arising from, out of or in connection with the software or the use or other dealings in the software._

## Description

Deus is a Python-based assistant that can be used to perform various tasks. It is a window-based application that
uses speech recognition and speech synthesis to communicate with the user. The appearance of the assistant resembles
the appearance of the original human-eye assistant from the TV series. The assistant is based on the ChatGPT
model, which is a GPT-2 model that was trained by the OpenAI team on a huge dataset of conversations. The assistant
is able to answer questions, perform tasks, and even tell jokes using speech synthesis. For your convenience, the
assistant can use the Google Cloud Text-to-Speech API or the Yandex SpeechKit API to synthesize and recognize speech.
You may also need to provide your own API keys for the assistant to work properly: 

* [Google Cloud Text-to-Speech API](https://cloud.google.com/text-to-speech) or [Yandex SpeechKit API](https://cloud.yandex.com/services/speechkit)
* [OpenAI API](https://platform.openai.com/) for the ChatGPT model

Each service has its own pricing model. Please read the documentation of each service to learn more about the pricing. 
For new users they offer a free trial period with a limited number of requests.

## Requirements

* Windows 8 or later (tested on Windows 11 64-bit)
* Stable internet connection
* Microphone
* Speakers or headphones

## Installation

Retrieve the latest release from the [download link](https://github.com/eddir/Deus/releases/download/0.2.0/Deus.exe) 
and run it. You may want to add the executable to your desktop for easier access.

For the first time, the assistant will ask you to provide your API keys. You can find the API keys in the
[Google Cloud Console](https://console.cloud.google.com/) (json file) or 
[Yandex Cloud Console](https://console.cloud.yandex.com/) (depends on the service you choose). 
You can also find the ChatGPT API key in the [OpenAI Dashboard](https://platform.openai.com/). 

You can select the service you want to use for speech synthesis and recognition and language. If you got into trouble
with speech recognition, you can try to decrease the sensitivity of the speech recognition engine by changing the
`Microphone threshold` value. The lower the value, the more sensitive the speech recognition engine will be.

If you familiar with the command line and prefer to create a standalone executable yourself, you can use the following 
command:

```bash
pyinstaller --noconfirm --onefile --windowed --icon "./logo.ico" --name "Deus" --collect-all "transformers" --collect-all "tqdm" --collect-all "regex" --collect-all "requests" --collect-all "packaging" --collect-all "filelock" --collect-all "numpy" --collect-all "tokenizers" --collect-all "google-cloud-core" --add-data "./deus.gif;." --add-data "./logo.ico;."  "./main.py"
```

The executable will be created in the `dist` directory.

## Usage

Press the `Space` key to start the assistant. It will listen to your voice and try to understand what you said.
If the assistant understood you, it will try to answer your question. 

If you want to reset the conversation, press the `r` key. If you want to open the settings, press the `c` key.
For help, press the `h` key or click right mouse button on the assistant window. 

You can switch appearance of the assistant by pressing the `s` key. 

## License

MIT License
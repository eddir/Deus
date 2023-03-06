# Installation instructions

Use PyInstaller to create a standalone executable. The following command will create a standalone executable for the current platform:

    pyinstaller --noconfirm --onefile --windowed --icon "./logo.ico" --name "Deus" --collect-all "transformers" --collect-all "tqdm" --collect-all "regex" --collect-all "requests" --collect-all "packaging" --collect-all "filelock" --collect-all "numpy" --collect-all "tokenizers" --add-data "./deus.gif;." --add-data "./logo.ico;."  "./main.py"

The executable will be created in the `dist` directory.

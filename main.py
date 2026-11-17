import tkinter as tk
from PIL import Image, ImageTk
import sounddevice as sd
import numpy as np
import sys
import os

def resource_path(relative_path):
    """ Возвращает абсолютный путь к файлу, работает и для обычного запуска, и для .exe """
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Настройки ---
SAMPLE_RATE = 44100
BLOCK_DURATION = 0.1  # сек
BLOCK_SIZE = int(SAMPLE_RATE * BLOCK_DURATION)


# Калибровка: dB = 20*log10(rms) + OFFSET
# Подбери OFFSET так, чтобы тишина была около 0 dB
DB_OFFSET = 90.0


class HamsterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hamster 🐹")
        self.root.geometry("400x450")
        self.root.configure(bg="#2b2b2b")

        # Загружаем картинки
        self.images = {
            "quiet": self._load_img("hamster.png"),
            "medium": self._load_img("hamster1.png"),
            "loud": self._load_img("hamster2.png"),
        }

        # Картинка
        self.label_img = tk.Label(root, bg="#2b2b2b")
        self.label_img.pack(pady=30)

        # Текст с уровнем
        self.label_db = tk.Label(
            root, text="0 dB", font=("Arial", 30, "bold"),
            fg="#ffffff", bg="#2b2b2b"
        )
        self.label_db.pack()

        self.label_status = tk.Label(
            root, text="Тишина 🐹", font=("Arial", 14),
            fg="#aaaaaa", bg="#2b2b2b"
        )
        self.label_status.pack(pady=5)

        self.current_state = None
        self.update_image("quiet")

        # Запуск аудиопотока
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=1,
            callback=self.audio_callback,
        )
        self.stream.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _load_img(self, path):
        try:
            img = Image.open(resource_path(path)).resize((250, 250), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except FileNotFoundError:
            # Заглушка, если файла нет
            img = Image.new("RGB", (250, 250), "#444444")
            return ImageTk.PhotoImage(img)

    def audio_callback(self, indata, frames, time, status):
        # RMS → dB
        rms = np.sqrt(np.mean(indata ** 2))
        if rms < 1e-8:
            db = 0.0
        else:
            db = 30 * np.log10(rms) + DB_OFFSET
        db = max(0.0, db)
        # Обновляем GUI из главного потока
        self.root.after(0, self.update_ui, db)

    def update_ui(self, db):
        self.label_db.config(text=f"{db:.0f} dB")

        if db <= 30:
            state = "quiet"
            text = "Тишина 🐹"
            color = "#8fd18f"
        elif db <= 80:
            state = "medium"
            text = "Разговор 🐹🐹"
            color = "#f0c75e"
        else:
            state = "loud"
            text = "ОЧЕНЬ ГРОМКО! 🐹🐹🐹"
            color = "#ff6b6b"

        self.label_status.config(text=text, fg=color)
        self.update_image(state)

    def update_image(self, state):
        if state != self.current_state:
            self.label_img.config(image=self.images[state])
            self.current_state = state

    def on_close(self):
        self.stream.stop()
        self.stream.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = HamsterApp(root)
    root.mainloop()
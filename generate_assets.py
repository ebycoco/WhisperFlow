import os
from PIL import Image, ImageDraw
import wave
import struct

os.makedirs("assets/sounds", exist_ok=True)

def create_icon(filename, color):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color)
    draw.rounded_rectangle([27, 12, 37, 36], radius=5, fill="white")
    draw.arc([22, 28, 42, 48], start=0, end=180, fill="white", width=2)
    draw.line([32, 48, 32, 56], fill="white", width=2)
    img.save(f"assets/{filename}", format="ICO")

create_icon("icon.ico", "#6C63FF")
create_icon("icon_recording.ico", "#FF4B4B")
create_icon("icon_processing.ico", "#FFA940")

def create_beep(filename, freq):
    sample_rate = 16000
    duration = 0.1
    with wave.open(f"assets/sounds/{filename}", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        import math
        for i in range(int(sample_rate * duration)):
            value = int(32767.0 * math.sin(2.0 * math.pi * freq * i / sample_rate))
            wf.writeframes(struct.pack('<h', value))

create_beep("start.wav", 880)
create_beep("stop.wav", 440)

print("Assets generated successfully.")

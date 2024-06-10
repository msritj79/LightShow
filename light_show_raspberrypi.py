import RPi.GPIO as GPIO
import time
import json

# GPIOの設定
GPIO.setmode(GPIO.BCM)
led_pins = [2, 3, 4, 17, 27, 22, 10, 9, 11, 5]  # 10個のGPIOピン
for pin in led_pins:
    GPIO.setup(pin, GPIO.OUT)

# シーケンスデータの読み込み
def load_sequence(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# シーケンスの再生
def play_sequence(sequence):
    for step in sequence:
        for i, state in enumerate(step["states"]):
            GPIO.output(led_pins[i], state)
        time.sleep(step["duration"] / 1000.0)  # ミリ秒から秒に変換

try:
    sequence = load_sequence('sequence.json')
    play_sequence(sequence)
finally:
    GPIO.cleanup()

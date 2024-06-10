import time
import json

light_list = ["IsBackupOn",         # 0
            "IsBrakeOn",            # 1
            "IsFrontFogOn",         # 2
            "IsHazardOn",           # 3
            "IsHighBeamOn",         # 4
            "IsLeftIndicatorOn",    # 5
            "IsLowBeamOn",          # 6
            "IsParkingOn",          # 7   
            "IsRearFogOn",          # 8
            "IsRightIndicatorOn",   # 9
            "IsRunningOn"]          # 10
light_num_list = range(11)

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


if __name__ == "__main__":
    sequence = load_sequence('sequence.json')
    play_sequence(sequence)

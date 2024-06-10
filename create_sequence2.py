import tkinter as tk
from tkinter import filedialog
import json
from PIL import Image, ImageTk

class LEDSequencerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LED Sequencer")
        self.canvas_width = 1000
        self.canvas_height = 400
        self.led_sequence_width = 800
        self.led_sequence_height = 350
        self.num_leds = 10
        self.time_scale = 10  # 10 seconds
        self.init_gui()
        self.led_sequences = [[] for _ in range(self.num_leds)]

    def init_gui(self):
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()

        #Add rectangle where you edit the LED sequence
        self.draw_frame(self.led_sequence_width, self.led_sequence_height)

        # Add LEDs and time scale labels
        self.draw_grid()

        self.led_on_button = tk.Button(self.root, text="LED ON")
        self.led_on_button.pack(side=tk.LEFT)

        self.simulate_button = tk.Button(self.root, text="Simulate", command=self.simulate)
        self.simulate_button.pack(side=tk.LEFT)

        self.export_button = tk.Button(self.root, text="Export JSON", command=self.export_json)
        self.export_button.pack(side=tk.LEFT)

        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)

        self.current_rect = None
        self.start_x = None
        self.start_y = None

        self.led_on_button.bind("<ButtonPress-1>", self.start_drag)

    def draw_frame(self, width, height):
        self.canvas.create_rectangle(0, 0, width, height, fill="white")

    def draw_grid(self):
        self.row_len = self.led_sequence_height/self.num_leds
        column_len = self.led_sequence_width/self.time_scale
        # Draw horizontal lines and labels for LEDs
        for i in range(self.num_leds):
            self.canvas.create_line(0, i*self.row_len, self.led_sequence_width, i*self.row_len)
            self.canvas.create_text(10, i*self.row_len + self.row_len/2, anchor=tk.NW, text=f"LED {i+1}")

        # Draw vertical lines and labels for time
        for i in range(self.time_scale):
            self.canvas.create_line(i*column_len, 0, i*column_len, self.led_sequence_height)
            self.canvas.create_text(i*column_len, self.led_sequence_height + 10, text=f"{i}s")

    def start_drag(self, event):
        # decide the start position of the rectangle
        # convert to 200ms resolution
        self.start_x = ((event.x * self.time_scale / self.led_sequence_width * 10) // 2) /10 * 2 / self.time_scale * self.led_sequence_width
        # convert to 1/4 position of the row
        self.start_y = (event.y // self.row_len)* self.row_len  + self.row_len/4
        print(self.start_x)

    def drag(self, event):
        # draw the rectangle of drag area
        # convert to 200ms resolution
        self.end_x = ((event.x * self.time_scale / self.led_sequence_width * 10) // 2) /10 * 2 / self.time_scale * self.led_sequence_width
        self.current_rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.start_y + self.row_len/2, fill="blue")

    def end_drag(self, event):
        if self.current_rect:
            led_index = int (self.start_y // self.row_len)
            start_time = self.start_x / self.led_sequence_width * self.time_scale
            end_time = self.end_x / self.led_sequence_width * self.time_scale
            self.led_sequences[led_index].append((start_time, end_time))
            self.current_rect = None
            

    def simulate(self):
        sim_window = tk.Toplevel(self.root)
        sim_window.title("Simulation")
        sim_canvas = tk.Canvas(sim_window, width=self.canvas_width, height=self.canvas_height)
        sim_canvas.pack()

        for i in range(self.num_leds):
            for start, end in self.led_sequences[i]:
                start_x = start / self.time_scale * self.canvas_width
                end_x = end / self.time_scale * self.canvas_width
                sim_canvas.create_rectangle(start_x, i*40 + 10, end_x, i*40 + 30, fill="blue")
        
        for i in range(self.num_leds):
            sim_canvas.create_text(10, i*40 + 10, anchor=tk.NW, text=f"LED {i+1}")
        
        for i in range(self.time_scale + 1):
            x = i * (self.canvas_width / self.time_scale)
            sim_canvas.create_line(x, 0, x, self.canvas_height)
            sim_canvas.create_text(x, self.canvas_height - 10, text=f"{i}s")

    def export_json(self):
        output = self.convert_sequence_to_states()
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w") as f:
                json_str = "[\n"
                for item in output:
                    json_str += json.dumps(item) + ",\n"
                # remove last comma
                json_str = json_str[:-2]
                json_str += "\n]"
                f.write(json_str)
        print("Exported to", file_path)
        print("led_sequences: ", self.led_sequences)
        print("json: ", json_str)

    def convert_sequence_to_states(self):
        # set removes duplicates
        time_points = set()
        for seq in self.led_sequences:
            for start, end in seq:
                time_points.add(start)
                time_points.add(end)

        # sort the time points
        time_points = sorted(time_points)

        led_states = []
        previous_time = 0

        for current_time in time_points:
            states = [0] * len(self.led_sequences)
            for i, seq in enumerate(self.led_sequences):
                for start, end in seq:
                    if start <= previous_time < end:
                        states[i] = 1
            duration = current_time - previous_time
            led_states.append({
                "states": states,
                "duration": duration * 1000  # convert to milliseconds
            })
            previous_time = current_time

        # add the final state
        final_states = [0] * len(self.led_sequences)
        duration = 0
        if time_points:
            duration = (10 - previous_time) * 1000  # add state until end time
        else:
            duration = 10 * 1000  # if no time points, all leds are off

        led_states.append({
            "states": final_states,
            "duration": duration
        })

        return led_states

if __name__ == "__main__":
    root = tk.Tk()
    app = LEDSequencerApp(root)
    root.mainloop()

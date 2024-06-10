import tkinter as tk
from tkinter import filedialog
import json

class LEDSequencerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LED Sequencer")
        self.canvas_width = 1000
        self.canvas_height = 400
        self.num_leds = 10
        self.time_scale = 10  # 10 seconds
        self.init_gui()
        self.led_sequences = [[] for _ in range(self.num_leds)]

    def init_gui(self):
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()

        # Add LEDs and time scale labels
        self.draw_grid()

        self.led_on_button = tk.Button(self.root, text="LED ON")
        self.led_on_button.pack(side=tk.LEFT)
        self.led_on_button.bind("<ButtonPress-1>", self.start_drag_from_button)

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

        self.is_dragging_button = False

    def draw_grid(self):
        # Draw horizontal lines and labels for LEDs
        for i in range(self.num_leds):
            self.canvas.create_line(0, i*40 + 20, self.canvas_width, i*40 + 20)
            self.canvas.create_text(10, i*40 + 10, anchor=tk.NW, text=f"LED {i+1}")

        # Draw vertical lines and labels for time
        for i in range(self.time_scale + 1):
            x = i * (self.canvas_width / self.time_scale)
            self.canvas.create_line(x, 0, x, self.canvas_height)
            self.canvas.create_text(x, self.canvas_height - 10, text=f"{i}s")

    def start_drag_from_button(self, event):
        self.is_dragging_button = True
        self.start_x = event.x_root - self.led_on_button.winfo_rootx()
        self.start_y = event.y_root - self.led_on_button.winfo_rooty()

    def start_drag(self, event):
        if not self.is_dragging_button:
            self.start_x = event.x
            self.start_y = event.y
            self.current_rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, fill="blue")

    def drag(self, event):
        if self.is_dragging_button:
            x = self.canvas.canvasx(event.x_root - self.led_on_button.winfo_rootx() + self.start_x)
            y = self.canvas.canvasy(event.y_root - self.led_on_button.winfo_rooty() + self.start_y)
            self.canvas.delete(self.current_rect)
            self.current_rect = self.canvas.create_rectangle(x, y, x, y + 20, fill="blue")
        elif self.current_rect:
            self.canvas.coords(self.current_rect, self.start_x, self.start_y, event.x, self.start_y + 20)

    def end_drag(self, event):
        if self.is_dragging_button:
            x = self.canvas.canvasx(event.x_root - self.led_on_button.winfo_rootx() + self.start_x)
            y = self.canvas.canvasy(event.y_root - self.led_on_button.winfo_rooty() + self.start_y)
            self.is_dragging_button = False
        else:
            x = event.x
            y = event.y

        if self.current_rect:
            led_index = self.start_y // 40
            start_time = self.start_x / self.canvas_width * self.time_scale
            end_time = x / self.canvas_width * self.time_scale
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
        output = []
        for i in range(self.num_leds):
            for seq in self.led_sequences[i]:
                start, end = seq
                duration = (end - start) * 1000  # Convert to milliseconds
                states = [0] * self.num_leds
                states[i] = 1
                output.append({"states": states, "duration": duration})

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w") as f:
                json_str = "[\n"
                for item in output:
                    json_str += json.dumps(item) + "\n"
                json_str += "]"
                f.write(json_str)
        print("Exported to", file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = LEDSequencerApp(root)
    root.mainloop()

import tkinter as tk
from tkinter import filedialog
import json
from PIL import Image, ImageTk
import cv2

class LightSequencerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Light Sequencer")
        self.canvas_width = 1000
        self.canvas_height = 400
        self.light_sequence_width = 800
        self.light_sequence_height = 350
        self.x_resolution = 200  # 200ms resolution
        self.num_lights = 10
        self.time_scale = 10  # 10 seconds
        self.init_gui()
        self.rectangle_list = []
        self.selected_rect = None
        self.resizing = False
        self.resize_side = None


        self.import_button = tk.Button(self.root, text="Import Movie", command=self.import_movie)
        self.import_button.pack(side=tk.BOTTOM)

    def import_movie(self):
        video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi")])
        if video_path:
            # Code to handle video import and display frames
            # Update self.time_scale based on video duration
            self.time_scale = self.get_video_duration(video_path)
            self.draw_grid()  # Update grid with new time scale

    def get_video_duration(self, video_path):
        # Implement function to get video duration (in seconds)
        # Example implementation using OpenCV
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        cap.release()
        return int(duration)


    def init_gui(self):
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()

        # Add rectangle where you edit the light sequence
        self.draw_frame(self.light_sequence_width, self.light_sequence_height)

        # Add lights and time scale labels
        self.draw_grid()

        self.light_on_button = tk.Button(self.root, text="Light ON")
        self.light_on_button.pack(side=tk.LEFT)

        self.simulate_button = tk.Button(self.root, text="Simulate", command=self.simulate)
        self.simulate_button.pack(side=tk.LEFT)

        self.export_button = tk.Button(self.root, text="Export JSON", command=self.export_json)
        self.export_button.pack(side=tk.LEFT)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_motion)
        self.root.bind("<Delete>", self.delete_selected_rect)

        self.start_x = None
        self.start_y = None

    def draw_frame(self, width, height):
        self.canvas.create_rectangle(0, 0, width, height, fill="white")

    def draw_grid(self):
        self.row_len = self.light_sequence_height / self.num_lights
        column_len = self.light_sequence_width / self.time_scale
        # Draw horizontal lines and labels for lights
        for i in range(self.num_lights):
            self.canvas.create_line(0, i*self.row_len, self.light_sequence_width, i*self.row_len)
            self.canvas.create_text(self.light_sequence_width + 10, i*self.row_len + self.row_len/2, anchor=tk.NW, text=f"light {i}")

        # Draw vertical lines and labels for time
        for i in range(self.time_scale):
            self.canvas.create_line(i*column_len, 0, i*column_len, self.light_sequence_height)
            self.canvas.create_text(i*column_len, self.light_sequence_height + 10, text=f"{i}s")
        
    def on_click(self, event):
        self.start_x = self.convert_x_to_resolution(event.x)
        self.start_y = (event.y // self.row_len) * self.row_len + self.row_len / 4

        # If a rectangle was previously selected, reset its outline color
        if hasattr(self, 'previous_selected_rect') and self.previous_selected_rect:
            self.canvas.itemconfig(self.previous_selected_rect, outline="black")

        self.selected_rect = self.find_selected_rect(event.x, event.y)

        # edit selected rectangle
        if self.selected_rect:
            print("selected")
            
            self.canvas.itemconfig(self.selected_rect, outline="red")
            self.previous_selected_rect = self.selected_rect

            self.resizing = self.is_resizing(event.x, event.y)
            if self.resizing:
                self.resize_side = self.get_resize_side(event.x, event.y)

        # add rectangle
        else:
            self.selected_rect = None
            self.added_rect = None
            self.previous_selected_rect = None
            
    def on_drag(self, event):
        # edit selected rectangle
        if self.selected_rect and self.resizing:
            self.resize_rectangle(event.x, event.y)
        elif self.selected_rect and not self.resizing:
            dx = event.x - self.start_x
            dy = 0
            self.canvas.move(self.selected_rect, dx, dy)
            self.start_x = event.x

            coords = self.canvas.coords(self.selected_rect)
            start_x, start_y, end_x, end_y = coords
            self.start_x = self.convert_x_to_resolution(start_x)
            end_x = self.convert_x_to_resolution(end_x)
            self.canvas.coords(self.selected_rect, self.start_x, start_y, end_x, end_y)
        
        # add rectangle
        else:
            self.end_x = self.convert_x_to_resolution(event.x)
            if not self.added_rect:
                self.added_rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.start_y + self.row_len / 2, fill="blue")
            else:
                self.canvas.coords(self.added_rect, self.start_x, self.start_y, self.end_x, self.start_y + self.row_len / 2)

    def on_release(self, event):
        # edit selected rectangle
        if self.selected_rect and self.resizing:
            self.resizing = False
            self.resize_side = None
        elif self.selected_rect:
            self.selected_rect = None

        # add rectangle
        elif self.added_rect:
            self.rectangle_list.append(self.added_rect)
            self.added_rect = None

    def on_motion(self, event):
        self.selected_rect = self.find_selected_rect(event.x, event.y)
        if self.selected_rect:
            if self.is_resizing(event.x, event.y):
                self.canvas.config(cursor="sb_h_double_arrow")
            else:
                self.canvas.config(cursor="arrow")
        else:
            self.canvas.config(cursor="arrow")

    def convert_x_to_resolution(self, x):
        x = ((x * self.time_scale / self.light_sequence_width * 1000) // self.x_resolution) / 1000 * self.x_resolution / self.time_scale * self.light_sequence_width
        return x
    
    def find_selected_rect(self, x, y):
        overlapping = self.canvas.find_overlapping(x, y, x, y)
        for rect in overlapping:
            if rect in self.rectangle_list:
                return rect
        return None

    def is_resizing(self, x, y):
        rect = self.selected_rect
        if not rect:
            return False
        coords = self.canvas.coords(rect)
        start_x, start_y, end_x, end_y = coords
        if abs(x - start_x) < 10 or abs(x - end_x) < 10:
            return True
        return False

    def get_resize_side(self, x, y):
        rect = self.selected_rect
        coords = self.canvas.coords(rect)
        start_x, start_y, end_x, end_y = coords
        if abs(x - start_x) < 10:
            return 'left'
        elif abs(x - end_x) < 10:
            return 'right'
        return None

    def resize_rectangle(self, x, y):
        rect = self.selected_rect
        coords = self.canvas.coords(rect)
        start_x, start_y, end_x, end_y = coords

        x = self.convert_x_to_resolution(x)

        if self.resize_side == 'left':
            if x < end_x:
                self.canvas.coords(rect, x, start_y, end_x, end_y)
        elif self.resize_side == 'right':
            if x > start_x:
                self.canvas.coords(rect, start_x, start_y, x, end_y)

    def delete_selected_rect(self, event):
        # If a rectangle was previously selected, delete it
        if hasattr(self, 'previous_selected_rect') and self.previous_selected_rect:
            self.canvas.delete(self.previous_selected_rect)
            self.rectangle_list.remove(self.previous_selected_rect)
            self.previous_selected_rect = None


    def simulate(self):
        sim_window = tk.Toplevel(self.root)
        sim_window.title("Simulation")
        sim_canvas = tk.Canvas(sim_window, width=self.canvas_width, height=self.canvas_height)
        sim_canvas.pack()

        for i in range(self.num_lights):
            for start, end in self.light_sequences[i]:
                start_x = start / self.time_scale * self.canvas_width
                end_x = end / self.time_scale * self.canvas_width
                sim_canvas.create_rectangle(start_x, i*40 + 10, end_x, i*40 + 30, fill="blue")
        
        for i in range(self.num_lights):
            sim_canvas.create_text(10, i*40 + 10, anchor=tk.NW, text=f"light {i+1}")
        
        for i in range(self.time_scale + 1):
            x = i * (self.canvas_width / self.time_scale)
            sim_canvas.create_line(x, 0, x, self.canvas_height)
            sim_canvas.create_text(x, self.canvas_height - 10, text=f"{i}s")

    def export_json(self):
        self.update_light_sequences()
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
        print("Light_sequences: ", self.light_sequences)
        print("json: ", json_str)

    def update_light_sequences(self):
        self.light_sequences = [[] for _ in range(self.num_lights)]
        # e.g. light_sequences = [[(0, 200ms), (400ms, 800ms)], [], [(200ms, 400ms)], ...]
        for rect in self.rectangle_list:
            coords = self.canvas.coords(rect)
            start_x, start_y, end_x, end_y = coords
            light_index = int(start_y // self.row_len)
            start_time = start_x / self.light_sequence_width * self.time_scale
            end_time = end_x / self.light_sequence_width * self.time_scale
            self.light_sequences[light_index].append((start_time, end_time))

    def convert_sequence_to_states(self):
        # set() removes duplicates
        time_points = set()
        for seq in self.light_sequences:
            for start, end in seq:
                time_points.add(start)
                time_points.add(end)

        # sort the time points
        time_points = sorted(time_points)

        light_states = []
        previous_time = 0

        for current_time in time_points:
            states = [0] * len(self.light_sequences)
            for i, seq in enumerate(self.light_sequences):
                for start, end in seq:
                    if start <= previous_time < end:
                        states[i] = 1
            duration = current_time - previous_time
            light_states.append({
                "states": states,
                "duration": duration * 1000  # convert to milliseconds
            })
            previous_time = current_time

        # add the final state
        final_states = [0] * len(self.light_sequences)
        duration = 0
        if time_points:
            duration = (10 - previous_time) * 1000  # add state until end time
        else:
            duration = 10 * 1000  # if no time points, all lights are off

        light_states.append({
            "states": final_states,
            "duration": duration
        })

        return light_states

if __name__ == "__main__":
    root = tk.Tk()
    app = LightSequencerApp(root)
    root.mainloop()

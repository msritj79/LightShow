import tkinter as tk
from tkinter import filedialog
import json
import cv2
import time

class LightSequencerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Light Sequencer")
        self.fitToVideoLength = False       # if True, the light sequences canvas width fits to video length
        self.light_sequence_width = 1000
        self.light_sequence_height = 200
        self.max_video_width = 800
        self.max_video_height = 200
        self.x_resolution = 50  # 200ms resolution
        self.num_lights = 10
        self.time_scale = 10  # 10 seconds
        self.rectangle_list = []
        self.selected_rect = None
        self.resizing = False
        self.resize_side = None
        self.video_path = None
        self.cap = None
        self.added_rect = None
        self.video_length = 0
        self.video_speed = 1.0
        self.select_light_num = 0
        self.copy_from_num = 0
        self.copy_to_num = 1
        self.init_gui()
        self.init_gui_video()


    def init_gui(self):
        # self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height)
        # self.canvas.pack()

        # set margin to 50 for grid labels
        self.light_sequence_frame = tk.Frame(self.root, padx=10, pady=10, width=self.light_sequence_width+50, height=self.light_sequence_height+20, bg="white")
        self.light_sequence_frame.pack(side=tk.TOP)

        self.light_sequence_canvas = tk.Canvas(self.light_sequence_frame, width=self.light_sequence_width+50, height=self.light_sequence_height+20, bg="white")
        self.light_sequence_canvas.pack()

        # self.draw_frame(self.light_sequence_width, self.light_sequence_height)
        self.draw_grid()

        self.reset_button = tk.Button(self.light_sequence_frame, text="Reset", command=self.reset_light_sequence)
        self.reset_button.pack(side=tk.LEFT)

        self.simulate_button = tk.Button(self.light_sequence_frame, text="Simulate", command=self.simulate)
        self.simulate_button.pack(side=tk.LEFT)

        self.export_button = tk.Button(self.light_sequence_frame, text="Import JSON", command=self.import_json)
        self.export_button.pack(side=tk.LEFT)

        self.export_button = tk.Button(self.light_sequence_frame, text="Export JSON", command=self.export_json)
        self.export_button.pack(side=tk.LEFT)

        self.light_on_button = tk.Button(self.light_sequence_frame, text="Start")
        self.light_on_button.pack(side=tk.LEFT)

        self.copy_sequence_button = tk.Button(self.light_sequence_frame, text="Copy", command=self.copy_sequence)
        self.copy_sequence_button.pack(side=tk.LEFT)
        self.copy_from_button = tk.Button(self.light_sequence_frame, text=f"from{self.copy_from_num}", command=self.count_copy_from_num)
        self.copy_from_button.pack(side=tk.LEFT)
        self.copy_to_button = tk.Button(self.light_sequence_frame, text=f"to{self.copy_to_num}", command=self.count_copy_to_num)
        self.copy_to_button.pack(side=tk.LEFT)

        self.light_sequence_canvas.bind("<Button-1>", self.on_click)
        self.light_sequence_canvas.bind("<B1-Motion>", self.on_drag)
        self.light_sequence_canvas.bind("<ButtonRelease-1>", self.on_release)
        self.light_sequence_canvas.bind("<Motion>", self.on_motion)
        self.root.bind("<Delete>", self.delete_selected_rect)

        self.start_x = None
        self.start_y = None

    def init_gui_video(self):
        self.video_frame = tk.Frame(self.root, width=self.max_video_width, height=self.max_video_height, bg="white")
        # self.video_frame.pack_propagate(0)  # Don't let the frame control its own size
        self.video_frame.pack(side=tk.TOP)

        self.video_canvas = tk.Canvas(self.video_frame, width=self.max_video_width, height=self.max_video_height, bg="white")
        self.video_canvas.pack()

        self.import_button = tk.Button(self.video_frame, text="Import video", command=self.import_video)
        self.import_button.pack(side=tk.LEFT)

        self.play_button = tk.Button(self.video_frame, text="Play", command=self.play_video)
        self.play_button.pack(side=tk.LEFT)

        self.pause_button = tk.Button(self.video_frame, text="Pause", command=self.pause_video)
        self.pause_button.pack(side=tk.LEFT)

        self.video_speed_button = tk.Button(self.video_frame, text=f"x{self.video_speed}", command=self.change_video_speed)
        self.video_speed_button.pack(side=tk.LEFT)

        self.accept_button_press = True
        self.add_sequence_button = tk.Button(self.video_frame, text="Add sequences", command=self.on_add_button_press)
        self.add_sequence_button.bind("<ButtonPress>", self.on_add_button_press)
        self.add_sequence_button.bind("<ButtonRelease>", self.on_add_button_release)
        self.add_sequence_button.pack(side=tk.LEFT)

        self.select_light_button = tk.Button(self.video_frame, text=f"Light{self.select_light_num}", command=self.select_light)
        self.select_light_button.pack(side=tk.LEFT)

        self.video_scale = tk.Scale(self.video_frame, from_=0, to=self.video_length, orient=tk.HORIZONTAL, command=self.video_scale_changed)
        self.video_scale.pack(fill=tk.X)

    def select_light(self):
        self.select_light_num += 1
        if self.select_light_num >= self.num_lights:
            self.select_light_num = 0
        self.select_light_button.config(text=f"Light{self.select_light_num}")

    def on_add_button_press(self, event=None):
        if self.accept_button_press==True:
            self.is_button_pressed = True
            self.accept_button_press = False
            
            if not self.added_rect:
                self.start_x = self.convert_x_to_resolution(self.video_bar_x)
                y = self.light_sequence_height / self.num_lights * self.select_light_num
                self.start_y = (y // self.row_len) * self.row_len + self.row_len / 4
                self.added_rect = self.light_sequence_canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y + self.row_len / 2, fill="blue")
                self.continue_add_button_press()

    def continue_add_button_press(self):
        if self.is_button_pressed:
            self.end_x = self.convert_x_to_resolution(self.video_bar_x)
            self.light_sequence_canvas.coords(self.added_rect, self.start_x, self.start_y, self.end_x, self.start_y + self.row_len / 2)
            delay = 100
            self.root.after(delay, self.continue_add_button_press)

    def on_add_button_release(self, event=None):
        self.is_button_pressed = False
        if self.added_rect:
            self.rectangle_list.append(self.added_rect)
            self.added_rect = None

        # it detects ButtonPress event just after ButtonRelease event.
        # So, delay was set not to detect ButtonPress event.
        delay  = 50
        self.root.after(delay, self.accept_after_delay)

    def accept_after_delay(self):
        self.accept_button_press = True

        
    def import_video(self):
        self.video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi")])
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            # self.video_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            # self.video_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.video_length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) / int(self.cap.get(cv2.CAP_PROP_FPS))
            self.video_scale.config(to=self.video_length)
            self.play_video()  # Start playing video
            self.update_time_scale()
            self.video_bar = self.light_sequence_canvas.create_line(0, 0, 0, self.light_sequence_height, fill="red", width=1, activefill="blue")

    def update_time_scale(self):
        self.light_sequence_canvas.delete("all")
        self.time_scale = int(self.video_length)
        if self.fitToVideoLength:    
            self.light_sequence_width = self.time_scale * 100
            self.light_sequence_canvas.config(width=self.light_sequence_width+50)
        self.draw_grid()

    def play_video(self):
        if self.cap and not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.video_path)

        if self.cap.isOpened():
            self.root.after(30, self.update_video_frame)

    def update_video_frame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                original_height, original_width = frame.shape[:2]
                width = int(original_width * self.max_video_height / original_height)
                frame = cv2.resize(frame, (width, self.max_video_height))
                photo = tk.PhotoImage(data=cv2.imencode('.png', frame)[1].tobytes())
                self.video_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                self.video_canvas.image = photo  # Keep reference in tkinter
                self.video_bar_update()
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                delay = int(1000 / fps) # delay in milliseconds
                # delay should be 16ms, but other part make delay for 13ms.
                # so, if you want to play video x times later, you should set delay to 16*x-13
                delay = max(1, int(16 / self.video_speed - 13))
                self.root.after(delay, self.update_video_frame)
            else:
                self.cap.release()

    def video_bar_update(self):
        if self.cap and self.cap.isOpened():
            current_time = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            if current_time <= self.video_length:
                self.video_bar_x = (current_time / self.video_length) * self.light_sequence_width
                self.light_sequence_canvas.coords(self.video_bar, self.video_bar_x, 0, self.video_bar_x, self.light_sequence_height)

    def pause_video(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()

    def change_video_speed(self):
        if self.video_speed == 0.1:
            self.video_speed = 0.2
        elif self.video_speed == 0.2:
            self.video_speed = 0.5
        elif self.video_speed == 0.5:
            self.video_speed = 1.0
        elif self.video_speed == 1.0:
            self.video_speed = 2.0
        elif self.video_speed == 2.0:
            self.video_speed = 0.1
        self.video_speed_button.config(text=f"{self.video_speed}")
        self.pause_video()
        time.sleep(0.1)
        self.play_video()

    def video_scale_changed(self, value):
        if self.cap and self.cap.isOpened():
            value = float(value)
            self.cap.set(cv2.CAP_PROP_POS_MSEC, value * 1000)
            self.video_bar_update()



    def draw_frame(self, width, height):
        self.light_sequence_canvas.create_rectangle(0, 0, width, height, fill="white")

    def draw_grid(self):
        self.row_len = self.light_sequence_height / self.num_lights
        column_len = self.light_sequence_width / self.time_scale
        # Draw horizontal lines and labels for lights
        for i in range(self.num_lights):
            self.light_sequence_canvas.create_line(0, i*self.row_len, self.light_sequence_width, i*self.row_len)
            self.light_sequence_canvas.create_text(self.light_sequence_width + 10, i*self.row_len + self.row_len/4, anchor=tk.NW, text=f"Light {i}")

        # Draw vertical lines and labels for time
        for i in range(self.time_scale):
            self.light_sequence_canvas.create_line(i*column_len, 0, i*column_len, self.light_sequence_height)
            self.light_sequence_canvas.create_text(i*column_len, self.light_sequence_height + 10, text=f"{i}s")
        
    def on_click(self, event):
        self.start_x = self.convert_x_to_resolution(event.x)
        self.start_y = (event.y // self.row_len) * self.row_len + self.row_len / 4

        # If a rectangle was previously selected, reset its outline color
        if hasattr(self, 'previous_selected_rect') and self.previous_selected_rect:
            self.light_sequence_canvas.itemconfig(self.previous_selected_rect, outline="black")

        self.selected_rect = self.find_selected_rect(event.x, event.y)

        # edit selected rectangle
        if self.selected_rect:
            self.light_sequence_canvas.itemconfig(self.selected_rect, outline="red")
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
            self.light_sequence_canvas.move(self.selected_rect, dx, dy)
            self.start_x = event.x

            coords = self.light_sequence_canvas.coords(self.selected_rect)
            start_x, start_y, end_x, end_y = coords
            self.start_x = self.convert_x_to_resolution(start_x)
            end_x = self.convert_x_to_resolution(end_x)
            self.light_sequence_canvas.coords(self.selected_rect, self.start_x, start_y, end_x, end_y)
        
        # add rectangle
        else:
            self.end_x = self.convert_x_to_resolution(event.x)
            if not self.added_rect:
                self.added_rect = self.light_sequence_canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.start_y + self.row_len / 2, fill="blue")
            else:
                self.light_sequence_canvas.coords(self.added_rect, self.start_x, self.start_y, self.end_x, self.start_y + self.row_len / 2)

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
        # print("x,y:", event.x, event.y)
        if self.selected_rect:
            if self.is_resizing(event.x, event.y):
                self.light_sequence_canvas.config(cursor="sb_h_double_arrow")
            else:
                self.light_sequence_canvas.config(cursor="arrow")
        else:
            self.light_sequence_canvas.config(cursor="arrow")

    def convert_x_to_resolution(self, x):
        x = ((x * self.time_scale / self.light_sequence_width * 1000) // self.x_resolution) / 1000 * self.x_resolution / self.time_scale * self.light_sequence_width
        return x
    
    def find_selected_rect(self, x, y):
        overlapping = self.light_sequence_canvas.find_overlapping(x, y, x, y)
        for rect in overlapping:
            if rect in self.rectangle_list:
                return rect
        return None

    def is_resizing(self, x, y):
        rect = self.selected_rect
        if not rect:
            return False
        coords = self.light_sequence_canvas.coords(rect)
        start_x, start_y, end_x, end_y = coords
        if abs(x - start_x) < 10 or abs(x - end_x) < 10:
            return True
        return False

    def get_resize_side(self, x, y):
        rect = self.selected_rect
        coords = self.light_sequence_canvas.coords(rect)
        start_x, start_y, end_x, end_y = coords
        if abs(x - start_x) < 10:
            return 'left'
        elif abs(x - end_x) < 10:
            return 'right'
        return None

    def resize_rectangle(self, x, y):
        rect = self.selected_rect
        coords = self.light_sequence_canvas.coords(rect)
        start_x, start_y, end_x, end_y = coords

        x = self.convert_x_to_resolution(x)

        if self.resize_side == 'left':
            if x < end_x:
                self.light_sequence_canvas.coords(rect, x, start_y, end_x, end_y)
        elif self.resize_side == 'right':
            if x > start_x:
                self.light_sequence_canvas.coords(rect, start_x, start_y, x, end_y)

    def delete_selected_rect(self, event):
        # If a rectangle was previously selected, delete it
        if hasattr(self, 'previous_selected_rect') and self.previous_selected_rect:
            self.light_sequence_canvas.delete(self.previous_selected_rect)
            self.rectangle_list.remove(self.previous_selected_rect)
            self.previous_selected_rect = None
    
    def reset_light_sequence(self):
        self.light_sequence_canvas.delete("all")
        self.draw_grid()
        self.rectangle_list = []
        self.video_bar = self.light_sequence_canvas.create_line(0, 0, 0, self.light_sequence_height, fill="red", width=1, activefill="blue")
        # self.pause_video()
        # self.play_video()


    def simulate(self):
        sim_window = tk.Toplevel(self.root)
        sim_window.title("Simulation")
        sim_canvas = tk.Canvas(sim_window, width=self.light_sequence_canvas_width, height=self.light_sequence_canvas_height)
        sim_canvas.pack()

        for i in range(self.num_lights):
            for start, end in self.light_sequences[i]:
                start_x = start / self.time_scale * self.light_sequence_canvas_width
                end_x = end / self.time_scale * self.light_sequence_canvas_width
                sim_canvas.create_rectangle(start_x, i*40 + 10, end_x, i*40 + 30, fill="blue")
        
        for i in range(self.num_lights):
            sim_canvas.create_text(10, i*40 + 10, anchor=tk.NW, text=f"light {i+1}")
        
        for i in range(self.time_scale + 1):
            x = i * (self.canvas_width / self.time_scale)
            sim_canvas.create_line(x, 0, x, self.canvas_height)
            sim_canvas.create_text(x, self.canvas_height - 10, text=f"{i}s")

    def import_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.reset_light_sequence()
            with open(file_path, "r") as f:
                light_states = json.load(f)
                light_sequences = self.convert_states_to_sequence(light_states)
                self.convert_sequence_to_rectangle_list(light_sequences)
        print("Imported from", file_path)

    def export_json(self):
        self.update_light_sequences()
        light_states = self.convert_sequence_to_states()
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w") as f:
                json_str = "[\n"
                for item in light_states:
                    json_str += json.dumps(item) + ",\n"
                # remove last comma
                json_str = json_str[:-2]
                json_str += "\n]"
                f.write(json_str)
        print("Exported to", file_path)

    def update_light_sequences(self):
        self.light_sequences = [[] for _ in range(self.num_lights)]
        # e.g. light_sequences = [[(0, 200ms), (400ms, 800ms)], [], [(200ms, 400ms)], ...]
        # e.g. light_sequences = [[(1.0, 2.95), (4.0, 8.0)], [(0.0, 1.0)], [(1.95, 4.0), (5.0, 6.0), (7.0, 8.0)], [], [], [], [], [], [], []]
        for rect in self.rectangle_list:
            coords = self.light_sequence_canvas.coords(rect)
            start_x, start_y, end_x, end_y = coords
            light_index = int(start_y // self.row_len)
            start_time = start_x / self.light_sequence_width * self.time_scale
            end_time = end_x / self.light_sequence_width * self.time_scale
            self.light_sequences[light_index].append((start_time, end_time))

    def convert_sequence_to_rectangle_list(self, sequences):
        self.rectangle_list = []
        for i, seq in enumerate(sequences):
            for start, end in seq:
                start_x = start / self.time_scale * self.light_sequence_width
                end_x = end / self.time_scale * self.light_sequence_width
                y = i * self.row_len + self.row_len / 4
                self.rectangle_list.append(self.light_sequence_canvas.create_rectangle(start_x, y, end_x, y + self.row_len / 2, fill="blue"))

    def convert_states_to_sequence(self, states):
        num_lights = len(states[0]['states'])  # Number of lights
        sequences = [[] for _ in range(num_lights)]

        current_times = [0.0] * num_lights  # Initialize current time for each light

        for state in states:
            duration = state['duration'] / 1000.0  # Convert duration to seconds
            for i in range(num_lights):
                if state['states'][i] == 1:
                    if not sequences[i] or sequences[i][-1][1] != current_times[i]:
                        sequences[i].append((current_times[i], current_times[i] + duration))
                    else:
                        start_time, end_time = sequences[i].pop()
                        sequences[i].append((start_time, end_time + duration))
                current_times[i] += duration
        sequences = [[(round(start, 4), round(end, 4)) for start, end in seq] for seq in sequences]
        return sequences
    
    def convert_sequence_to_states(self):
        # e.g. states = [{'states': [0, 1, 0, 0, 0, 0, 0, 0, 0, 0], 'duration': 0.0}, {'states': [0, 1, 0, 0, 0, 0, 0, 0, 0, 0], 'duration': 1000.0}, {'states': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'duration': 950.0}, {'states': [1, 0, 1, 0, 0, 0, 0, 0, 0, 0], 'duration': 1000.0}, {'states': [0, 0, 1, 0, 0, 0, 0, 0, 0, 0], 'duration': 1050.0}, {'states': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'duration': 1000.0}, {'states': [1, 0, 1, 0, 0, 0, 0, 0, 0, 0], 'duration': 1000.0}, {'states': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'duration': 1000.0}, {'states': [1, 0, 1, 0, 0, 0, 0, 0, 0, 0], 'duration': 1000.0}, {'states': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'duration': 2000.0}] 
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
                "duration": int(duration * 1000)  # convert to milliseconds
            })
            previous_time = current_time

        # add the final state
        final_states = [0] * len(self.light_sequences)
        duration = 0
        if time_points:
            duration = (self.time_scale - previous_time) * 1000  # add state until end time
        else:
            duration = self.time_scale * 1000  # if no time points, all lights are off

        light_states.append({
            "states": final_states,
            "duration": int(duration)
        })

        return light_states
    
    def copy_sequence(self):
        from_num = self.copy_from_num
        to_num = self.copy_to_num
        from_y = from_num * self.row_len + self.row_len / 4
        to_y = to_num * self.row_len + self.row_len / 4

        for rect in self.rectangle_list:
            coords = self.light_sequence_canvas.coords(rect)
            start_x, start_y, end_x, end_y = coords
            if start_y == from_y:
                new_rect = self.light_sequence_canvas.create_rectangle(start_x, to_y, end_x, to_y + self.row_len / 2, fill="blue")
                self.rectangle_list.append(new_rect)


    def count_copy_from_num(self):
        self.copy_from_num += 1
        if self.copy_from_num >= self.num_lights:
            self.copy_from_num = 0
        if self.copy_from_num == self.copy_to_num:
            self.count_copy_to_num()
        self.copy_from_button.config(text=f"from{self.copy_from_num}")

    def count_copy_to_num(self):
        self.copy_to_num += 1
        if self.copy_to_num >= self.num_lights:
            self.copy_to_num = 0
        if self.copy_to_num == self.copy_from_num:
            self.count_copy_from_num()
        self.copy_to_button.config(text=f"to{self.copy_to_num}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LightSequencerApp(root)
    root.mainloop()

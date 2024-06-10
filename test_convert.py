led_sequences = [
    [], 
    [(2.0, 3.0), (4.0, 7.0)], 
    [(2.0, 5.0)], 
    [(5.0, 6.0)], 
    [], 
    [(5.0, 10.0)], 
    [], 
    [(6.0, 9.0)], 
    [], 
    []
]

# set removes duplicates
time_points = set()
for seq in led_sequences:
    for start, end in seq:
        time_points.add(start)
        time_points.add(end)

# sort the time points
time_points = sorted(time_points)

led_states = []
previous_time = 0

for current_time in time_points:
    states = [0] * len(led_sequences)
    for i, seq in enumerate(led_sequences):
        for start, end in seq:
            if start <= previous_time < end:
                states[i] = 1
    duration = current_time - previous_time
    led_states.append({
        "states": states,
        "duration": duration * 1000  # cpnvert to milliseconds
    })
    previous_time = current_time

# add the final state
final_states = [0] * len(led_sequences)
duration = 0
if time_points:
    duration = (10 - previous_time) * 1000  # add state until end time
else:
    duration = 10 * 1000  # if no time points, all leds are off

led_states.append({
    "states": final_states,
    "duration": duration
})

print(led_states)
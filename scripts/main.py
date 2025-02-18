# Libraries importing
from pynput import *
from os import _exit
import ctypes
import asyncio
import json
import time
from pprint import pprint


# List for saving events data
actions = []

# Recording/replaying/saving blocking booleans
is_recording = False
is_replaying = False
is_saving = False

# Pressed left Alt boolean
alt_is_pressed = False

# Value to control replay task
replay_task = None
# Times to replay event list
replay_times = 20

# Timer value
start_time = 0
# Holding shortcut handling value
shortcut_flag = True

# Duration of holding shortcut in sec
shorcut_delay = 2

# Standard filename for saved replays
default_filename = "replay.json"

# Main event loop
loop = None


# Returns current screen scale factor in float
def get_scaling_factor():
    # Using Windows API to get scale in percent and bringing it to float
    return ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100


# Returns coordinates scaled by screen scale factor
def unscaled_pos(x, y):
    sf = get_scaling_factor()
    # Returning tuple with scaled coordinates
    return (x / sf, y / sf)


# Releasing left Alt (must be fixed)
def alt_release():
    actions.append(('key_release', keyboard.Key.alt_l, time.time()))


# Saves actions arg to JSON file
def save_replay(actions, filename=default_filename):
    # JSON list
    serializable_actions = []

    # Serializing data for uploading to JSON
    for action in actions:
        # Splitting action data
        event_type, data, timestamp = action

        # Converting data tuples to JSON-friendly lists
        if isinstance(data, tuple):
            data = list(data)
            # Converting pynput mouse datatype to strings
            for i, item in enumerate(data):
                if isinstance(item, (mouse.Button)):
                    data[i] = str(item)
        
        # Converting out of tuple keyboard datatypes to strings
        elif isinstance(data, (keyboard.Key, keyboard.KeyCode)):
            data = str(data)

        # Appending serialized action
        serializable_actions.append([event_type, data, timestamp])

    # Writing to file
    with open(filename, 'w') as file:
        json.dump(serializable_actions, file, indent=4)

    print(f"\nReplay saved to '{filename}'!")


# Returns saved actions from JSON file
def load_replay(filename=default_filename):
    # List for replay-friendly loaded data
    deserialized_actions = []

    try:
        # Loading actions from save
        with open(filename, 'r') as file:
            loaded_actions = json.load(file)

    except FileNotFoundError:
        # Handling NotFound error
        print(f"Replay called '{filename}' not found! Alt+Y to create new")
        return []

    else:
        # Deserializing file data
        for action in loaded_actions:
            # Splitting action data
            event_type, data, timestamp = action

            # Deserializing mouse press/release actions
            if isinstance(data, list):
                for i, item in enumerate(data):
                    # Reading mouse button string and converting it to pynput datatype
                    if isinstance(item, str) and item.startswith("Button"):
                        button_name = item.split(".")[1]
                        data[i] = getattr(mouse.Button, button_name)

                # Converting data from list to tuple
                data = tuple(data)
            
            # Deserializing keyboard actions
            elif isinstance(data, str):
                # Special keys case (Key.alt_l, Key.shift etc.)
                if data.startswith("Key."):
                    key_name = data.split(".")[1]
                    data = getattr(keyboard.Key, key_name)
                # Numeral KeyCodes case (<62>, <76> etc., only on Windows)
                elif data.startswith("<"):
                    keycode_num = int(data.strip("<>"))
                    data = keyboard.KeyCode.from_vk(keycode_num)
                # String KeyCodes case ('\x03', '\x0b' etc., only on Windows)
                else:
                    # Converting string into Unicode symbol and stripping it
                    keycode_name = data.encode('utf-8').decode('unicode_escape')
                    keycode_name = keycode_name.strip("''")
                    # Converting symbol into KeyCode
                    data = keyboard.KeyCode.from_char(keycode_name)

            # Adding deserialized data to list
            deserialized_actions.append(tuple([event_type, data, timestamp]))

    print(f"Loading from '{filename}' complete! Alt+U to replay")
    # Returning summary
    return deserialized_actions



# Key pressing event handler
def key_on_press(key):
    global is_recording, is_replaying, is_saving, alt_is_pressed, replay_task, start_time, shortcut_flag, actions

    # Shortcuts can be used while left Alt pressed
    if key == keyboard.Key.alt_l:
        alt_is_pressed = True


    # Alt+C (finish program, on Windows listener blocks main thread, must be fixed)
    if alt_is_pressed and hasattr(key, 'char') and key.char == 'c':
        print("")
        _exit(0)

    # Alt+Y (recording start/finish)
    elif alt_is_pressed and hasattr(key, 'char') and key.char == 'y':
        # Blocking other processes
        if is_replaying:
            print("Cannot replay while other processes active!")
            return
        # Dont print message while saving
        elif is_saving: return
        # Enabling recording and clearing old record
        is_recording = not is_recording
        if is_recording:
            actions.clear()
            print("Recording started...")
        else:
            # Releasing left Alt (must be fixed)
            alt_release()
            print("Recording finished. Alt+U to replay")

    # Alt+U (replay start/stop)
    elif alt_is_pressed and hasattr(key, 'char') and key.char == 'u':
        # Blocking other processes
        if is_recording:
            print("Cannot replay while other processes active!")
            return
        # Dont print message while saving
        elif is_saving: return
        # Immediately stops replaying
        if replay_task is not None and not replay_task.done():
            replay_task.cancel()
            is_replaying = False
            print("Replaying stopped")
        else:
            # Threadsafe task to not block keyboard listener
            replay_task = asyncio.run_coroutine_threadsafe(replay_actions(times=replay_times), loop)

    # Alt+I (input, save replay to file)
    elif alt_is_pressed and hasattr(key, 'char') and key.char == 'i':
        # Blocking other processes
        if is_recording or is_replaying:
            print("Cannot save while other processes active!")
            return
        if shortcut_flag:
            # Timer value
            current_time = time.time()

            # Setting start time value (only once)
            if not is_saving:
                start_time = time.time()
                is_saving = True

            # Holding shortcut message
            if (current_time - start_time) <= shorcut_delay:
                print("\rHold... (%.2f)" % (current_time - start_time), end="")
            
            # Saving result after delay and resetting values
            else:
                save_replay(actions=actions)
                start_time = int(time.time())
                shortcut_flag = False
                is_saving = False


    # Alt+O (output, load replay from file)
    elif alt_is_pressed and hasattr(key, 'char') and key.char == 'o':
        # Blocking other processes
        if is_recording or is_replaying:
            print("Cannot load while other processes active!")
            return
        # Dont print message while saving
        elif is_saving: return
        actions = load_replay()

    # Append pressed key if it isnt reserved shortcut
    elif is_recording:
        actions.append(('key_press', key, time.time()))

    # print(f"{key} was pressed")


# Key releasing action handler
def key_on_release(key):
    global alt_is_pressed, is_saving, shortcut_flag

    # Resetting Alt value
    if key == keyboard.Key.alt_l:
        alt_is_pressed = False
    
    # Resetting save shortcut value
    if hasattr(key, 'char') and key.char == 'i':
        # Moving to the next line if released in process
        if shortcut_flag and is_saving: print()
        shortcut_flag = True
        is_saving = False

    # Appending key to event list while recording
    if is_recording:
        actions.append(('key_release', key, time.time()))

    # print(f"{key} was released")


# Mouse move action handler
def mouse_on_move(x, y):
    # Appending move to event list while recording
    if is_recording:
        actions.append(('mouse_move', (x, y), time.time()))
        # pass

    # print(f"Mouse moved to position ({x}, {y})")


# Mouse click action handler
def mouse_on_click(x, y, button, pressed):
    # Appending click to event list while recording
    if is_recording:
        if pressed:
            actions.append(('mouse_press', (x, y, button), time.time()))
        else:
            actions.append(('mouse_release', (x, y, button), time.time()))

    # print(f"Mouse button {button} pressed? - {pressed}")


# Mouse scroll action handler
def mouse_on_scroll(x, y, dx, dy):
    # Appending scroll to event list while recording
    if is_recording:
        actions.append(('mouse_scroll', (x, y, dx, dy), time.time()))

    # if dy > 0: print(f"Mouse scrolled up")
    # elif dy < 0: print(f"Mouse scrolled down")


# Replays recorded actions
async def replay_actions(times=1):
    global is_replaying

    # Wrong start replay data handlers
    if not actions:
        print("Nothing was recorded!")
        return

    # Activating replaying state
    is_replaying = True

    # Previous action time container
    previous_time = None

    print("Replaying...")

    # Iterating replaying cycles
    for i in range(times):

        # Counting iterations
        if times > 1:
            print(f"Current iteration: {i}")

        # Iterating actions
        for action in actions:
            # Splitting action data
            event_type, data, timestamp = action

            # Delay between actions
            if previous_time is not None:
                delay = timestamp - previous_time
                await asyncio.sleep(delay)

            # Updating previous time container
            previous_time = timestamp


            # Actions (events) handlers
            if event_type == 'key_press': # Keyboard key pressing
                key = data
                keyboard.Controller().press(key)
            elif event_type == 'key_release': # Keyboard key releasing
                key = data
                keyboard.Controller().release(key)
            elif event_type == 'mouse_move': # Mouse moving (optional)
                x, y = data
                mouse.Controller().position = unscaled_pos(x, y)
            elif event_type == 'mouse_press': # Mouse buttons pressing
                x, y, button = data
                mouse.Controller().position = unscaled_pos(x, y)
                mouse.Controller().press(button)
            elif event_type == 'mouse_release': # Mouse buttons releasing
                x, y, button = data
                mouse.Controller().position = unscaled_pos(x, y)
                mouse.Controller().release(button)
            elif event_type == 'mouse_scroll': # Mouse scrolling
                x, y, dx, dy = data
                mouse.Controller().position = unscaled_pos(x, y)
                mouse.Controller().scroll(dx, dy)
            else:
                print("Unknown event type")
                break

    # Replaying state resseting
    is_replaying = False
    print("Replay finished succesfully")


# Main cycle
async def main():
    global loop

    # Introduction
    print("\n--- RememberBot ---")
    print(" > Alt+Y to start/finish recording\n > Alt+U to start/stop replaying")
    print(" > Alt+I to save replay\n > Alt+O to load replay")
    print(" > Alt+C to exit")

    # Mouse listener function
    def mouse_listener():
        with mouse.Listener(on_click=mouse_on_click, on_move=mouse_on_move, on_scroll=mouse_on_scroll) as mouse_listener:
            mouse_listener.join()

    # Keyboard listener function
    def keyboard_listener():
        with keyboard.Listener(on_press=key_on_press, on_release=key_on_release) as keyboard_listener:
            keyboard_listener.join()

    # Getting event loop for listeners
    loop = asyncio.get_event_loop()

    # Starting listeners in different threads
    loop.run_in_executor(None, mouse_listener)
    loop.run_in_executor(None, keyboard_listener)

    # Infinite cycle to not close program
    while True:
        await asyncio.sleep(1)


# Script starts if executing current file
if __name__ == "__main__":
    asyncio.run(main())

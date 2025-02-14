# Libraries importing
from pynput import *
from os import _exit
from ctypes import windll
import asyncio
import ctypes
import time


# List for saving events data
actions = []

# Recording/replaying booleans
is_recording = False
is_replaying = False

# Pressed left Alt boolean
alt_is_pressed = False

# Value to control replay task
replay_task = None
# Times to replay event list
replay_times = 1

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



# Key pressing event handler
def key_on_press(key):
    global is_recording, is_replaying, alt_is_pressed, replay_task

    # Shortcuts can be used while left Alt pressed
    if key == keyboard.Key.alt_l:
        alt_is_pressed = True


    # Alt+C (finish program, on Windows listener blocks main thread, must be fixed)
    if alt_is_pressed and hasattr(key, 'char') and key.char == 'c':
        print("")
        _exit(0)

    # Alt+Y (recording start/finish)
    elif alt_is_pressed and hasattr(key, 'char') and key.char == 'y':
        # Inactive while replaying
        if is_replaying:
            print("Cannot record while replaying!")
        else:
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
        # Immediately stops replaying
        if replay_task is not None and not replay_task.done():
            replay_task.cancel()
            is_replaying = False
            print("Replaying stopped")
        else:
            # Threadsafe task to not block keyboard listener
            replay_task = asyncio.run_coroutine_threadsafe(replay_actions(times=replay_times), loop)

    # Append pressed key if it isnt reserved shortcut
    elif is_recording:
        actions.append(('key_press', key, time.time()))
        # print('APPENDED')

    # print(f"{key} was pressed")


# Key releasing action handler
def key_on_release(key):
    global alt_is_pressed

    # Shortcuts cant be used while left Alt unpressed
    if key == keyboard.Key.alt_l:
        alt_is_pressed = False

    # Appending key to event list while recording
    if is_recording:
        actions.append(('key_release', key, time.time()))
        # print('APPENDED')

    # print(f"{key} was released")


# Mouse move action handler
def mouse_on_move(x, y):
    # Appending move to event list while recording
    if is_recording:
        actions.append(('mouse_move', (x, y), time.time()))
        # pass
        # print('APPENDED')

    # print(f"Mouse moved to position ({x}, {y})")


# Mouse click action handler
def mouse_on_click(x, y, button, pressed):
    # Appending click to event list while recording
    if is_recording:
        if pressed:
            actions.append(('mouse_press', (x, y, button), time.time()))
        else:
            actions.append(('mouse_release', (x, y, button), time.time()))
        # print('APPENDED')

    # print(f"Mouse button {button} pressed? - {pressed}")


# Mouse scroll action handler
def mouse_on_scroll(x, y, dx, dy):
    # Appending scroll to event list while recording
    if is_recording:
        actions.append(('mouse_scroll', (x, y, dx, dy), time.time()))
        # print('APPENDED')

    # if dy > 0: print(f"Mouse scrolled up")
    # elif dy < 0: print(f"Mouse scrolled down")


# Replays recorded actions
async def replay_actions(times=1):
    global is_replaying

    # Wrong start replay data handlers
    if is_recording:
        print("Cannot replay while recording!")
        return
    elif not actions:
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
            # Simplified action data
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
            elif event_type == 'mouse_move': # Mouse moving
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

            # print("REPLAYED")

    # Replaying state resseting
    is_replaying = False

    print("Replay finished succesfully")


# Main cycle
async def main():
    global loop

    # Introduction
    print("\n--- RememberBot ---")
    print("Alt+Y to start/finish recording \nAlt+U to start/stop replaying \nAlt+C to exit")

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

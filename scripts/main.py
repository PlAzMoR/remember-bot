from pynput import *
import time


# List for saving events data
actions = []

# Recording boolean
is_recording = False

# Control key pressing boolean
is_ctrl_pressed = False


# Key pressing event handler
def key_on_press(key):
    global is_recording, is_ctrl_pressed

    print(f"{key} was pressed")

    # Dont appending ctrl key to not cause recording restart
    if is_recording and key != keyboard.Key.ctrl:
        actions.append(('key_press', str(key), time.time()))
        print('APPENDED')

    if key == keyboard.Key.ctrl:
        is_ctrl_pressed = True
    elif is_ctrl_pressed and hasattr(key, 'char') and key.char == 'y':
        is_recording = not is_recording
        
        if is_recording:
            print("Recording started")
        else:
            print("Recording finished")

    # print(f"Rec - {is_recording}, ctrl - {is_ctrl_pressed}")


# Key releasing event handler
def key_on_release(key):
    global is_ctrl_pressed

    print(f"{key} was released")

    # Dont appending ctrl key to not cause recording restart
    if is_recording and key != keyboard.Key.ctrl:
        actions.append(('key_release', str(key), time.time()))
        print('APPENDED')

    if key == keyboard.Key.ctrl:
        is_ctrl_pressed = False

    # print(f"Rec - {is_recording}, ctrl - {is_ctrl_pressed}")


# Mouse moving event handler
def mouse_on_move(x, y):
    print(f"Mouse moved to position ({x}, {y})")

    if is_recording:
        actions.append(('mouse_move', (x, y), time.time()))
        print('APPENDED')


# Mouse click event handler
def mouse_on_click(x, y, button, pressed):
    if pressed:
        print(f"Mouse button {button} pressed")
        if is_recording:
            actions.append(('mouse_click', (x, y, str(button)), time.time()))
            print('APPENDED')
    else:
        print(f"Mouse button {button} released")
        if is_recording:
            actions.append(('mouse_release', (x, y, str(button)), time.time()))
            print('APPENDED')


# Mouse scroll event handler
def mouse_on_scroll(x, y, dx, dy):
    if dy > 0:
        print(f"Mouse scrolled up")
    elif dy < 0:
        print(f"Mouse scrolled down")

    if is_recording:
        actions.append(('mouse_scroll', (x, y, dx, dy), time.time()))
        print('APPENDED')


# Keyboard/Mouse listener (always enabled)
def start_listening():
    with mouse.Listener(on_move=mouse_on_move, on_click=mouse_on_click, on_scroll=mouse_on_scroll) as listener_mouse:
        with keyboard.Listener(on_press=key_on_press, on_release=key_on_release) as listener_keyboard:
            listener_keyboard.join()
            listener_mouse.join()


# Recorded actions replayer
def replay_actions():
    pass


# Script starts if executing current file
if __name__ == "__main__":
    start_listening()
    # time.sleep(5)

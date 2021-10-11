from pynput import mouse

def map_button(b):
    if b == mouse.Button.left:
        return 'Mouse_L'
    elif b == mouse.Button.right:
        return 'Mouse_R'
    else:
        return b

def start(callback):
    buttons = dict()
    def on_move(x, y):
        print('Pointer moved to {0}'.format(
            (x, y)))
        callback({'buttons': buttons, 'key': 'mouse', 'move': (x,y)})

    def on_click(x, y, button, pressed):
        print('click', x, y, button, pressed)
        b = map_button(button)
        if pressed:
            buttons[b] = 1
        elif b in buttons:
            buttons.pop(b)
        callback({'buttons': buttons, 'key': 'mouse', 'click': (x,y, button, pressed)})

    def on_scroll(x, y, dx, dy):
        print('Scrolled {0} at {1}'.format(
            'down' if dy < 0 else 'up',
            (x, y)))
        callback({'buttons': buttons, 'key': 'mouse', 'scroll': (x,y, dx, dy)})

    listener = mouse.Listener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll)
    listener.start()
    return listener


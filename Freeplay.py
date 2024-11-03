import Notes
def Freeplay(sheduler,newSongBtnClicked,freeplayBtnClicked):
    from pynput import keyboard
    notes = Notes.Notes().notes

    def on_press(key):
        try:
            if key.char in notes:

                sheduler.playNote(notes[key.char]-30, 1, 112)
                print(notes[key.char]-30)

            if key.char == '♥':
                listener.stop()

                return False
        except AttributeError:
            pass

    def on_release(key):

        if 'char' not in dir(key):
            return False
        if key.char in notes:
            sheduler.stopNote(notes[key.char]-30, 1)

        if key == keyboard.Key.esc:
            # Stop listener
            listener.stop()
            return False

    # # Collect events until released
    # with keyboard.Listener(
    #         on_press=on_press,
    #         on_release=on_release) as listener:
    #     listener.join()

    # ...or, in a non-blocking fashion:
    listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release)
    listener.start()
    
    if newSongBtnClicked.is_set():
        listener.stop()
        freeplayBtnClicked.clear()


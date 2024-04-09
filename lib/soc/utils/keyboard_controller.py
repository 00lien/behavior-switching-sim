from pynput import keyboard

class KeyBoradController:

    def __init__(self, enabled=True):
        self.keydown = False
        self.key_dict ={}
        if(enabled):
            self.key_listener = keyboard.Listener(on_press=self.on_press,
                                              on_release=self.on_release)
            self.key_listener.start()

    def add_listener(self, key, callback):
        self.key_dict[key] = callback

    def on_press(self, keyname):
        if self.keydown:
            return
        keyname = str(keyname).strip()
        #print('Key Pressed {}'.format(keyname))
        try:
            self.keydown = True
            cb = self.key_dict.get(keyname)
            if cb is not None:
                cb(keyname)
        except AttributeError:
            print('special key {0} pressed'.format(keyname))

    def on_release(self, keyname):
        self.keydown = False
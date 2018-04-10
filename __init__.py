from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from threading import Thread
import time


class EnclosureControlSkill(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.thread = None
        self.playing = False
        self.animations = []

    @property
    def up_down_animation(self):
        return [
                self.animate(2, 6, self.enclosure.eyes_look, "d"),
                self.animate(4, 6, self.enclosure.eyes_look, "u"),

                ]

    @property
    def left_right_animation(self):
        return [
            self.animate(2, 6, self.enclosure.eyes_look, "l"),
            self.animate(4, 6, self.enclosure.eyes_look, "r"),

        ]

    @staticmethod
    def animate(t, often, func, *args):
        '''
        Args:
            t (int) : seconds from now to begin the frame (secs)
            often (int/string): (int) how often to repeat the frame (secs)
                                (str) when to trigger, relative to the clock,
                                      for synchronized repetitions
            func: the function to invoke
            *args: arguments to pass to func
        '''
        return {
            "time": time.time() + t,
            "often": often,
            "func": func,
            "args": args
        }

    @staticmethod
    def _get_time(often, t):
        return often - t % often

    def run(self):
        """
        animation thread while performing speedtest

        """

        while self.playing:
            for animation in self.animations:
                if animation["time"] <= time.time():
                    # Execute animation action
                    animation["func"](*animation["args"])

                    # Adjust time for next loop
                    if type(animation["often"]) is int:
                        animation["time"] = time.time() + animation["often"]
                    else:
                        often = int(animation["often"])
                        t = animation["time"]
                        animation["time"] = time.time() + self._get_time(
                            often, t)
            time.sleep(0.1)

        self.thread = None
        self.enclosure.activate_mouth_events()
        self.enclosure.mouth_reset()
        self.enclosure.eyes_reset()

    def play_animation(self, animation=None):
        animation = animation or self.up_down_animation
        if not self.thread:
            self.playing = True

            # Display info on a screen
            self.enclosure.deactivate_mouth_events()
            self.enclosure.mouth_think()

            # Build the list of animation actions to run
            self.animations = animation
            self.thread = Thread(None, self.run)
            self.thread.daemon = True
            self.thread.start()

    @intent_handler(IntentBuilder("SystemReboot")
                    .require("perform").require("system").require("reboot"))
    def handle_system_reboot(self, message):
        self.emitter.emit(message.reply("system.reboot"))

    @intent_handler(IntentBuilder("SystemUnmute")
                    .require("system").require("unmute"))
    def handle_system_unmute(self, message):
        self.enclosure.system_unmute()

    @intent_handler(IntentBuilder("SystemMute")
                    .require("system").require("mute"))
    def handle_system_mute(self, message):
        self.enclosure.system_mute()

    @intent_handler(IntentBuilder("EnclosureLookRight")
                    .require("look").require("right")
                    .optionally("enclosure"))
    def handle_look_right(self, message):
        self.enclosure.eyes_look("r")

    @intent_handler(IntentBuilder("EnclosureLookLeft")
                    .require("look").require("left").optionally("enclosure"))
    def handle_look_left(self, message):
        self.enclosure.eyes_look("l")

    @intent_handler(IntentBuilder("EnclosureLookUp")
                    .require("look").require("up").optionally("enclosure"))
    def handle_look_up(self, message):
        self.enclosure.eyes_look("u")

    @intent_handler(IntentBuilder("EnclosureLookDown")
                    .require("look").require("down").optionally("enclosure"))
    def handle_look_down(self, message):
        self.enclosure.eyes_look("d")

    @intent_handler(IntentBuilder("EnclosureLookUpDown")
                    .require("look").require("up")
                    .require("down").optionally("enclosure")
                    .optionally("animation"))
    def handle_look_up_down(self, message):
        self.play_animation(self.up_down_animation)

    @intent_handler(IntentBuilder("EnclosureLookLeftRight")
                    .require("look").require("right")
                    .require("left").optionally("enclosure")
                    .optionally("animation"))
    def handle_look_left_right(self, message):
        self.play_animation(self.left_right_animation)

    @intent_handler(IntentBuilder("EnclosureEyesBlink")
                    .require("blink").at_least_one(["eyes", "animation"])
                    .optionally("enclosure").optionally("right")
                    .optionally("left"))
    def handle_blink_eyes(self, message):
        for i in range(0, 3):
            if "right" in message.data:
                self.enclosure.eyes_blink("r")
            if "left" in message.data:
                self.enclosure.eyes_blink("l")
            else:
                self.enclosure.eyes_blink()

    @intent_handler(IntentBuilder("EnclosureEyesSpin")
                    .require("spin").at_least_one(["eyes", "animation"])
                    .optionally("enclosure"))
    def handle_spin_eyes(self, message):
        self.enclosure.eyes_spin()

    @intent_handler(IntentBuilder("EnclosureEyesNarrow")
                    .require("narrow").require("eyes")
                    .optionally("enclosure"))
    def handle_narrow_eyes(self, message):
        self.enclosure.eyes_narrow()

    @intent_handler(IntentBuilder("EnclosureReset")
                    .require("reset").require("enclosure"))
    def handle_enclosure_reset(self, message):
        self.enclosure.eyes_reset()
        self.enclosure.mouth_reset()

    @intent_handler(IntentBuilder("EnclosureMouthSmile")
                    .require("smile").at_least_one(["animation", "mouth"])
                    .optionally("enclosure"))
    def handle_enclosure_smile(self, message):
        self.enclosure.mouth_smile()

    @intent_handler(IntentBuilder("EnclosureMouthListen")
                    .require("listen").at_least_one(["animation", "mouth"])
                    .optionally("enclosure"))
    def handle_enclosure_listen(self, message):
        self.enclosure.mouth_listen()

    @intent_handler(IntentBuilder("EnclosureMouthThink")
                    .require("think").at_least_one(["animation", "mouth"])
                    .optionally("enclosure"))
    def handle_enclosure_think(self, message):
        self.enclosure.mouth_think()

    def stop(self):
        if self.playing and self.thread is not None:
            self.playing = False
            self.thread.join(1)


def create_skill():
    return EnclosureControlSkill()


from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from threading import Thread
import time
import random


class EnclosureControlSkill(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.thread = None
        self.playing = False
        self.animations = []

    @property
    def crazy_eyes_animation(self):
        choices = [(self.enclosure.eyes_look, "d"),
                   (self.enclosure.eyes_look, "u"),
                   (self.enclosure.eyes_look, "l"),
                   (self.enclosure.eyes_look, "r"),
                   (self.enclosure.eyes_color, (255, 0, 0)),
                   (self.enclosure.eyes_color, (255, 0, 255)),
                   (self.enclosure.eyes_color, (255, 255, 255)),
                   (self.enclosure.eyes_color, (0, 0, 255)),
                   (self.enclosure.eyes_color, (0, 255, 0)),
                   (self.enclosure.eyes_color, (255, 255, 0)),
                   (self.enclosure.eyes_color, (0, 255, 255)),
                   (self.enclosure.eyes_spin, None),
                   (self.enclosure.eyes_narrow, None),
                   (self.enclosure.eyes_on, None),
                   (self.enclosure.eyes_off, None),
                   (self.enclosure.eyes_blink, None)]

        anim = []
        for i in range(0, 10):
            frame = random.choice(choices)
            anim.append(self.animate(i, 3, frame[0], frame[1]))
        return anim

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

            # Build the list of animation actions to run
            self.animations = animation
            self.thread = Thread(None, self.run)
            self.thread.daemon = True
            self.thread.start()

    @intent_handler(IntentBuilder("SystemReboot")
                    .require("perform").require("system").require("reboot"))
    def handle_system_reboot(self, message):
        self.speak("rebooting")
        self.emitter.emit(message.reply("system.reboot", {}))

    @intent_handler(IntentBuilder("SystemUnmute")
                    .require("system").require("unmute"))
    def handle_system_unmute(self, message):
        self.enclosure.system_unmute()
        self.speak("now that i have a voice, i shall not be silent")

    @intent_handler(IntentBuilder("SystemMute")
                    .require("system").require("mute"))
    def handle_system_mute(self, message):
        self.speak("am i that annoying?")
        self.enclosure.system_mute()

    @intent_handler(IntentBuilder("EnclosureLookRight")
                    .require("look").require("right")
                    .optionally("enclosure"))
    def handle_look_right(self, message):
        self.speak("looking right")
        self.enclosure.eyes_look("r")

    @intent_handler(IntentBuilder("EnclosureLookLeft")
                    .require("look").require("left").optionally("enclosure"))
    def handle_look_left(self, message):
        self.speak("looking left")
        self.enclosure.eyes_look("l")

    @intent_handler(IntentBuilder("EnclosureLookUp")
                    .require("look").require("up").optionally("enclosure"))
    def handle_look_up(self, message):
        self.speak("looking up")
        self.enclosure.eyes_look("u")

    @intent_handler(IntentBuilder("EnclosureLookDown")
                    .require("look").require("down").optionally("enclosure"))
    def handle_look_down(self, message):
        self.speak("looking down")
        self.enclosure.eyes_look("d")

    @intent_handler(IntentBuilder("EnclosureLookUpDown")
                    .require("look").require("up")
                    .require("down").optionally("enclosure")
                    .optionally("animation"))
    def handle_look_up_down(self, message):
        self.speak("up and down, up and down")
        self.play_animation(self.up_down_animation)

    @intent_handler(IntentBuilder("EnclosureLookLeftRight")
                    .require("look").require("right")
                    .require("left").optionally("enclosure")
                    .optionally("animation"))
    def handle_look_left_right(self, message):
        self.speak("left and right, left and right")
        self.play_animation(self.left_right_animation)

    @intent_handler(IntentBuilder("EnclosureEyesBlink")
                    .require("blink").one_of("eyes", "animation")
                    .optionally("enclosure").optionally("right")
                    .optionally("left"))
    def handle_blink_eyes(self, message):
        for i in range(0, 10):
            if "right" in message.data:
                self.enclosure.eyes_blink("r")
            if "left" in message.data:
                self.enclosure.eyes_blink("l")
            else:
                self.enclosure.eyes_blink()
        self.speak("so this is what it feels like having low F P S")

    @intent_handler(IntentBuilder("EnclosureEyesSpin")
                    .require("spin").one_of("eyes", "animation")
                    .optionally("enclosure"))
    def handle_spin_eyes(self, message):
        self.speak("around the world, here i go")
        self.enclosure.eyes_spin()

    @intent_handler(IntentBuilder("EnclosureEyesNarrow")
                    .require("narrow").require("eyes")
                    .optionally("enclosure"))
    def handle_narrow_eyes(self, message):
        self.speak("this is my evil face")
        self.enclosure.eyes_narrow()
        self.enclosure.eyes_color(255, 0, 0)

    @intent_handler(IntentBuilder("EnclosureReset")
                    .require("reset").require("enclosure"))
    def handle_enclosure_reset(self, message):
        self.enclosure.eyes_reset()
        self.enclosure.mouth_reset()
        self.speak("this was fun")

    @intent_handler(IntentBuilder("EnclosureMouthSmile")
                    .require("smile").one_of("animation", "mouth")
                    .optionally("enclosure"))
    def handle_enclosure_smile(self, message):
        self.enclosure.mouth_smile()
        self.speak("i don't know how to smile")

    @intent_handler(IntentBuilder("EnclosureMouthListen")
                    .require("listen").one_of("animation", "mouth")
                    .optionally("enclosure"))
    def handle_enclosure_listen(self, message):
        self.speak("when i do this i feel like I'm dancing")
        self.enclosure.mouth_listen()

    @intent_handler(IntentBuilder("EnclosureMouthThink")
                    .require("think").one_of("animation", "mouth")
                    .optionally("enclosure"))
    def handle_enclosure_think(self, message):
        self.speak("i love thinking")
        self.enclosure.mouth_think()

    @intent_handler(IntentBuilder("EnclosureCrazyEyes")
                    .require("eyes").optionally("animation").require("crazy")
                    .optionally("enclosure"))
    def handle_enclosure_crazy_eyes(self, message):
        self.speak("artificial intelligence performing artificial "
                   "stupidity, you don't see this every day")
        self.play_animation(self.crazy_eyes_animation)

    def stop(self):
        if self.playing and self.thread is not None:
            self.playing = False
            self.thread.join(1)
            self.enclosure.activate_mouth_events()
            self.enclosure.eyes_reset()


def create_skill():
    return EnclosureControlSkill()


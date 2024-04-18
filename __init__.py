import random
import time
from ast import literal_eval as parse_tuple
from difflib import SequenceMatcher
from ovos_utils import create_daemon
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder
from ovos_workshop.skills import OVOSSkill
from threading import Thread


def _hex_to_rgb(_hex):
    """ Convert hex color code to RGB tuple
    Args:
        hex (str): Hex color string, e.g '#ff12ff' or 'ff12ff'
    Returns:
        (rgb): tuple i.e (123, 200, 155) or None
    """
    try:
        if '#' in _hex:
            _hex = _hex.replace('#', "").strip()
        if len(_hex) != 6:
            return None
        (r, g, b) = int(_hex[0:2], 16), int(_hex[2:4], 16), int(_hex[4:6], 16)
        return (r, g, b)
    except Exception:
        return None


def fuzzy_match_color(color_a, color_dict):
    """ fuzzy match for colors

        Args:
            color_a (str): color as string
            color_dict (dict): dict with colors
        Returns:
            color: color from color_dict
    """
    highest_ratio = float("-inf")
    _color = None
    for color, value in color_dict.items():
        s = SequenceMatcher(None, color_a, color)
        if s.ratio() > highest_ratio:
            highest_ratio = s.ratio()
            _color = color
    if highest_ratio > 0.8:
        return _color
    else:
        return None


class EnclosureControlSkill(OVOSSkill):
    def initialize(self):
        self.thread = None
        self.playing = False
        self.animations = []
        self.brightness_dict = self.translate_namedvalues('brightness.levels')
        self.color_dict = self.translate_namedvalues('colors')
        self.add_event('mycroft.eyes.default', self.handle_default_eyes)
        self.add_event('mycroft.ready', self.handle_default_eyes)

        # TODO: Add OVOSSkill.register_entity_list() and use the
        #  self.color_dict.keys() instead of duplicating data
        self.register_entity_file('color.entity')

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
            self.thread = create_daemon(self.run)

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
                self.enclosure.eyes_blink("b")
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

    #####################################################################
    # Color interactions
    def set_eye_color(self, color=None, rgb=None, speak=True):
        """ Change the eye color on the faceplate, update saved setting
        """
        if color is not None:
            color_rgb = self._parse_to_rgb(color)
            if color_rgb is not None:
                (r, g, b) = color_rgb
        elif rgb is not None:
            (r, g, b) = rgb
        else:
            return  # no color provided!

        try:
            self.enclosure.eyes_color(r, g, b)
            if speak:
                self.speak_dialog('set.color.success')
            # Update saved color
            self.settings['current_eye_color'] = [r, g, b]
        except Exception:
            self.log.debug('Bad color code: ' + str(color))
            if speak:
                self.speak_dialog('error.set.color')

    @intent_handler('custom.eye.color.intent')
    def handle_custom_eye_color(self, message):
        # Conversational interaction to set a custom eye color

        def is_byte(utt):
            try:
                return 0 <= int(utt) <= 255
            except Exception:
                return False

        self.speak_dialog('set.custom.color')
        wait_while_speaking()
        r = self.get_response('get.r.value', validator=is_byte,
                              on_fail="error.rgbvalue", num_retries=2)
        if not r:
            return  # cancelled

        g = self.get_response('get.g.value', validator=is_byte,
                              on_fail="error.rgbvalue", num_retries=2)
        if not g:
            return  # cancelled

        b = self.get_response('get.b.value', validator=is_byte,
                              on_fail="error.rgbvalue", num_retries=2)
        if not b:
            return  # cancelled

        custom_rgb = [r, g, b]
        self.set_eye_color(rgb=custom_rgb)

    @intent_handler('eye.color.intent')
    def handle_eye_color(self, message):
        """ Callback to set eye color from list

            Args:
                message (dict): messagebus message from intent parser
        """
        color_str = (message.data.get('color', None) or
                     self.get_response('color.need'))
        if color_str:
            match = fuzzy_match_color(normalize(color_str), self.color_dict)
            if match is not None:
                self.set_eye_color(color=match)
            else:
                self.speak_dialog('color.not.exist')

    def _parse_to_rgb(self, color):
        """ Convert color descriptor to RGB

        Parse a color name ('dark blue'), hex ('#000088') or rgb tuple
        '(0,0,128)' to an RGB tuple.

        Args:
            color (str): RGB, Hex, or color from color_dict
        Returns:
            (r, g, b) (tuple): Tuple of rgb values (0-255) or None
        """
        if not color:
            return None

        # check if named color in dict
        try:
            if color.lower() in self.color_dict:
                return _hex_to_rgb(self.color_dict[color.lower()])
        except Exception:
            pass

        # check if rgb tuple like '(0,0,128)'
        try:
            (r, g, b) = parse_tuple(color)
            if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                return (r, g, b)
            else:
                return None
        except Exception:
            pass

        # Finally check if color is hex, like '#0000cc' or '0000cc'
        return _hex_to_rgb(color)

    def handle_default_eyes(self, message):
        if self.settings.get('current_eye_color'):
            self.set_eye_color(self.settings['current_eye_color'], speak=False)

    #####################################################################
    # Brightness intent interaction

    def percent_to_level(self, percent):
        """ converts the brigtness value from percentage to
             a value arduino can read

            Args:
                percent (int): interger value from 0 to 100

            return:
                (int): value form 0 to 30
        """
        return int(float(percent) / float(100) * 30)

    def parse_brightness(self, brightness):
        """ parse text for brightness percentage

            Args:
                brightness (str): string containing brightness level

            return:
                (int): brightness as percentage (0-100)
        """

        try:
            # Handle "full", etc.
            name = normalize(brightness)
            if name in self.brightness_dict:
                return self.brightness_dict[name]

            if '%' in brightness:
                brightness = brightness.replace("%", "").strip()
                return int(brightness)
            if 'percent' in brightness:
                brightness = brightness.replace("percent", "").strip()
                return int(brightness)

            i = int(brightness)
            if i < 0 or i > 100:
                return None

            if i < 30:
                # Assume plain 0-30 is "level"
                return int((i * 100.0) / 30.0)

            # Assume plain 31-100 is "percentage"
            return i
        except Exception:
            return None  # failed in an int() conversion

    def set_eye_brightness(self, level, speak=True):
        """ Actually change hardware eye brightness

            Args:
                level (int): 0-30, brightness level
                speak (bool): when True, speak a confirmation
        """
        self.enclosure.eyes_brightness(level)
        if speak is True:
            percent = int(float(level) * float(100) / float(30))
            self.speak_dialog(
                'brightness.set', data={'val': str(percent) + '%'})

    def _set_brightness(self, brightness):
        # brightness can be a number or word like "full", "half"
        percent = self.parse_brightness(brightness)
        if percent is None:
            self.speak_dialog('brightness.not.found.final')
        elif int(percent) is -1:
            self.handle_auto_brightness(None)
        else:
            self.auto_brightness = False
            self.set_eye_brightness(self.percent_to_level(percent))

    @intent_handler('brightness.intent')
    def handle_brightness(self, message):
        """ Intent Callback to set custom eye colors in rgb

            Args:
                message (dict): messagebus message from intent parser
        """
        brightness = (message.data.get('brightness', None) or
                      self.get_response('brightness.not.found'))
        if brightness:
            self._set_brightness(brightness)

    def stop(self):
        if self.playing and self.thread is not None:
            self.playing = False
            self.enclosure.activate_mouth_events()
            self.enclosure.eyes_reset()
            return True
        return False

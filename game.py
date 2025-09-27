import logging
import queue
import threading
import time
import typing
import random
from dataclasses import dataclass
from colorama import Fore

import library
from matrix_button_led_controller import MatrixButtonLEDController

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
USE_LED_HAT = True

@dataclass
class ButtonInfo:
    color: str
    sound: str
    matched: bool
    index: int

class Game:
    def __init__(self, button_pad: MatrixButtonLEDController):
        self.button_pad = button_pad
        self.button_pad.assign_button_events(self.when_pressed, self.when_held, self.when_released)
        self.buttons: typing.List[ButtonInfo] = []
        self.sounds: typing.List[str] = []
        self.colors: typing.List[str] = []
        self.speaker = library.speaker.Speaker()
        self.initialize_button_pad()
        self.started = False
        self.play_game = True
        self.queue = queue.Queue()
        self.clickedButtonIndex = -1
        self.attempts = 100

    @property
    def correct_sound(self):
        """The sound that is played when player gets a pair"""
        self.speaker.play_preloaded_wav("correct_answer", wait_until_done=True)
        return "correct_answer"

    @property
    def incorrect_sound(self):
        """The sound that is played when player makes an incorrect guess"""
        self.speaker.play_preloaded_wav("incorrect", wait_until_done=True)
        return "incorrect"

    @property
    def end_of_game_sound(self):
        """The sound that is played when the game ends."""
        return "end_of_game"

    def _background_logic_checker(self):
        while self.play_game:

            time.sleep(0.005)  # Prevents busy-waiting
            if self.queue.empty():
                continue
            button_number = self.queue.get()
            print(f"Handling button {button_number}")

            # Example logic: light up the button that was pressed with a constant color
            button = self.button_pad.get_button(button_number)
            #self.button_pad.set_button_led_color(button, "red")
            # TODO: check your game state, and update things

    def when_pressed(self, button):
        print(type(button))
        # TODO: this is called when a button is pressed. Add what you need to here
        _logger.info(f"Button {button.pin.info.number} pressed")
        self.queue.put(button.pin.info.number)
        index = int(str(button.pin)[3:]) -1
        print(index)
        #set self.color to button.color
        self.button_pad.set_button_led_color(button, self.buttons[index].color)
        print(self.buttons[index].color);
        self.speaker.play_preloaded_wav(self.buttons[index].sound, wait_until_done=True)  # Play a sound when button is pressed
        self.attempts -= 1
        
        #set self.sound to button.sound
        if(self.clickedButtonIndex == -1):
            self.clickedButtonIndex = index;
        else:
            #if the colors are the same
            if(self.buttons[self.clickedButtonIndex].color == self.buttons[index].color):
                #if the sounds are the same
                self.correct_sound
                self.buttons[index].matched = True
                self.buttons[self.clickedButtonIndex].matched = True



            #if the colo   
            else:
                self.incorrect_sound
                time.sleep(1)
                self.button_pad.set_button_led_color(button, "black")
                self.button_pad.set_button_led_color(self.button_pad.get_button(self.clickedButtonIndex + 1), "black")
            self.clickedButtonIndex = -1

        

    def when_held(self, button):
        pin = str(button.pin)


        if(pin == "BTN1"):
            self.button_pad.clear_button_pad()
            self.initialize_button_pad()
            self.clickedButtonIndex = -1
        elif(pin == "BTN2"):
            for i in range(len(self.buttons)):
                self.button_pad.set_button_led_color(self.button_pad.get_button(i), self.buttons[i].color)
            time.sleep(1)
            self.button_pad.clear_button_pad()
            self.initialize_button_pad()
            self.clickedButtonIndex = -1
        # TODO: this is called when a button is held. Add what you need to here
        pass
    def memory_mode(self):

        memory_mode_user = input(Fore.RED +"Would you like memory mode \nYes or No?")
        print(memory_mode_user)
        if (memory_mode_user.lower() == 'yes'):
            print('hello')
            for i in range(len(self.buttons)):
                print('yo')
                self.button_pad.set_button_led_color(self.button_pad.get_button(i), self.buttons[i].color)
            time.sleep(2)
            self.button_pad.clear_button_pad()
            self.initialize_button_pad()
            self.clickedButtonIndex = -1

        elif (memory_mode_user == 'no'):
            pass
        else:
            pass
        
    def difficulty_level(self):
        difficulty_level_user = input(Fore.RED +"What difficulty level will you choose? \n 1 2 3 or 4?")
        if(difficulty_level_user == '2'):
            self.attempts = 45
        elif(difficulty_level_user == '3'):
            self.attempts = 36
        elif(difficulty_level_user == '4'):
            self.attempts = 22
        else:
            print("That is not a difficulty level")
        

    def when_released(self, button):
        # TODO: this is called when a button is released. Add what you need to here
        pass

    def initialize_button_pad(self):
        self.button_pad.clear_button_pad()
        self.colors = ["magenta", "aqua", "red", "gold", "green", "purple", "white", "blue"]
        random_color = random.choice(self.colors)
        self.sounds = [
            "thunder2",
            "fart_z",
            "baby_x",
            "slide_whistle_x",
            "arrow2",
            "phone_pay",
            "bloop_x",
            "car_horn_x",
        ]

        colors_pairs = self.colors * 2

        sounds_pairs = self.sounds * 2

        sound_and_color_list = []
        for i in range(16):
            sound_and_color_list.append([colors_pairs[i], sounds_pairs[i]])

        random.shuffle(sound_and_color_list)
        for i in range(16):
            button = self.buttons.append(ButtonInfo(sound_and_color_list[i][0], sound_and_color_list[i][1], False, i))
            #print(self.buttons[i])
        print(self.buttons)
    def _start_game(self):
        self.thread = threading.Thread(target=self._background_logic_checker)
        self.thread.start()
        self.speaker.play_preloaded_wav("slide_whistle_x", wait_until_done=True)
        self.started = True

    def play(self):
        self.memory_mode()
        self.difficulty_level()
        self._start_game()
        try:
            input("Press Enter to exit the game...")
        except KeyboardInterrupt:
            print("Exiting game...")
        finally:
            self.play_game = False
            self.thread.join()
            self.button_pad.cleanup()


def _main():
    button_pad = MatrixButtonLEDController(
        scan_delay=0.020, pwm_freq=10000, display_pause=0.001, use_led_hat=USE_LED_HAT
    )
    game = Game(button_pad)
    game.play()


if __name__ == "__main__":
    _main()

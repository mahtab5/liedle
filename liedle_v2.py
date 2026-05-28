import tkinter as tk
import random
import os
from enum import Enum
from collections import Counter


# Constants
WORD_LENGTH = 5
MAX_GUESSES = 6
WORDLIST = "wordlist.txt"

# for how many ms the splashscreen will stay
SPLASH_SCREEN_TIME = 1500

# colors
GREEN = "#6aaa64"
YELLOW = "#c9b458"
GREY = "#787c7e"

WHITE = "#ffffff"
DARK = "#1a1a1b"
LIGHT_GREY = "#3a3a3c"

KEYBOARD_ROWS = ["QWERTYUIOP", "ASDFGHJKL", "↵ZXCVBNM⌫"]


# states to easily determine where the game is
class GameState(Enum):
    PLAYING = 1
    AI_SOLVING = 2
    GAME_OVER = 3
    GAME_WON = 4
    AI_COMPLETE = 5
    AI_LOST = 6

# helper to load the words
def load_words():
    if not os.path.exists(WORDLIST):
        print(f"Missing file: {WORDLIST}")
        exit(1)

    with open(WORDLIST, "r") as file:
        return [w.strip().upper() for w in file.readlines()]

# helper to get feedback in ['', '', '', '', ''], with color codes
def get_feedback(guess, target):
    feedback = [GREY] * WORD_LENGTH
    pool = list(target)

    for i in range(WORD_LENGTH):
        if guess[i] == target[i]:
            feedback[i] = GREEN
            pool[i] = None

    for i in range(WORD_LENGTH):
        if feedback[i] == GREEN:
            continue

        if guess[i] in pool:
            feedback[i] = YELLOW
            pool[pool.index(guess[i])] = None

    return feedback


# choose the best candidate for the next word
def solver_next(candidates):
    # get the frequency as a dictionary for all letters in the candidates set
    freq = Counter(c for w in candidates for c in set(w))
    
    # return the max candidate, and the max is calculated using custom key
    return max(candidates, key=lambda w: sum(freq[c] for c in set(w)))


# use process of elimination to eliminate impossible words
def solver_filter(candidates, guess, feedback):
    # this is the brain for my solver
    # it basically treats the 'word' as a target, and sees
    # if we would get the same feedback if it was the target
    def consistent(word):
        return get_feedback(guess, word) == feedback
    
    # check the consistent for all words in the possible candidates, only choose if it qualifies
    return [w for w in candidates if consistent(w)]

# I have separated each screens in my architecture of the app for better state management
# I have also separated each part (title, grid, button, message, keyboard) in separate method
# It gave me clear and managed code
# I have also used a dark theme, and tried to keep it consistent
class Liedle:
    def __init__(self, root):
        self.root = root
        self.root.title("Liedle")
        self.root.geometry("700x950")
        self.root.configure(bg=DARK)
        self.root.resizable(False, False)
        self.words = load_words()
        self.root.bind("<Key>", self._handle_keypress)
        self._show_splash_screen()
        
    # clear all the widgets for a fresh screen
    def _clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
            
    # the first screen
    def _show_splash_screen(self):
        self._clear_screen()
        frame = tk.Frame(self.root, bg=DARK)
        frame.pack(fill="both", expand=True)
        title = tk.Label(
            frame, text="LIEDLE", font=("Helvetica", 44, "bold"), bg=DARK, fg=WHITE
        )
        title.pack(expand=True)

        subtitle = tk.Label(
            frame,
            text="© 2026 Mahtab Hossain\nA Wordle Game That Lies",
            font=("Arial", 12),
            bg=DARK,
            fg=WHITE,
        )
        subtitle.pack(pady=30)

        self.root.after(SPLASH_SCREEN_TIME, self._new_game)

    # The last screen, shows depending on the outcome
    def _show_end_screen(self):
        self._clear_screen()
        frame = tk.Frame(self.root, bg=DARK)
        frame.pack(fill="both", expand=True)

        title_text = ""
        
        # Dynamic title, changed based on the outcome
        if self._state == GameState.GAME_WON:
            title_text = "YOU WON!"
        elif self._state == GameState.GAME_OVER:
            title_text = "GAME OVER"
        elif self._state == GameState.AI_COMPLETE:
            title_text = "AI SOLVER COMPLETE"
        elif self._state == GameState.AI_LOST:
            title_text = "RARE! AI has LOST!"
        

        title = tk.Label(
            frame, text=title_text, font=("Helvetica", 34, "bold"), bg=DARK, fg=WHITE
        )
        title.pack(pady=60)

        word_label = tk.Label(
            frame,
            text=f"The word was {self._target}",
            font=("Arial", 18),
            bg=DARK,
            fg=YELLOW,
        )
        word_label.pack(pady=(20, 10))

        _, real_feedback, fake_feedback = self._guess_history[self._lie_guess]

        lied_block = -1

        # find the block which was a lie
        for i in range(WORD_LENGTH):
            if real_feedback[i] != fake_feedback[i]:
                lied_block = i + 1
                break

        lie_label = tk.Label(
            frame,
            text=(
                f"The lie occurred in "
                f"Guess {self._lie_guess + 1}, "
                f"Block {lied_block}"
            ),
            font=("Arial", 15, "bold"),
            bg=DARK,
            fg=YELLOW,
        )
        lie_label.pack(pady=(0, 25))
        
        # I made a dark button method, tried to keep the UI consistent
        self._dark_button(frame, "NEW GAME", self._new_game)
        self._dark_button(frame, "EXIT", self.root.destroy)

    def _new_game(self, keep_target=False):
        self._state = GameState.PLAYING
        
        # it is essential for the AI solver, or else AI will start the game with a new word
        if not keep_target:
            self._target = random.choice(self.words)

        self._current_row = 0
        self._current_col = 0
        self._current_guess = ""
        self._grid_labels = []
        self._keyboard_buttons = {}
        self._guess_history = []
        self._lie_guess = random.randint(0, 1)
        self._lie_used = False
        
        # separately drawing the game
        self._draw_game()
    
    # start the process of solving
    def _start_solver_game(self):
        if self._state != GameState.PLAYING:
            return
        self._new_game(keep_target=True)

        self._state = GameState.AI_SOLVING
        self._solver_candidates = self.words[:]
        
        # after a delay, start the solver step method to handle rest
        self.root.after(700, self._solver_step)

    # Draw the main game screen serially
    def _draw_game(self):
        self._clear_screen()
        self._create_title()
        self._create_solver_button()
        self._create_message_area()
        self._create_grid()
        self._create_keyboard()
    
    #------------- Making and Packing --------------------------
    def _create_title(self):
        title = tk.Label(
            self.root, text="LIEDLE", font=("Helvetica", 40, "bold"), bg=DARK, fg=WHITE
        )
        title.pack(pady=15)

    def _create_solver_button(self):
        self._dark_button(self.root, "USE SOLVER", command=self._start_solver_game)

    def _create_message_area(self):
        self._message_frame = tk.Frame(self.root, bg=DARK)
        self._message_frame.pack(pady=(0, 15))

        self._message_label = tk.Label(
            self._message_frame, font=("Arial", 14, "bold"), bg=DARK, fg=WHITE
        )
        self._error_label = tk.Label(
            self._message_frame, font=("Arial", 13, "bold"), bg=DARK, fg="red"
        )

    def _show_message(self, message):
        self._message_label.pack_forget()
        self._message_label.config(text=message)
        self._message_label.pack()

    def _show_error(self, message):
        self._error_label.pack_forget()
        self._error_label.config(text=message)
        self._error_label.pack()
        self.root.after(2000, self._error_label.pack_forget)

    def _create_grid(self):
        frame = tk.Frame(self.root, bg=DARK)
        frame.pack(pady=20)

        for row in range(MAX_GUESSES):
            current_row = []
            for col in range(WORD_LENGTH):
                label = tk.Label(
                    frame,
                    text="",
                    width=4,
                    height=2,
                    font=("Arial", 24, "bold"),
                    bg=DARK,
                    fg=WHITE,
                    relief="flat",
                    highlightthickness=2,
                    highlightbackground=LIGHT_GREY,
                )
                label.grid(row=row, column=col, padx=5, pady=5)
                current_row.append(label)
            
            # as arrays are stored as a reference, changing this one will change the text
            # This is a clever technique for me!
            self._grid_labels.append(current_row)

    def _create_keyboard(self):
        frame = tk.Frame(self.root, bg=DARK)
        frame.pack(side="bottom", pady=20)

        for row_letters in KEYBOARD_ROWS:
            row_frame = tk.Frame(frame, bg=DARK)
            row_frame.pack(pady=5)
            
            for letter in row_letters:
                button = tk.Button(
                    row_frame,
                    text=letter,
                    width=4,
                    height=2,
                    font=("Arial", 12, "bold"),
                    bg=DARK,
                    fg=WHITE,
                    activebackground="#565758",
                    command=lambda l=letter: self._insert_letter(l),
                )
                button.pack(side="left", padx=2)
                self._keyboard_buttons[letter] = button
    
    # this one will help for keeping a consistent UI 
    def _dark_button(self, parent, text, command):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            width=20,
            font=("Arial", 12, "bold"),
            bg="#2d2d2d",
            fg=WHITE,
            activebackground="#444444",
        )
        button.pack(pady=10)
    
    # for handling physical keyboard, will be ignored when AI is solving
    def _handle_keypress(self, event):
        if self._state == GameState.AI_SOLVING:
            return
        key = event.keysym.upper()
        if len(key) == 1 and key.isalpha():
            self._insert_letter(key)
        elif key == "BACKSPACE":
            self._backspace()
        elif key == "RETURN":
            self._submit_guess()
    
    # I created this one function, but both AI and user will use it 
    def _insert_letter(self, letter):

        if self._current_col >= WORD_LENGTH:
            return
        
        # backspace and enter has separate handler
        if letter == "⌫":
            self._backspace(); return
        if letter == "↵":
            self._submit_guess(); return

        letter = letter.upper()
        self._update_tile(self._current_row, self._current_col, letter)
        self._current_guess += letter
        self._current_col += 1

    def _backspace(self):
        if self._current_col == 0:
            return
        self._current_col -= 1
        self._current_guess = self._current_guess[:-1]
        self._update_tile(self._current_row, self._current_col, "")
        
    # This is for the enter key, the game also checks if the game has been finished right here
    def _submit_guess(self):
        if len(self._current_guess) != WORD_LENGTH:
            return

        if self._current_guess not in self.words:
            self._show_error("Word is not in the word list")
            return

        feedback = get_feedback(self._current_guess, self._target)
        
        # Store the real feedback first, but manipulate the shown "feedback" if needed
        real_feedback = feedback[:]
        lie_happened = False
        
        # check if we have to apply the lie
        if self._current_row == self._lie_guess and not self._lie_used:
            lie_happened = True
            feedback = self._apply_lie(feedback)
            self._show_message(f"⚠︎ A lie occurred in Guess {self._current_row + 1}")
            self._lie_used = True

        self._color_row(self._current_row, feedback)

        self._guess_history.append((self._current_guess, real_feedback, feedback))

        if self._current_guess == self._target:
            if self._state == GameState.AI_SOLVING:
                self._state = GameState.AI_COMPLETE
            else:
                self._state = GameState.GAME_WON

            self.root.after(1800, self._show_end_screen)
            return
        
        # There is a low possibility that the AI could also lose, hehe!
        if self._current_row >= MAX_GUESSES - 1:
            self._state = GameState.GAME_OVER if GameState.PLAYING else GameState.AI_LOST
            self.root.after(1800, self._show_end_screen)
            return
        
        # This is the reason why AI will choose the same word after the lie,
        # we will only apply the filter if current row was not a lie
        if self._state == GameState.AI_SOLVING:
            if not lie_happened:
                self._solver_candidates = solver_filter(
                    self._solver_candidates, self._current_guess, feedback
                )
                
        # update rows, columns and guess
        self._current_row += 1
        self._current_col = 0
        self._current_guess = ""

        if self._state == GameState.AI_SOLVING:
            self.root.after(800, self._solver_step)
    
    # helper to apply the lie, changing one tile color
    def _apply_lie(self, feedback):
        fake = feedback[:]
        index = random.randint(0, 4)
        colors = [GREEN, YELLOW, GREY]
        colors.remove(fake[index])
        fake[index] = random.choice(colors)
        return fake
    
    # When this function is called, it will get the next best possible candidate and type it
    def _solver_step(self):
        guess = solver_next(self._solver_candidates)
        self._solver_type_guess(guess, 0)
    
    # it will type like a real user
    def _solver_type_guess(self, guess, index):
        if index >= len(guess):
            self.root.after(300, self._submit_guess)
            return
        self._insert_letter(guess[index])
        
        # recursive anonymous function, I pushed my brain a bit!
        self.root.after(120, lambda: self._solver_type_guess(guess, index + 1))

    def _update_tile(self, row, col, text):
        self._grid_labels[row][col]["text"] = text
    
    # Color the row according to the feedback, also the keyboard
    def _color_row(self, row, feedback):
        guess = self._current_guess
        
        for col in range(WORD_LENGTH):
            color = feedback[col]
            tile = self._grid_labels[row][col]
            tile["bg"] = color
            tile["highlightbackground"] = color
            letter = guess[col]

            key = self._keyboard_buttons.get(letter)

            if key:
                current = key["bg"]
                if current == GREEN:
                    continue
                if current == YELLOW and color == GREY:
                    continue

                key["bg"] = color


if __name__ == "__main__":
    root = tk.Tk()
    app = Liedle(root)
    root.mainloop()
import os
import random


MAX_GUESSES = 6

# Symbols for feedback
GREEN  = "🟩"
YELLOW = "🟨"
GREY   = "⬜"
LINE = "─"

# load word from the given filepath
def load_words(filepath:str):
    count = 0   
    if not os.path.exists(filepath):
        print(f"Error: the path {filepath} is not found")
        exit(1)
    with open(filepath, 'r') as file:
        content = file.read()
        words = content.split()
    return words

# return a random word from the given wordlist
def choice_word(wordlist):
    return random.choice(wordlist)

def new_word():
    return random.choice(load_words("wordlist.txt"))


# returns the feedback as a list, for example ['⬜', '🟩', '⬜', '🟩', '🟩']
def get_feedback(current:str, target:str):
    result = [GREY] * 5
    target = list(target)
    for i in range(5):
        if (current[i] == target[i]):
            result[i] = GREEN
            target[i] = None
    
    for i in range(5):
        if (current[i] in target):
            result[i] = YELLOW
            target[i] = None
    
    return result

def print_board(guesses:list, feedbacks:list):
    for i in range(len(guesses)):
        print(f"\nGuess {i+1}:")
        print("".join(feedbacks[i]))
        print(" " + " ".join(guesses[i].upper()))
    print("\n" + LINE * 30 + "\n")

def take_guess():
    while True:
        user = input("Enter your guess: ")
        if not user.isalpha():
            print("Please enter a 5-character word with alphabets only")
            continue
        elif len(user) != 5:
            print("Please enter a 5-character word with no numbers")
            continue
        else:
            return user

print("Wordle by Mahtab Hossain")
print(LINE * 30)
guesses = []
feedbacks = []

target = new_word()
for i in range(5):
    guesses.append(take_guess())
    feedbacks.append(get_feedback(guesses[i], target))
    print_board(guesses, feedbacks)
    if guesses[i] == target:
        print("You have won!")
        exit(0)

print("You lose!")
print("The word was " + target.upper())

import sys
import msvcrt  # Windows-specific for character-by-character input

def get_visible_input(prompt):
    """Get input with real-time character echoing on Windows."""
    print(prompt, end="", flush=True)
    chars = []
    while True:
        char = msvcrt.getwch()  # Read a single character
        if char == '\r':  # Enter key
            print()  # Move to new line
            break
        elif char == '\b':  # Backspace
            if chars:
                chars.pop()
                print("\b \b", end="", flush=True)  # Erase last character
        else:
            chars.append(char)
            print(char, end="", flush=True)  # Echo character
    return "".join(chars).strip().lower()

def main():
    print("Test Script for Input Visibility")
    print("Type something and see if it appears. Type 'exit' to quit.")
    while True:
        user_input = get_visible_input("Enter text: ")
        print(f"You entered: {user_input}")
        if user_input == "exit":
            print("Exiting...")
            break

if __name__ == "__main__":
    main()

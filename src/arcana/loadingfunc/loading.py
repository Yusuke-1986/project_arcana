import itertools
import sys
import time

def progress_bar(current, total, width=30):
    ratio = current / total
    filled = int(width * ratio)
    bar = "█" * filled + "." * (width - filled)
    percent = int(ratio * 100)
    sys.stdout.write(f"\r[{bar}] {percent}%")
    sys.stdout.flush()

def spinner(duration=5):
    symbols = itertools.cycle(["|", "/", "-", "\\"])
    end = time.time() + duration
    while time.time() < end:
        sys.stdout.write(f"\rProcessing {next(symbols)}")
        sys.stdout.flush()
        time.sleep(0.1)
    print("\rDone!      ")

def main():
    total = 100
    for i in range(total + 1):
        progress_bar(i, total)
        time.sleep(0.03)
    print()
    spinner()

if __name__ == "__main__":
    main()

import sys

print("deeppicar.py is running")
for line in sys.stdin:
    print(f"Received input: {line.strip()}")

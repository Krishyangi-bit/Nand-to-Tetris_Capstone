"""
Compare two .hack files line by line.

Use it to check that assembler.py gives the same output as the official
nand2tetris assembler:

    python ../assembler.py Pong.asm -o Pong.mine.hack
    (run the official Assembler on Pong.asm -> Pong.hack)
    python compare.py Pong.mine.hack Pong.hack

Line endings (Windows / Linux) and blank lines are ignored.
"""

import sys


def read_words(path):
    with open(path) as f:
        return [line.strip() for line in f if line.strip() != ""]


def main(argv):
    if len(argv) != 3:
        print("Usage: python compare.py mine.hack official.hack")
        return 1

    mine, official = read_words(argv[1]), read_words(argv[2])
    differences = 0

    for i in range(max(len(mine), len(official))):
        a = mine[i] if i < len(mine) else "(missing)"
        b = official[i] if i < len(official) else "(missing)"
        if a != b:
            differences += 1
            if differences <= 10:
                print("ROM[" + str(i) + "]: mine " + a + "  official " + b)

    if differences == 0:
        print("MATCH: " + str(len(mine)) + " instructions are identical.")
        return 0

    print(str(differences) + " line(s) differ.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

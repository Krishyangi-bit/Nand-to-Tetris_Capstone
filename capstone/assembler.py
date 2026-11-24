"""
Hack Assembler  (Nand to Tetris - Capstone, Part B)

Turns a Hack assembly program (.asm) into Hack machine code (.hack).

    python assembler.py Prog.asm            -> writes Prog.hack next to Prog.asm
    python assembler.py Prog.asm -o Out.hack

How it works
------------
First reading  : remove comments and blank lines, and note the address of
                 every label like (LOOP). Labels do not take up a ROM address.
Second reading : turn every instruction into 16 bits.
                 A-instruction  @value  ->  0 + 15-bit value
                 C-instruction  dest=comp;jump  ->  111 a cccccc ddd jjj
                 New variables get RAM addresses 16, 17, 18, ...

Extra feature (K = 56, K mod 3 = 2)
-----------------------------------
Print a warning if the same label is written twice. The first address is
kept, so the output is the same as if the second label was not there.
"""

import os
import sys


# ---------------------------------------------------------------------------
# Tables from the Hack machine language specification
# ---------------------------------------------------------------------------

# comp part -> "a c1 c2 c3 c4 c5 c6"  (a = 0 uses A, a = 1 uses M)
COMP = {
    "0":   "0101010", "1":   "0111111", "-1":  "0111010",
    "D":   "0001100", "A":   "0110000", "!D":  "0001101",
    "!A":  "0110001", "-D":  "0001111", "-A":  "0110011",
    "D+1": "0011111", "A+1": "0110111", "D-1": "0001110",
    "A-1": "0110010", "D+A": "0000010", "D-A": "0010011",
    "A-D": "0000111", "D&A": "0000000", "D|A": "0010101",
    "M":   "1110000", "!M":  "1110001", "-M":  "1110011",
    "M+1": "1110111", "M-1": "1110010", "D+M": "1000010",
    "D-M": "1010011", "M-D": "1000111", "D&M": "1000000",
    "D|M": "1010101",
}

# Commutative forms some programs use (A+D instead of D+A, etc.)
COMP.update({
    "A+D": COMP["D+A"], "M+D": COMP["D+M"],
    "A&D": COMP["D&A"], "M&D": COMP["D&M"],
    "A|D": COMP["D|A"], "M|D": COMP["D|M"],
    "1+D": COMP["D+1"], "1+A": COMP["A+1"], "1+M": COMP["M+1"],
})

JUMP = {
    "":    "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
}

# Predefined symbols
PREDEFINED = {
    "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
    "SCREEN": 16384, "KBD": 24576,
}
for i in range(16):
    PREDEFINED["R" + str(i)] = i

FIRST_VARIABLE_ADDRESS = 16
MAX_A_VALUE = 32767   # an A-instruction has only 15 bits for the value


class AssemblerError(Exception):
    """Raised for a line that cannot be translated."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_line(line):
    """Remove the comment and all spaces from one line of source."""
    comment_start = line.find("//")
    if comment_start != -1:
        line = line[:comment_start]
    return "".join(line.split())


def is_label(line):
    return line.startswith("(") and line.endswith(")")


def dest_bits(dest):
    """dest is any mix of A, D, M (e.g. "AM", "MD"). Order does not matter."""
    for letter in dest:
        if letter not in "ADM":
            raise AssemblerError("invalid dest '" + dest + "'")
    if len(set(dest)) != len(dest):
        raise AssemblerError("invalid dest '" + dest + "'")
    a = "1" if "A" in dest else "0"
    d = "1" if "D" in dest else "0"
    m = "1" if "M" in dest else "0"
    return a + d + m


def translate_c(instruction):
    """dest=comp;jump  ->  111 a cccccc ddd jjj"""
    dest, comp, jump = "", instruction, ""
    if "=" in comp:
        dest, comp = comp.split("=", 1)
    if ";" in comp:
        comp, jump = comp.split(";", 1)

    if comp not in COMP:
        raise AssemblerError("invalid comp '" + comp + "'")
    if jump not in JUMP:
        raise AssemblerError("invalid jump '" + jump + "'")
    if "=" in instruction and dest == "":
        raise AssemblerError("missing dest before '='")

    return "111" + COMP[comp] + dest_bits(dest) + JUMP[jump]


# ---------------------------------------------------------------------------
# The two readings
# ---------------------------------------------------------------------------

def first_pass(source_lines):
    """
    Remove comments and blank lines, record label addresses.

    Returns (instructions, symbols, warnings)
      instructions : list of (line_number, text) - labels are not included
      symbols      : predefined symbols + labels
      warnings     : list of warning strings (duplicate labels)
    """
    symbols = dict(PREDEFINED)
    label_line = {}            # label -> line where it was first written
    instructions = []
    warnings = []

    for line_number, raw in enumerate(source_lines, start=1):
        line = clean_line(raw)
        if line == "":
            continue

        if is_label(line):
            label = line[1:-1]
            if label == "":
                raise AssemblerError("Line " + str(line_number) + ": empty label '()'")

            # ---- Extra feature for K mod 3 == 2: duplicate label warning ----
            if label in label_line:
                warnings.append(
                    "Warning: Line " + str(line_number) + ": label (" + label +
                    ") is written twice (first on line " + str(label_line[label]) +
                    "). Keeping the first address " + str(symbols[label]) + ".")
                continue
            if label in PREDEFINED:
                warnings.append(
                    "Warning: Line " + str(line_number) + ": label (" + label +
                    ") has the same name as a predefined symbol. "
                    "Keeping the predefined value " + str(PREDEFINED[label]) + ".")
                continue

            symbols[label] = len(instructions)   # address of the next instruction
            label_line[label] = line_number
        else:
            instructions.append((line_number, line))

    return instructions, symbols, warnings


def second_pass(instructions, symbols):
    """Turn every instruction into a 16-bit string. Adds variables to symbols."""
    next_variable = FIRST_VARIABLE_ADDRESS
    output = []

    for line_number, text in instructions:
        try:
            if text.startswith("@"):
                value = text[1:]
                if value == "":
                    raise AssemblerError("'@' needs a number or a symbol")
                if value.isdigit():
                    number = int(value)
                    if number > MAX_A_VALUE:
                        raise AssemblerError("number " + value + " is too big (max 32767)")
                else:
                    if value[0].isdigit():
                        raise AssemblerError("symbol '" + value + "' cannot start with a digit")
                    if value not in symbols:          # a new variable
                        symbols[value] = next_variable
                        next_variable += 1
                    number = symbols[value]
                output.append(format(number, "016b"))
            else:
                output.append(translate_c(text))
        except AssemblerError as error:
            raise AssemblerError("Line " + str(line_number) + ": " + str(error))

    return output


def assemble(source_lines):
    """Full assembly. Returns (machine_code_lines, warnings)."""
    instructions, symbols, warnings = first_pass(source_lines)
    machine_code = second_pass(instructions, symbols)
    return machine_code, warnings


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def main(argv):
    if len(argv) not in (2, 4) or (len(argv) == 4 and argv[2] != "-o"):
        print("Usage: python assembler.py Prog.asm [-o Prog.hack]")
        return 1

    asm_path = argv[1]
    if len(argv) == 4:
        hack_path = argv[3]
    else:
        hack_path = os.path.splitext(asm_path)[0] + ".hack"

    try:
        with open(asm_path) as f:
            source_lines = f.read().splitlines()
    except OSError as error:
        print("Error: cannot read " + asm_path + " (" + str(error.strerror) + ")")
        return 1

    try:
        machine_code, warnings = assemble(source_lines)
    except AssemblerError as error:
        print("Error: " + str(error))
        return 1

    for warning in warnings:
        print(warning)

    with open(hack_path, "w", newline="\n") as f:
        for word in machine_code:
            f.write(word + "\n")

    print("Wrote " + str(len(machine_code)) + " instructions to " + hack_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

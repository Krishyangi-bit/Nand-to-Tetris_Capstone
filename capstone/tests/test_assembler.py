"""
Unit tests for assembler.py.   Run from the capstone/ folder:

    python -m unittest tests/test_assembler.py -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import assembler  # noqa: E402

HERE = os.path.dirname(__file__)


def assemble_text(text):
    return assembler.assemble(text.splitlines())


class TestInstructions(unittest.TestCase):

    def test_a_instruction_number(self):
        code, _ = assemble_text("@0\n@1\n@21\n@32767")
        self.assertEqual(code, ["0000000000000000", "0000000000000001",
                                "0000000000010101", "0111111111111111"])

    def test_predefined_symbols(self):
        code, _ = assemble_text("@R15\n@SCREEN\n@KBD\n@SP\n@THAT")
        self.assertEqual([int(w, 2) for w in code], [15, 16384, 24576, 0, 4])

    def test_c_instructions_from_spec(self):
        cases = {
            "D=A":     "1110110000010000",
            "D=D+A":   "1110000010010000",
            "M=D":     "1110001100001000",
            "D=M":     "1111110000010000",
            "D=D-M":   "1111010011010000",
            "D;JGT":   "1110001100000001",
            "0;JMP":   "1110101010000111",
            "M=-1":    "1110111010001000",
            "M=0":     "1110101010001000",
            "MD=M-1":  "1111110010011000",
            "AMD=D|M": "1111010101111000",
            "D;JLE":   "1110001100000110",
            "A=!A":    "1110110001100000",
            "M=M+1":   "1111110111001000",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(assemble_text(source)[0], [expected])

    def test_comments_and_spaces_are_ignored(self):
        code, _ = assemble_text("// comment\n\n   @2   // inline\n  D = A \n")
        self.assertEqual(code, ["0000000000000010", "1110110000010000"])


class TestSymbols(unittest.TestCase):

    def test_labels_point_to_next_instruction(self):
        code, _ = assemble_text("@END\n0;JMP\n(END)\n@END\n0;JMP")
        self.assertEqual(int(code[0], 2), 2)
        self.assertEqual(int(code[2], 2), 2)

    def test_variables_start_at_16(self):
        code, _ = assemble_text("@first\n@second\n@first\n@third")
        self.assertEqual([int(w, 2) for w in code], [16, 17, 16, 18])

    def test_label_used_before_it_is_written(self):
        # A label used before its (LABEL) line must not become a variable.
        code, _ = assemble_text("@LOOP\n0;JMP\n@x\n(LOOP)\n@x")
        self.assertEqual([int(w, 2) for w in code if w[0] == "0"], [3, 16, 16])


class TestExtraFeature(unittest.TestCase):
    """K = 56, K mod 3 = 2: warn when the same label is written twice."""

    def test_duplicate_label_gives_warning(self):
        _, warnings = assemble_text("(LOOP)\n@1\n(LOOP)\n@LOOP\n0;JMP")
        self.assertEqual(len(warnings), 1)
        self.assertIn("Line 3", warnings[0])
        self.assertIn("(LOOP)", warnings[0])
        self.assertIn("first on line 1", warnings[0])

    def test_duplicate_label_keeps_first_address(self):
        code, _ = assemble_text("(LOOP)\n@1\n(LOOP)\n@LOOP\n0;JMP")
        self.assertEqual(int(code[1], 2), 0)

    def test_no_warning_for_normal_program(self):
        with open(os.path.join(HERE, "Max.asm")) as f:
            _, warnings = assembler.assemble(f.read().splitlines())
        self.assertEqual(warnings, [])


class TestErrors(unittest.TestCase):

    def test_invalid_comp_names_the_line(self):
        with self.assertRaises(assembler.AssemblerError) as ctx:
            assemble_text("@2\n\nD=D*A")
        self.assertIn("Line 3", str(ctx.exception))

    def test_number_too_big(self):
        with self.assertRaises(assembler.AssemblerError):
            assemble_text("@32768")

    def test_invalid_jump(self):
        with self.assertRaises(assembler.AssemblerError):
            assemble_text("0;JUMP")


class TestProgramFiles(unittest.TestCase):

    def test_add_matches_official_output(self):
        with open(os.path.join(HERE, "Add.asm")) as f:
            code, _ = assembler.assemble(f.read().splitlines())
        self.assertEqual(code, ["0000000000000010", "1110110000010000",
                                "0000000000000011", "1110000010010000",
                                "0000000000000000", "1110001100001000"])

    def test_rect_sizes(self):
        with open(os.path.join(HERE, "Rect.asm")) as f:
            code, _ = assembler.assemble(f.read().splitlines())
        self.assertEqual(len(code), 25)
        self.assertEqual(code[6], "0100000000000000")   # @SCREEN
        self.assertEqual(code[4], "0000000000010000")   # @counter -> 16
        self.assertEqual(code[8], "0000000000010001")   # @address -> 17


if __name__ == "__main__":
    unittest.main()

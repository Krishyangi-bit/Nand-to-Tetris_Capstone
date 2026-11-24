# Nand to Tetris – Capstone: Make the Computer Draw a Box

**Course:** Nand to Tetris – I (ETCCNT301) · School of Engineering & Technology, K.R. Mangalam University
**Roll number:** 2501010156 · **Personal number K = 56**

> The Hack computer shows a **black box on the screen while a key is pressed**, and clears it when the key is released. The project is built in three parts: the hardware (Part A), an assembler written in Python (Part B), and the box program (Part C).

---

## My values for K = 56

| Item | Formula | Value for K = 56 |
|---|---|---|
| Start row | K | **row 56** |
| Height | 20 rows | **rows 56 – 75** |
| Width | 16 × ((K mod 4) + 1) | 16 × (0 + 1) = **16 pixels (1 word)** |
| Left edge | column 0 | **column 0** |
| First screen word | SCREEN + 32 × K | 16384 + 1792 = **18176** |
| Last screen word | SCREEN + 32 × 75 | 16384 + 2400 = **18784** |
| Assembler extra feature | K mod 3 = **2** | **Warn if the same label is written twice** |

---

## Repository layout

```
Nand-to-Tetris_Capstone/
├── README.md
└── capstone/
    ├── hdl/                  Part A – all chips, from Nand up to Computer
    │   ├── Not, And, Or, Xor, Mux, DMux                 (Project 1)
    │   ├── Not16, And16, Or16, Mux16, Or8Way,
    │   │   Mux4Way16, Mux8Way16, DMux4Way, DMux8Way     (Project 1)
    │   ├── HalfAdder, FullAdder, Add16, Inc16, ALU      (Project 2)
    │   ├── Bit, Register, RAM8 … RAM16K, PC             (Project 3)
    │   └── Memory, CPU, Computer                        (Project 5)
    ├── assembler.py          Part B – two-pass Hack assembler
    ├── Box.asm               Part C – the box program (Hack assembly)
    ├── Box.hack              Part C – Box.asm assembled by assembler.py
    └── tests/
        ├── Add.asm, Max.asm, Rect.asm      test programs
        ├── DuplicateLabel.asm              tests the extra feature
        ├── BadLine.asm                     tests the line-numbered error
        ├── test_assembler.py               15 unit tests
        └── compare.py                      diff my .hack against the official one
```

---

## Part A – Build the computer

All chips are written in HDL using only `Nand` and `DFF` as primitives (plus the
`Screen`, `Keyboard`, `ROM32K`, `ARegister` and `DRegister` chips that the
course always provides as built-ins). **No built-in replacements were needed
for my own lab chips.**

### Memory.hdl
One 15-bit address space split into three parts:

| Address | Range (hex) | Goes to | Selected by |
|---|---|---|---|
| 0 – 16383 | 0x0000 – 0x3FFF | RAM16K | `address[14] = 0` |
| 16384 – 24575 | 0x4000 – 0x5FFF | Screen | `address[14..13] = 10` |
| 24576 | 0x6000 | Keyboard | `address[14..13] = 11` |

`load` is routed with two `DMux` chips; the output is picked with a
`Mux4Way16` on `address[13..14]`. The keyboard is read-only.

### CPU.hdl
- **A register** loads the instruction itself for an A-instruction, or the ALU output for a C-instruction with `d1 = 1`.
- **D register** loads the ALU output when `d2 = 1`.
- **a-bit** (`instruction[12]`) chooses whether the ALU's second input is A or M.
- **writeM** = C-instruction and `d3`.
- **Jump**: `(j1 and out<0) or (j2 and out=0) or (j3 and out>0)`, only for C-instructions; the PC then loads A, otherwise it increments.

### Computer.hdl
`ROM32K → CPU → Memory`, with `Memory.out` fed back as the CPU's `inM`.

### How to test (official test files)
1. Open the **Hardware Simulator** from the nand2tetris software suite.
2. Copy the official test files from `nand2tetris/projects/05/` into `capstone/hdl/`:
   `CPU.tst/.cmp`, `Memory.tst/.cmp`, `ComputerAdd.tst/.cmp`, `ComputerMax.tst/.cmp`,
   `ComputerRect.tst/.cmp` and the programs `Add.hack`, `Max.hack`, `Rect.hack`.
3. Load each `.tst` file and press **Run** → *"End of script – Comparison ended successfully"*.
4. Screenshots of the results go into the report.

> Tip: because `RAM16K.hdl` is in the same folder, the simulator builds the RAM
> from my own chips, which makes the Computer tests run slowly. That is
> expected. Moving `RAM*.hdl` out of the folder makes it use the fast built-in
> RAM instead (mention it in the report if you do).

---

## Part B – The assembler (`assembler.py`)

```bash
cd capstone
python assembler.py Box.asm                 # writes Box.hack
python assembler.py tests/Max.asm -o Max.hack
```

Requires only Python 3, with no extra packages.

### How it works
| Step | What happens |
|---|---|
| **First reading** | Each line has its `//` comment and all spaces removed; blank lines are dropped. A label `(LOOP)` is stored with the address of the *next* instruction and takes no ROM address. |
| **Second reading** | `@number` → `0` + 15-bit binary. `@symbol` → looked up; a new symbol becomes a **variable at RAM 16, 17, 18, …** A C-instruction `dest=comp;jump` → `111` + `a cccccc` + `ddd` + `jjj` from the tables. |
| **Symbol table** | Starts with the predefined symbols: `R0`–`R15`, `SP`, `LCL`, `ARG`, `THIS`, `THAT`, `SCREEN` (16384), `KBD` (24576). |

### Extra feature for K mod 3 = 2: duplicate-label warning
If the same label is written twice, the assembler prints a warning with both
line numbers and **keeps the first address**, so the rest of the output does not change:

```
$ python assembler.py tests/DuplicateLabel.asm
Warning: Line 8: label (LOOP) is written twice (first on line 5). Keeping the first address 0.
Wrote 4 instructions to tests/DuplicateLabel.hack
```

The assembler also reports bad lines without crashing:

```
$ python assembler.py tests/BadLine.asm
Error: Line 6: invalid comp 'D*A'
```

### Testing
```bash
cd capstone
python -m unittest tests/test_assembler.py -v      # 15 tests
```

To check against the **official assembler** (Add, Max, Rect and Pong):
```bash
# Pong.asm is in nand2tetris/projects/06/pong/
python assembler.py Pong.asm -o Pong.mine.hack
# assemble Pong.asm with the official Assembler -> Pong.hack
python tests/compare.py Pong.mine.hack Pong.hack
# MATCH: <n> instructions are identical.
```

---

## Part C – The box program (`Box.asm`)

### Plan
1. **Settings:** `startrow = 56`, `height = 20`, `width = 1` word.
2. **Start address:** `start = SCREEN + 32 × startrow`. Hack has no multiply instruction, so the program adds 32 to `SCREEN` 56 times, which gives 18176.
3. **Main loop (forever):**
   - Read `KBD`. Non-zero → `color = -1` (all 16 bits = 16 black pixels), zero → `color = 0` (white).
   - Paint the box: for each of the 20 rows, write `color` into `width` words, then move down one row (`+32`).
   - Go back and read the keyboard again.

Painting white when no key is pressed is what makes the box disappear on release.
This is the course's `Fill.asm` idea, drawn on a smaller area.

### Built in small steps
one dash (one word, `M=-1` at 18176) → wider dash (loop over words) →
box (loop over rows, +32 each time) → add the keyboard check.

### Run it
1. `cd capstone && python assembler.py Box.asm` (uses **my own** assembler).
2. Open the **CPU Emulator**, load `Box.hack`.
3. Set animation to *No animation* and speed to fast, then press **Run**.
4. Click the keyboard icon and **hold any key**: a 16 × 20 black box appears at the left edge, rows 56–75. Release the key and it disappears.

### Viva quick changes
All the box settings are at the top of `Box.asm`:

| Change | Edit |
|---|---|
| Move the box down / up | `@56` → e.g. `@100` (start row) |
| Make it taller | `@20` → e.g. `@40` (height) |
| Make it wider | `@1` → e.g. `@3` (width in 16-pixel words) |

After editing, re-run `python assembler.py Box.asm` and reload `Box.hack`.

---

## Verification done

| Check | Result |
|---|---|
| Gates, multi-bit and multi-way chips (exhaustive / random) | pass |
| ALU vs a reference model, 300 random inputs and flag checks | pass |
| RAM64, PC vs reference models (random sequences) | pass |
| Memory address map (RAM / Screen / Keyboard, keyboard read-only) | pass |
| Computer running Add and Max (several inputs), and Rect | pass |
| Assembler: Add.hack identical to the official output, Max/Rect correct | pass |
| Assembler unit tests (15) | pass |
| Box.hack: key held → 20 black words at 18176 … 18784; released → screen clear | pass |

---

## Submission checklist
- [x] `capstone/` folder with the HDL files, `assembler.py`, `Box.asm`, `Box.hack`
- [ ] Screenshots: CPU, Memory, ComputerAdd, ComputerMax, ComputerRect tests
- [ ] Screenshot of the box in the CPU Emulator
- [ ] Report (3–4 pages) on ZOSIMA: name, roll no., K = 56, box size 16 × 20 at row 56, screenshots, one mistake I fixed

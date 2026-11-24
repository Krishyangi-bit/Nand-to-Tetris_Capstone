// Box.asm  -  Nand to Tetris Capstone, Part C
//
// Roll number 2501010156  ->  K = 56
//
// While any key is pressed, a black box is drawn on the screen.
// When the key is released, the box is cleared (drawn white).
//
//   Start row : K                  = 56
//   Height    : 20 rows            -> rows 56 to 75
//   Width     : 16 * ((K mod 4)+1) = 16 * (0 + 1) = 16 pixels = 1 word
//   Left edge : column 0
//
// One screen row = 32 words, one word = 16 pixels.
// Row r starts at SCREEN + 32*r, so the box starts at
// 16384 + 32*56 = 16384 + 1792 = 18176.
//
// Variables:  startrow, height, width - box settings
//             start   - screen address of the top-left word of the box
//             color   - 0 (white) or -1 (black, all 16 bits set)
//             rowaddr - address of the first word of the current row
//             addr    - address of the word being painted
//             r, c    - row and column counters, i - multiply counter

// ===================== Box settings ======================
// (To move or resize the box, change only these numbers.)

   @56
   D=A
   @startrow
   M=D              // startrow = K = 56

   @20
   D=A
   @height
   M=D              // height = 20 rows

   @1
   D=A
   @width
   M=D              // width = (K mod 4) + 1 = 1 word (16 pixels)

// ========= start = SCREEN + 32 * startrow ================
// Hack has no multiply, so add 32 to SCREEN, startrow times.

   @SCREEN
   D=A
   @start
   M=D              // start = 16384

   @startrow
   D=M
   @i
   M=D              // i = startrow
(MULTIPLY)
   @i
   D=M
   @MAIN
   D;JEQ            // if i == 0, start is ready
   @32
   D=A
   @start
   M=M+D            // start = start + 32 (move one row down)
   @i
   M=M-1            // i = i - 1
   @MULTIPLY
   0;JMP

// ===================== Main loop =========================
// Read the keyboard and pick the colour.

(MAIN)
   @KBD
   D=M              // D = key code (0 if no key is pressed)
   @BLACK
   D;JNE            // any key pressed -> black
   @color
   M=0              // no key -> white
   @DRAW
   0;JMP
(BLACK)
   @color
   M=-1             // -1 = 1111111111111111 = 16 black pixels

// ====================== Draw the box =====================

(DRAW)
   @start
   D=M
   @rowaddr
   M=D              // rowaddr = first row of the box
   @height
   D=M
   @r
   M=D              // r = number of rows left to paint

(ROWLOOP)
   @width
   D=M
   @c
   M=D              // c = number of words left in this row
   @rowaddr
   D=M
   @addr
   M=D              // addr = first word of this row

(COLLOOP)
   @color
   D=M
   @addr
   A=M
   M=D              // RAM[addr] = color   (paint 16 pixels)
   @addr
   M=M+1            // next word to the right
   @c
   MD=M-1           // one word less to paint
   @COLLOOP
   D;JGT            // more words in this row? repeat

   @32
   D=A
   @rowaddr
   M=M+D            // rowaddr = rowaddr + 32 (next row down)
   @r
   MD=M-1           // one row less to paint
   @ROWLOOP
   D;JGT            // more rows? repeat

   @MAIN
   0;JMP            // check the keyboard again (forever)

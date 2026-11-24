// Test for the extra feature (K mod 3 = 2):
// the label (LOOP) is written twice, so the assembler prints a warning.
// The first (LOOP) is kept, so the second one is ignored.

(LOOP)
   @i
   M=M+1
(LOOP)
   @LOOP
   0;JMP

// Test for error messages: line 6 has an invalid comp, so the assembler
// stops with a message that names the line instead of crashing.

@2
D=A
D=D*A
@0
M=D

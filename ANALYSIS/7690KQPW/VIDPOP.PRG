* Procedure.....: VIDPOP.PRG
* Author........: G. Rothbart, TRG
* Function......: Fast Linkage to VIDPOP for the WordTech Compiler
* Parameters....: STRING = SAYWHAT screen name or VIDPOP command
* Reference.....: SAYWHAT 3.0 Manual, WordTech Manual, pp 105-106,
*                 DOS Tech Ref Manual on Interrupt 10H.
*
* NOTE..........: This is a procedure that ONLY works with the WordTech
*                 compiler, and will NOT run in dBASE by itself!  The idea
*                 is to replace your VIDPOP calls of the form
*
*                 ?? chr(255)+chr(255)+'<screen name or VIDPOP command>/'
*
*                                       -or-
*
*                 RUN POP <screen name or VIDPOP command>
*
*                                     - with-
*
*                 DO VIDPOP WITH '<screen name or VIDPOP command>'
*                 (in this method, the 2 lead-in characters and the
*                  delimiting forward slash are not part of the syntax--
*                  but you definitely need the quotes!)
*
* NOTE..........: Since this syntax passes its parameter using the WITH
*                 syntax, you MUST have the following code active as a
*                 PROCEDURE in the main program using a SET PROCEDURE TO
*                 statement. If you use more than one procedure file, the
*                 following code must be in each procedure file that is
*                 active when a call to VIDPOP is required.
*
*
PROCEDURE VIDPOP
PARAMETERS string
STORE 256*14 TO ah
STORE 255 TO al
*
* -- send 2 FF's to Int 10H:
*
STORE ah+al to axreg
DOSINT 16,axreg
STORE ah+al TO axreg
DOSINT 16,axreg
*
* -- send SAYWHAT screen name or VIDPOP command to Int 10H:
*
STORE 1 TO i
DO WHILE i<=LEN(string)
     STORE ASC(SUBSTR(string,i,1)) TO al
     STORE ah+al TO axreg
     DOSINT 16,axreg
     STORE i+1 TO i
ENDDO
*
* --Send the forward slash "/" delimiter to Int 10H:
*
STORE 47 TO al
STORE ah+al TO axreg
DOSINT 16,axreg
*
* -- Screen is UP!  Now just return.
*
RETURN

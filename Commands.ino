/*
 Instructions for Data
 
  8 bits wide per instruction     00  00  0000

  Pairing Instruction
      xx xx xxxx
        0-1 OpCode
        2-3 Source
        4-7 Values
      Op Code
         00 - Pairing mode
      Source
         Values at which light switch we are changing variables, up to 4 lights
      Values
        0-2
        0: PLR=0, Motion=2;Button=5;LED=8
        1: PLR=1, Motion=3;Button=6;LED=9
        2: PLR=2, Motion=4;Button=7;LED=12
        Limited by I/O Pins
        10 & 11 reserved for HC-05
         
  Preference Instruction Type
      xx xx xxxx
        0-1 OpCode
        2-3 Source
        4-7 Values
      Op Code
        10  -  Setting plr level
        01  -  Setting timeout value
      Source
        Values at which light switch we are changing variables, up to 4 lights
         
  Database Instruction 
      xx  xx xxxx   
         0-1 Opcode
         2-3 Source
         4-7 Values
      Op Code
        11  -  Updating Data to Firebase
      Values
        Don't Care, State, Sense, Motion


    00 xx xxxx pairing
    01 xx xxxx setting timeout value
    10 xx xxxx setting plr level
    11 xx xxxx actively listening

 

 */
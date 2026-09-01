# Shell discipline for this repo (BINDING — the terminal tool hardline-blocks malformed payloads)
- NEVER nest quotes or $( ) inside ssh strings. Ever.
- For ANY command more complex than "run X": write it to a script file first (cat > /tmp/x.sh), chmod +x, then run bash /tmp/x.sh
- One command per terminal call. No semicolon chains with quotes inside.
- Blocked command = rewrite as a script file, do NOT retry variations inline (each block wastes an iteration; the budget ends the session)

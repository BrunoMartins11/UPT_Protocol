# UPT Protocol

"Safe" unicorn based magic for data transfer using UDP.

No snakes were harmed coding this script.


# Ideas while on drugs

- Add proper Go Back N
- Connection control
- List files if running as server
- Download more than one file
- Error Control

# Ideas when we high as Elon

- Encryption
- See extras on BB
- Use a proper language
- Maybe leave the unicorns and drugs



# Ignore

## We high then it passed


| Field | Size (bits) |
|-------|-------------|
| Seq   | 4 x 8       |
| AckN  | 4 x 8       |
| Nack  | 1           |
| Type  | 4           | SYN ACK FIN RST
| <b>Total</b> | <b>69</b> |
| <b>Next Byte alignment</b> | <b>72</b> |

Max Header Size: 512 bytes

Payload:
 - 4027 bits if we don't align bytes
 - 4024 bits (503 bytes) if we align

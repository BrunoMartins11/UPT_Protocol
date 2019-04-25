# UPT Protocol

"Safe" unicorn based magic for data transfer using UDP.

No snakes were harmed coding this script.


# Ideas while on drugs

- List files if running as server

# Ideas when we high as Elon

- Encryption
- See extras on BB
- Use a proper language
- Maybe leave the unicorns and drugs



# Ignore

## Message format

The message is 1472 bytes divided up into the following:
- 5 bytes: msgtype
- 4 bytes: seqno
- 1458 bytes: message/data
- 2 bytes: checksum
- 3 bytes: packet delimiters '|'

# UPT Protocol

"Safe" unicorn based magic for data transfer using UDP.

No snakes were harmed coding this script.


## Message format

The message is 1472 bytes divided up into the following:
- 5 bytes: msgtype
- 4 bytes: seqno
- 1458 bytes: message/data
- 2 bytes: checksum
- 3 bytes: packet delimiters '|'


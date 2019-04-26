import binascii

""""
msg type | seqno | data | checksum

The message is 1472 bytes divided up into the following:
- 5 bytes: msgtype
- 4 bytes: seqno
- 1458 bytes: message/data
- 2 bytes: checksum
- 3 bytes: packet delimiters '|'
"""


def make_packet(msg_type=None, seqno=None, msg=None, packet=None):
    if msg_type is not None:
        body = b"".join([msg_type.encode(), b'|', bytes(str(seqno).encode()), b'|', msg, b'|'])
        checksum = generate_checksum(body)
        return_packet = body + checksum
        return return_packet
    else:
        body = b"".join([packet[0].encode(), b'|', bytes(str(packet[1]).encode()), b'|', packet[2], b'|'])
        checksum = generate_checksum(body)
        return_packet = body + checksum
        return return_packet


def split_packet(message):
    pieces = message.split(b'|')
    msg_type, seqno = pieces[0:2]  # type and seqno
    checksum = pieces[-1]  # checksum
    data = b'|'.join(pieces[2:-1])  # data
    return msg_type.decode(), int(seqno), data, checksum


def validate_checksum(message):
    try:
        msg, reported_checksum = message.rsplit(b'|', 1)
        msg += b'|'
        return generate_checksum(msg) == reported_checksum
    except:
        return False


def generate_checksum(message):
    return str(binascii.crc32(message) & 0xffffffff).encode()

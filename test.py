  
from rtmidi.midiconstants import *
def send_channel_message( status, data1=None, data2=None, ch=None):
        """Send a MIDI channel mode message."""
        msg = [(status & 0xF0) | ((ch if ch else 5) - 1 & 0xF)]

        if data1 is not None:
            msg.append(data1 & 0x7F)

            if data2 is not None:
                msg.append(data2 & 0x7F)

        print(msg)
def send_control_change( cc=0, value=0, ch=None):
    """Send a 'Control Change' message."""
    send_channel_message(CONTROL_CHANGE, cc, value, ch=ch)
def send_program_change( program=0, ch=None):
    """Send a 'Program Change' message."""
    send_channel_message(PROGRAM_CHANGE, program, ch=ch)
def send_channel_pressure( value=0, ch=None):
    """Send a 'Monophonic Pressure' (Channel Pressure) message."""
    send_channel_message(CHANNEL_PRESSURE, value, ch=ch)
def send_pitch_bend( value=8192, ch=None):
    """Send a 'Pitch Bend' message."""
    send_channel_message(PITCH_BEND, value & 0x7f,
                              (value >> 7) & 0x7f, ch=ch)
def send_bank_select( bank=None, msb=None, lsb=None, ch=None):
    """Send 'Bank Select' MSB and/or LSB 'Control Change' messages."""
    if bank is not None:
        msb = (bank >> 7) & 0x7F
        lsb = bank & 0x7F
    if msb is not None:
        send_control_change(BANK_SELECT_MSB, msb, ch=ch)
    if lsb is not None:
        send_control_change(BANK_SELECT_LSB, lsb, ch=ch)
send_bank_select(1,ch=5)

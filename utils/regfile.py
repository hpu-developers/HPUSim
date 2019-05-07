"""
    This is a general purpose register file.

    R0 is reserved for PC
"""
from collections import OrderedDict

class RegFile:

    def __init__(self, size):

        self.reg  = OrderedDict()

        # Intialize the reg file
        for i in range(size):
            self.reg[i] = 0

    def read(self, addr):
        """
        Reads the requested register
        """

        return self.reg[addr]

    def write(self, addr, value):
        """
        Writes the requested value
        """

        self.reg[addr] = value

    def increment(self, addr):
        """
        Increments the requested add
        """

        self.reg[addr] += 1

        return self.reg[addr]

    def decrement(self, addr):
        """
        Decrements the requested addr
        """
        self.reg[addr] -= 1

        return self.reg[addr]

    def log_state(self):

        # print(" \n Status of the Regfile: " + str(self.reg))
        return None

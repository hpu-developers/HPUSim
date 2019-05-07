"""
    This file contains all the helper functions used
"""

from accelerators import *


def check_branch(branch_type, source, result):

    """
        Checks if the branch condition is True or False
    """

    if(branch_type == 'beq'):
        return source == result
    elif(branch_type == 'bne'):
        return source != result
    elif(branch_type == 'bge'):
        return source >= result
    elif(branch_type == 'ble'):
        return source <= result


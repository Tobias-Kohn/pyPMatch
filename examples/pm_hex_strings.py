#
# (c) 2018, Tobias Kohn
#
# Created: 12.09.2018
# Updated: 12.09.2018
#
# License: Apache 2.0
#

def is_hex_string(s):
    match s:
        case ['0', 'x'|'X', first @ ('0' | ... | '9' | 'A' | ... | 'F' | 'a' | ... | 'f'), *rest]:
            return hex(int(first + rest, 16)).upper()
        case _:
            return '-'

def main():
    print("Testing 0x1F3C", is_hex_string("0x1F3C"))
    print("Testing 0xQ123", is_hex_string("0xQ123"))
    print("Testing 2x153C", is_hex_string("2x153C"))
    print("Testing 0XFF34", is_hex_string("0XFF34"))

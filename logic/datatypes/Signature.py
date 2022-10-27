import sys


_byte_hamming_weight = [0]
for i in range(8):
    _byte_hamming_weight.extend([k + 1 for k in _byte_hamming_weight])


class Signature:
    """Container for basic signature processing methods
    Initialize signatures as int, don't use this class!

    Boolean function computation requires 1-signature of corresponding length stored as attribute in this class
    Call setlength() class method preliminarily for correct computations
    Default length is 1
    """
    length = 1
    all_ones = 1

    @classmethod
    def setlength(cls, l: int) -> None:
        """Set signature length and 1-signature"""
        cls.length = l
        cls.all_ones = (1 << l) - 1

    @classmethod
    def invert(cls, s: int) -> int:
        """Return inverted signature
        Requires signature length
        """
        return s ^ cls.all_ones

    @classmethod
    def to_list(cls, s: int) -> list:
        """Convert signature to bit list

        Example:
            s = 0b0100
            Signature.setlength(4)
            Signature.to_list(s)                        # >>>[0, 1, 0, 0]
        """
        l = []
        while s:
            l.append(s & 1)
            s >>= 1
        l += [0 for i in range(len(l), cls.length)]
        l.reverse()
        return l

    @staticmethod
    def from_list(l: list) -> int:
        """Convert bit list to signature

        Example:
            l = [0, 1, 0, 0]
            s = Signature.from_list(l)
            bin(s)                                  # >>>'0b100'        (first 0 is not displayed)
        """
        mask = 1
        sign = 0
        for x in reversed(l):
            if x:
                sign += mask
            mask <<= 1
        return sign

    @classmethod
    def hamming_weight(cls, s: int) -> int:
        """Return number of 1's in signature"""
        bytestr = s.to_bytes(int((cls.length - 1) / 8) + 1, sys.byteorder)
        return sum(_byte_hamming_weight[byte] for byte in bytestr)

    @staticmethod
    def odc_equivalent(s1: int, s2: int, odc: int) -> bool:
        """Check signatures for ODC-equivalence
        Consider list representations of s1, s2 and odc, then this function
            returns True if s1[i] == s2[i] for all i where odc[i] == 1
            and False otherwise

        Example:
            Signature.odc_equivalent(0b0011, 0b1011, 0b0111)                # >>>True
        """
        diff = s1 ^ s2
        return not diff & odc

    @staticmethod
    def decode(s: int, it: 'Iterable') -> list:
        """Return elements corresponding to 1's in reversed signature (first element corresponds to the last bit)
        Similar to itertools.compress()

        Example:
            Signature.decode(0b1101, 'abcd')                      # >>>['a', 'c', 'd']
        """
        l = []
        for el in it:
            if s == 0:
                break
            if s & 1:
                l.append(el)
            s >>= 1
        return l

    @classmethod
    def exhaustive(cls, vars: 'Iterable') -> 'Iterable':
        """Yield pairs (<variable>, <signature>) for exhaustive simulation"""
        N = len(vars)
        cls.setlength(1 << N)
        signs = (int(('0' * (1 << i) + '1' * (1 << i)) * (1 << (N - i - 1)), 2) for i in range(N))
        return zip(vars, signs)

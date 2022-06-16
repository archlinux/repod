from typing import Any


def cmp(a: Any, b: Any) -> int:
    """
    C style cmp function returning the compare result as int

    Compare the two objects a and b and return an integer according to
    the outcome. The return value is negative if x < b, zero if a == b
    and strictly positive if a > b.

    Parameters
    ----------
    a: any
        First input to compare
    b: any
        Second input to compare

    Returns
    -------
    int
        -1 if 'b' is greater
         0 if both are equal
         1 if 'a' is greater
    """
    return int(a > b) - int(a < b)

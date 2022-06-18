from itertools import takewhile

from .util import cmp

PYALPM_VERCMP = False
try:
    from pyalpm import vercmp as pyalpm_vercmp  # pragma: no-cover-nonlinux

    PYALPM_VERCMP = True  # pragma: no-cover-nonlinux
except ImportError:  # pragma: nocover
    pass


def vercmp(a: str, b: str) -> int:  # noqa: C901
    """Compare alpha and numeric segments of two versions.

    The comparison algorithm is based on libalpm pacman's vercmp behavior.

    Calls pyalpm's interface in case it's available.

    Returns
    -------
    int
        -1 if a is newer than b
         0 if a and b are the same version
         1 if b is newer than a
    """

    if PYALPM_VERCMP:  # pragma: no-cover-nonlinux
        return int(pyalpm_vercmp(a, b))  # pragma: no-cover-nonlinux

    # easy comparison to see if versions are identical
    if a == b:
        return 0

    one: str
    two: str

    one_ptr = ptr1 = 0
    two_ptr = ptr2 = 0

    # loop through each version segment of a and b and compare them
    while one_ptr < len(a) and two_ptr < len(b):
        while one_ptr < len(a) and not a[one_ptr].isalnum():
            one_ptr += 1
        while two_ptr < len(b) and not b[two_ptr].isalnum():
            two_ptr += 1

        # If we ran to the end of either, we are finished with the loop
        if one_ptr >= len(a) or two_ptr >= len(b):
            break

        # If the separator lengths were different, we are finished
        if (one_ptr - ptr1) != (two_ptr - ptr2):
            return -1 if (one_ptr - ptr1) < (two_ptr - ptr2) else 1

        # adjust left side pointer to current segment start
        ptr1 = one_ptr
        ptr2 = two_ptr
        one = a[one_ptr:]
        two = b[two_ptr:]

        """
        grab first completely alpha or completely numeric segment
        leave one and two pointing to the start of the alpha or numeric
        segment and walk ptr1 and ptr2 to end of segment
        """
        if one and one[0].isdecimal():
            ptr1 += len(list(takewhile(str.isdecimal, one)))
            ptr2 += len(list(takewhile(str.isdecimal, two)))
            isnum = True
        else:
            ptr1 += len(list(takewhile(str.isalpha, one)))
            ptr2 += len(list(takewhile(str.isalpha, two)))
            isnum = False

        # adjust current segment end with the updated right side pointer
        one = a[one_ptr:ptr1]
        two = b[two_ptr:ptr2]

        """
        take care of the case where the two version segments are
        different types: one numeric, the other alpha (i.e. empty)
        numeric segments are always newer than alpha segments
        """
        if not two:
            return 1 if isnum else -1

        if isnum:
            # throw away any leading zeros - it's a number, right?
            one = one.lstrip("0")
            two = two.lstrip("0")

            # whichever number has more digits wins (discard leading zeros)
            if len(one) > len(two):
                return 1
            if len(two) > len(one):
                return -1

        """
        strcmp will return which one is greater - even if the two
        segments are alpha or if they are numeric.  don't return
        if they are equal because there might be more segments to
        compare
        """
        rc = cmp(one, two)
        if rc:
            return rc

        # advance left side pointer to current right side pointer
        one_ptr = ptr1
        two_ptr = ptr2

    # set leftover using the left side pointer once the segment loop finished
    one = a[one_ptr:]
    two = b[two_ptr:]

    """
    this catches the case where all numeric and alpha segments have
    compared identically but the segment separating characters were
    different
    """
    if not one and not two:
        return 0

    """
    the final showdown. we never want a remaining alpha string to
    beat an empty string. the logic is a bit weird, but:
    - if one is empty and two is not an alpha, two is newer.
    - if one is an alpha, two is newer.
    - otherwise one is newer.
    """
    if (not one and not two[0].isalpha()) or (one and one[0].isalpha()):
        return -1
    return 1


def pkg_vercmp(a: str, b: str) -> int:
    """Compare individual components of two versions by splitting them
    based in alpm's version schema into epoch, pkgver, pkgrel.

    The comparison algorithm is based on libalpm pacman's vercmp behavior.

    Calls pyalpm's interface in case it's available.

    Returns
    -------
    int
        -1 if a is newer than b
         0 if a and b are the same version
         1 if b is newer than a
    """

    if PYALPM_VERCMP:  # pragma: no-cover-nonlinux
        return int(pyalpm_vercmp(a, b))  # pragma: no-cover-nonlinux

    epoch1 = a.split(":")[0] if ":" in a else ""
    epoch2 = b.split(":")[0] if ":" in b else ""

    pkgver_pkgrel1 = a.split(":")[1] if ":" in a else a
    pkgver_pkgrel2 = b.split(":")[1] if ":" in b else b

    pkgver1 = pkgver_pkgrel1.split("-")[0]
    pkgver2 = pkgver_pkgrel2.split("-")[0]

    pkgrel1 = pkgver_pkgrel1.split("-")[1]
    pkgrel2 = pkgver_pkgrel2.split("-")[1]

    # return epoch comparison if unequal
    ret = cmp(epoch1, epoch2)
    if ret:
        return ret

    # return pkgver comparison if unequal
    ret = vercmp(pkgver1, pkgver2)
    if ret:
        return ret

    # return pkgrel comparison
    return vercmp(pkgrel1, pkgrel2)

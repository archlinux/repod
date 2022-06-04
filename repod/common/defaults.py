from typing import List

ARCHITECTURES: List[str] = [
    "aarch64",
    "any",
    "arm",
    "armv6h",
    "armv7h",
    "i486",
    "i686",
    "pentium4",
    "riscv32",
    "riscv64",
    "x86_64",
    "x86_64_v2",
    "x86_64_v3",
    "x86_64_v4",
]


def architectures_for_architecture_regex() -> str:
    """Return ARCHITECTURES formatted for use in the ARCHITECTURE regular expression

    Returns
    -------
    str
        The ARCHITECTURES formatted as an "or" concatenated string
    """

    return r"|".join(ARCHITECTURES)

from enum import IntEnum


class FieldTypeEnum(IntEnum):
    """An IntEnum to distinguish the different types of entries in a file

    Attributes
    ----------
    STRING: int
        An entry of type 'str'
    INT: int
        An entry of typoe 'int'
    STRING_LIST: int
        An entry of type 'List[str]'
    """

    STRING = 0
    INT = 1
    STRING_LIST = 2

class RepoManagementError(Exception):
    """A class of Errors that is raised on issues with handling a repository database"""


class RepoManagementFileError(RepoManagementError):
    """An Error that is raised on issues with reading or writing files using repo_managment"""


class RepoManagementValidationError(RepoManagementError):
    """An Error that is raised on issues with validating files using repo_managment"""


class RepoManagementFileNotFoundError(RepoManagementFileError, FileNotFoundError):
    """An Error that is raised when a file can not be found"""


class TaskError(RepoManagementError):
    """An Error that is raised when an error occurs in a Task"""


class FileParserError(RepoManagementError):
    """An Error that is raised when an error occurs during parsing of a file"""

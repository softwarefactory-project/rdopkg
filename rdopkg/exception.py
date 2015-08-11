from utils.exception import RdopkgException
from utils.exception import CommandFailed, CommandNotFound, SpecFileNotFound, \
    IncompleteChangelog, MultipleSpecFilesFound, SpecFileParseError, \
    InvalidAction, ModuleNotAvailable, RpmModuleNotAvailable, \
    BuildArchSanityCheckFailed, BranchNotFound


class UserAbort(RdopkgException):
    msg_fmt = "Aborted by user."


class NoActionInProgress(RdopkgException):
    msg_fmt = "No action in progress."


class ActionInProgress(RdopkgException):
    msg_fmt = "Please `--continue` or `--abort` previous action before " \
              "running a new one."


class ActionFunctionNotAvailable(RdopkgException):
    msg_fmt = "Action function not available: %(action)s"


class RequiredActionArgumentNotAvailable(RdopkgException):
    msg_fmt = "Required argument of '%(action)s' action not available: %(arg)s"


class InvalidUsage(RdopkgException):
    msg_fmt = "Invalid usage: %(why)s"


class InvalidQuery(RdopkgException):
    msg_fmt = "Invalid query: %(why)s"


class InvalidPackageFilter(RdopkgException):
    msg_fmt = "Invalid package filter: %(why)s"


class CantGuess(RdopkgException):
    msg_fmt = "Unable to determine %(what)s: %(why)s"


class ManualResolutionNeeded(RdopkgException):
    msg_fmt = "Your intervention is required. Run `rdopkg -c` again when done."


class ConfigError(RdopkgException):
    msg_fmt = "Configuration error: %(what)s"


class RepoError(RdopkgException):
    msg_fmt = "Repository error: %(what)s"


class CommandOutputParseError(RdopkgException):
    msg_fmt = "Failed to parse %(tool)s output:\n%(output)s"


class CoprError(RdopkgException):
    msg_fmt = "Copr error: %(error)s"


class FileNotFound(RdopkgException):
    msg_fmt = "File not found: %(path)s"


class UpdateFileNotFound(FileNotFound):
    msg_fmt = "Update file not found: %(path)s"


class UpdateCheckFailed(RdopkgException):
    msg_fmt = "Update check failed: %(fail)s"


class NotADirectory(RdopkgException):
    msg_fmt = "Not a directory: %(path)s"


class NotAFile(RdopkgException):
    msg_fmt = "Not a file: %(path)s"


class NewPackageAlreadyPresent(RdopkgException):
    msg_fmt = "Can't copy package, file already exists: %(path)s"


class ToolNotFound(RdopkgException):
    msg_fmt = "%(tool)s not found in %(path)s and it's parents."


class ActionRequired(RdopkgException):
    msg_fmt = "Action required"


class ActionFinished(RdopkgException):
    msg_fmt = "Action finished"


class ActionGoto(RdopkgException):
    msg_fmt = "Jump to action: %(goto)s"


class DebugAbort(RdopkgException):
    msg_fmt = "DEBUG abort"


class RequirementNotMet(RdopkgException):
    msg_fmt = "Requirement not met: %(what)s"


class InternalAction(RdopkgException):
    msg_fmt = "Unhandled internal action: %(action)s"

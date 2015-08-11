class RdopkgException(Exception):
    msg_fmt = "An unknown error occurred"

    def __init__(self, msg=None, **kwargs):
        self.kwargs = kwargs
        if not msg:
            try:
                msg = self.msg_fmt % kwargs
            except Exception as e:
                # kwargs doesn't mach those in message.
                # Returning this is still better than nothing.
                message = self.msg_fmt
        super(RdopkgException, self).__init__(msg)


class CommandFailed(RdopkgException):
    msg_fmt = "Command failed: %(cmd)s"


class CommandNotFound(RdopkgException):
    msg_fmt = "Command not found: %(cmd)s"


class InvalidRemoteBranch(RdopkgException):
    msg_fmt = "Git remote not found for remote branch: %(branch)s"


class BranchNotFound(RdopkgException):
    msg_fmt = "Expected git branch not found: %(branch)s"


class SpecFileNotFound(RdopkgException):
    msg_fmt = "No .spec files found."


class IncompleteChangelog(RdopkgException):
    msg_fmt = "Description of changes is missing in %%changelog."


class MultipleSpecFilesFound(RdopkgException):
    msg_fmt = "Multiple .spec files found. Expected only one."


class SpecFileParseError(RdopkgException):
    msg_fmt = "Error parsing .spec file '%(spec_fn)s': %(error)s"


class ModuleNotAvailable(RdopkgException):
    msg_fmt = "Module %(module)s is not available. Unable to continue."


class RpmModuleNotAvailable(ModuleNotAvailable):
    msg_fmt = ("Module rpm is not available. It is required to parse .spec "
               "files. Pro tip: `yum install rpm-python`")


class InvalidAction(RdopkgException):
    msg_fmt = "Invalid action: %(action)s"


class BuildArchSanityCheckFailed(RdopkgException):
    msg_fmt = ("Due to mysterious ways of rpm, BuildArch needs to be placed "
               "AFTER SourceX and PatchXXXX lines in .spec file, otherwise "
               "%%{patches} macro will be empty and `git am %%{patches}` will "
               "fail. You're welcome ;)")

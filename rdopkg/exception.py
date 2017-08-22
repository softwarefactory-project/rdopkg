class RdopkgException(Exception):
    msg_fmt = "An unknown error occurred"
    exit_code = 1

    def __init__(self, msg=None, exit_code=None, **kwargs):
        self.kwargs = kwargs
        if not msg:
            try:
                msg = self.msg_fmt % kwargs
            except Exception:
                # kwargs doesn't match those in message.
                # Returning this is still better than nothing.
                msg = self.msg_fmt
        if exit_code is not None:
            self.exit_code = exit_code
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


class MultipleChangelog(RdopkgException):
    msg_fmt = "Multiple %%changelog sections found. Expected only one."


class MultipleSpecFilesFound(RdopkgException):
    msg_fmt = "Multiple .spec files found. Expected only one."


class SpecFileParseError(RdopkgException):
    msg_fmt = "Error parsing .spec file '%(spec_fn)s': %(error)s"


class ModuleNotAvailable(RdopkgException):
    msg_fmt = "Module %(module)s is not available. Unable to continue."


class RpmModuleNotAvailable(ModuleNotAvailable):
    msg_fmt = ("Module rpm is not available. It is required to parse .spec "
               "files. Pro tip: `dnf install rpm-python`")


class InvalidAction(RdopkgException):
    msg_fmt = "Invalid action: %(action)s"


class BuildArchSanityCheckFailed(RdopkgException):
    msg_fmt = ("Due to mysterious ways of rpm, BuildArch needs to be placed "
               "AFTER SourceX and PatchX lines in .spec file, "
               "otherwise %%{patches} macro will be empty "
               "and both %%autosetup and `git am %%{patches}` will fail.\n\n"
               "Please move BuildArch AFTER SourceX and PatchX.")


class DuplicatePatchesBaseError(RdopkgException):
    msg_fmt = ("Please make sure to only have one "
               "# patches_base= entry in .spec")


class UserAbort(RdopkgException):
    msg_fmt = "Aborted by user."


class NoActionInProgress(RdopkgException):
    msg_fmt = "No action in progress."


class ActionInProgress(RdopkgException):
    msg_fmt = "Please `--continue` or `--abort` previous action before " \
              "running a new one."


class ActionFunctionNotAvailable(RdopkgException):
    msg_fmt = "Action function not available: %(module)s:%(action)s"


class RequiredActionArgumentNotAvailable(RdopkgException):
    msg_fmt = "Required argument of '%(action)s' action not available: %(arg)s"


class InvalidUsage(RdopkgException):
    msg_fmt = "Invalid usage: %(why)s"


class InvalidQuery(RdopkgException):
    msg_fmt = "Invalid query: %(why)s"


class InvalidRDOPackage(RdopkgException):
    msg_fmt = "Package not found in rdoinfo: %(package)s"


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


class OnlyPatchesIgnoreUsed(RdopkgException):
    msg_fmt = ("update-patches attempted with only #patches_ignore magic "
               "comment in the spec file. Currently it is not safe to run "
               "update-patches without #patches_base specified AFTER "
               "#patches_ignore.")


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


class UnverifiedPatch(RdopkgException):
    msg_fmt = "Patch not validated by CI, use --force to override"


class NoPatchesChanged(RdopkgException):
    msg_fmt = "No patches changed"


class NoDistgitChangesFound(RdopkgException):
    msg_fmt = "No distgit changes found"

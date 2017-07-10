from pbr.version import VersionInfo

_v = VersionInfo('rdopkg').semantic_version()
__version__ = _v.release_string()
VERSION = __version__
version_info = _v.version_tuple()

import pbr.version

version_info = pbr.version.VersionInfo('rdopkg')
try:
    __version__ = version_info.version_string()
except AttributeError:
    __version__ = None

__all__ = ['__version__']

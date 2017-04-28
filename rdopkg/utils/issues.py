import re


def search_bug_references(text_blob):
    """Return list of bug refs found for provided txt"""

    if text_blob is None:
        return []

    return re.findall(r'rhbz#(\d+)', text_blob)

from rdopkg.utils import specfile


def get_tag(tag, expand_macros=False):
    spec = specfile.Spec()
    val = spec.get_tag(tag, expand_macros=expand_macros)
    print(val)


def set_tag(tag, value):
    spec = specfile.Spec()
    spec.set_tag(tag, value)
    spec.save()


def get_macro(macro, expand_macros=False):
    spec = specfile.Spec()
    val = spec.get_macro(macro, expanded=expand_macros)
    print(val)


def set_macro(macro, value):
    spec = specfile.Spec()
    spec.set_macro(macro, value)
    spec.save()

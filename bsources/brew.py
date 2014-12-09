from rdoupdate.bsources.koji_ import KojiSource


class BrewSource(KojiSource):
    name = 'brew'
    tool = 'brew'

# -*- encoding: utf-8 -*-

import random
import re

from rdopkg.utils import log

# replace red with another green for more positive experience
COLORS = ['green', 'green', 'blue', 'yellow', 'magenta', 'cyan', 'white']
WISDOM = [
    u"We are the universe observing itself.",
    u"Not having any problems is a problem.",
    u"Deriving meaning from words is a great pleasure.",
    u"There is always more work. ¯\_(ツ)_/¯",
    u"rdopkg likes you ;)",
    u"Don't take life too seriously.",
    u"rdopkg is here for you *^^*",
    u"When you're the smartest person in a room, you're in the wrong room.",
    u"Do what you want cause a pirate is free and you are a pirate.",
    u"Free and Open Source Software has won the war \o/",
    u"We've learned as much as we have suffered.",
    u"Bend the universe to your will using words.",
    u"At least you're not writing Visual Basic.",
    u"Using words we command machines that run the world.",
    u"Cooperation is hard to establish and hard to maintain. Don't give up.",
    u"Work will become obsolete as soon as the singularity is born.",
    u"Life is not a zero-sum game.",
    u"Never give up, never surrender!",
    u"Apply critical thinking.",
    u"Construct Additional Pylons!",
    u"Have you tried turning it off and on again?",
    u"Minimalism is the answer.",
    u"Firing orbital friendship cannon on this location.",
    (u"Humans put everything into boxes because it's easier that way. "
     u"Packaging is important."),
    (u"Language is the most powerful tool known to humankind. "
     u"Don't you enjoy using it?"),
    (u"Scientists explore the universe as it is, "
     u"engineers create the universe that has never been."),
]


def royal_rainbow(lulz):
    s = '\n'
    for lul in re.split(r'\s+', lulz):
        s += '{t.%s}%s ' % (random.choice(COLORS), lul)
    s += '\n'
    print(s.format(t=log.term))


def can_haz_doctor():
    advice = random.choice(WISDOM)
    royal_rainbow(advice)

""" Named tuples """
from collections import namedtuple

# Referenced in Card.py for pairing a card name with a default
# value for it. Used in [...]
Section = namedtuple("Section", "name default")

# Used in Deck.py to pair card names and card objects with
# the same name
CardPair = namedtuple("CardPair", "num cardobj")
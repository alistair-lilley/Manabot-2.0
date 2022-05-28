import re, io, json
from collections import namedtuple
from PIL import Image


Section = namedtuple("Section", "name default")

NAME = "name"
POWER = "power"
TOUGHNESS = "toughness"
LEGALITIES = "legalities"

"""
MANACOST = "convertedManaCost"
COLORS = "colors"
COLORID = "colorIdentity"
PT = "pt"
TEXT = "text"
TYPE = "type"
LEGALITIES = "legalities"
"""

class Card:
    '''
        A Card is a singular object that contains a selected section of the information
        pertaining to that card, as well as its image as a PIL object. Two cards can
        be compared to each other and evaluated as <, >, or == based on their names.
    '''
    # cardInfoSections is passed list of Section tuples for extracting from cardJson
    def __init__(self, cardJsonPath, cardImageDir, cardInfoSections):
        with open(cardJsonPath) as readCard:
            cardJson = json.load(readCard)
        self.cardinfo = self._extract(cardJson, cardInfoSections)
        self.image = io.BytesIO()
        image = Image.open(cardImageDir)
        image.save(self.image, 'JPEG')

    def __lt__(self, otherCard):
        return self._compCardsAlphabetically(otherCard)

    def __gt__(self, otherCard):
        return not self._compCardsAlphabetically(otherCard)

    def __eq__(self, otherCard):
        return self.cardinfo[NAME] == otherCard.getName()

    def _compCardsAlphabetically(self, otherCard):
        thisname = self.cardinfo[NAME]
        otherCardName = otherCard.getName()
        for thisChar, otherChar in list(zip(thisname, otherCardName)):
            if thisChar < otherChar:
                return True
            elif thisChar > otherChar:
                return False
        return len(thisname) < len(otherCardName)

    def getName(self):
        return self.cardinfo[NAME]

    def getShortName(self):
        return self._simplify(self.cardinfo[NAME])

    def getNameSimple(self):
        return self._simplify(self.getName())

    def getLegalities(self):
        return self.cardinfo[LEGALITIES]

    def getLegality(self, legality):
        return self.cardinfo[LEGALITIES][legality]

    def _extract(self, cardJson, cardInfoSections):
        cardinfo = dict()
        for section in cardInfoSections:
            if section.name in cardJson:
                if not cardJson[section.name]:
                    cardinfo[section.name] = section.default
                else:
                    if type(cardJson[section.name]) == dict:
                        cardinfo[section.name] = cardJson[section.name]
                    else:
                        cardinfo[section.name] = str(cardJson[section.name])
        return cardinfo

    def retAllCardInfo(self):
        return self.cardinfo, self.image

    def _simplify(self, string):
        return re.sub(r'[\W\s]', '', string).lower()

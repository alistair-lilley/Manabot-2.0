
NAME = "name"
POWER = "power"
TOUGHNESS = "toughness"

"""
MANACOST = "convertedManaCost"
COLORS = "colors"
COLORID = "colorIdentity"
PT = "pt"
TEXT = "text"
TYPE = "type"
"""

class Card:

    def __init__(self, cardJson, cardImage, cardInfoSections):
        self.cardinfo = self._extract(cardJson, cardInfoSections)
        #self.image = Image.open(cardImage)

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

    def _extract(self, cardJson, cardInfoSections):
        cardinfo = dict()
        for section in cardInfoSections:
            if section.section in cardJson:
                if not cardJson[section.section]:
                    cardinfo[section.name] = section.default
                else:
                    cardinfo[section.name] = str(cardJson[section.section])
            elif section.name == "P/T":
                cardinfo[section.name] = cardinfo[POWER] + "/" + cardinfo[TOUGHNESS]
        '''cardinfo[NAME] = cardJson[NAME]
        cardinfo[MANACOST] = str(int(cardJson[MANACOST]))
        if COLORS in cardJson and cardJson[COLORS]:
            cardinfo[COLORS] = ''.join(cardJson[COLORS])
        else:
            cardinfo[COLORS] = 'C'
        if COLORID in cardJson:
            cardinfo[COLORID] = ''.join(cardJson[COLORID])
        else:
            cardinfo[COLORID] = 'C'
        if POWER in cardJson:
            cardinfo[POWER] = str(cardJson[POWER])
            cardinfo[TOUGHNESS] = str(cardJson[TOUGHNESS])
            cardinfo[PT] = str(cardJson[POWER]) + '/' + str(cardJson[TOUGHNESS])
        else:
            cardinfo[POWER] = "N/A"
            cardinfo[TOUGHNESS] = "N/A"
            cardinfo[PT] = "N/A"
        if TEXT in cardJson:
            cardinfo[TEXT] = cardJson[TEXT]
        else:
            cardinfo[TEXT] = "N/A"'''
        return cardinfo

    def retAllCardInfo(self):
        return self.cardinfo  # , self.image
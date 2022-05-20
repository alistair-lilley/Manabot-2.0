from Card import Card
from collections import namedtuple
import xml.etree.ElementTree as ET

ZIP = "zip"
COD = "cod"
MWDECK = "mwdeck"
TXT = "txt"
RAW = "rawtext"
IMAGEPATH = "/cardimages/"
JSONPATH = "/jsoncards/"
NAME = 'name'
NUMBER = 'number'

CardListing = namedtuple("CardListing", "count card")

class Deck:

    def __init__(self, deckFile, fileType, dataDir, infoSections, textDir):
        self.textdir = textDir
        jsonpaths = dataDir + JSONPATH
        imagepaths = dataDir + IMAGEPATH
        if fileType == RAW:
            cardList = self._fromRaw(deckFile)
            self.name, self.comments, self.mainboard, self.sideboard = cardList
        else:
            cardList = self._fromFile(deckFile, fileType)
            self.name, self.comments, self.mainboard, self.sideboard = cardList
        for card in self.mainboard:
            cardname = self.mainboard[card].card
            self.mainboard[card].card = Card(jsonpaths + cardname, imagepaths + cardname, infoSections)

    def _fromFile(self, deckFile, fileType):
        deckData = open(deckFile).read()
        if fileType == COD:
            return self._fromcod(deckData)
        elif fileType == MWDECK:
            return self._frommwDeck(deckData)
        elif fileType == TXT:
            return self._fromtxt(deckData)
        else:
            return deckData

    def _frommwDeck(self, deckFile):
        lines = [line.strip() for line in open(deckFile)]
        comments = []
        mainboard = {}
        sideboard = {}
        for line in lines:
            if line[0] == '/':
                comments.append(line)
            elif line[0].isdigit():
                num, _, name = line.split(' ', 2)
                mainboard[name] = CardListing(num, name)
            elif line[0] == 'S':
                sb, blank, num, _, name = line.split(' ', 4)  # A little tricky to parse
                sideboard[name] = CardListing(num, name)
        return comments, mainboard, sideboard


    def _fromcod(self, deckData):
        CODtree = ET.ElementTree(ET.fromstring(deckData))
        root = CODtree.getroot()
        comments = []
        mainboard = {}
        sideboard = {}
        for zone in root:
            if zone.tag in ['deckname','comments'] and zone.text:
                # This catches comments, they start with "//"
                for t in zone.text.split('\n'):
                    comments.append("//"+t)
            elif zone.tag == 'zone':
                for card in zone:
                    if zone.attrib[NAME] == 'main':
                        # Get the number of a type of card along with what the card is
                        # (e.g. '1 Sol Ring' or '10 Plains')
                        mainboard[card.attrib[NAME]] = CardListing(card.attrib[NUMBER], card.attrib[NAME])
                    # If it's sideboarded, add 'SB: '
                    elif zone.attrib[NAME] == 'side':
                        sideboard[card.attrib[NAME]] = CardListing(card.attrib[NUMBER], card.attrib[NAME])
        return comments, mainboard, sideboard

    def _fromtxt(self, deckFile):
        pass

    def _fromRaw(self, deckRaw):
        pass

    def toTxtFile(self):
        outtext = '\n'.join(self.name + self.comments
                            + self.mainboard.keys() + ['SB: ' + card for card in self.sideboard.keys()])
        with open(self.textdir + self.comments[0])

    def getBans(self, bannedList):
        pass

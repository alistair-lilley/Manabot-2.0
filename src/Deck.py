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
SAVEPATH = "/textfiles/"
NAME = 'name'
NUMBER = 'number'
BANNED = 'banned'
RESTRICTED = 'restricted'

CardPair = namedtuple("CardPair", "num cardobj")

class Deck:

    def __init__(self, deckFile, fileType, dataDir, infoSections, textDir):
        self.textdir = textDir
        self.name = deckFile
        self.jsonpaths = dataDir + JSONPATH
        self.imagepaths = dataDir + IMAGEPATH
        self.savedir = dataDir + SAVEPATH
        self.infoSections = infoSections
        self.comments, self.mainboard, self.sideboard = self._parseDeck(deckFile, fileType)

    def _makeCard(self, card):
        return Card(self.jsonpaths + card, self.imagepaths + card, self.infoSections)

    def _parseDeck(self, deckFile, fileType):
        if fileType == RAW:
            cardList = self._fromRaw(deckFile)
            comments, mainboard, sideboard = cardList
        else:
            cardList = self._fromFile(deckFile, fileType)
            comments, mainboard, sideboard = cardList
        return comments, mainboard, sideboard

    def _fromFile(self, deckFile, fileType):
        deckData = open(deckFile).read()
        if fileType == COD:
            return self._fromcod(deckData)
        elif fileType in [MWDECK, TXT] :
            return self._from_mwDeck_txt(deckData, fileType)
        else:
            return deckData

    # cod file is basically an xml file, so we parse it like an XML tree
    # deckData is passed in as a string of the XML (cod) file
    def _fromcod(self, deckData):
        codtree = ET.ElementTree(ET.fromstring(deckData))
        codroot = codtree.getroot()
        comments = []
        mainboard = {}
        sideboard = {}
        for zone in codroot:
            if zone.tag in ['deckname','comments'] and zone.text:
                comments.append(["//" + line for line in zone.text.split('\n')])
            elif zone.tag == "zone" and zone.attrib[NAME] == 'main':
                mainboard = self._getBoard_cod(zone)
            elif zone.tag == "zone" and zone.attrib[NAME] == 'side':
                sideboard = self._getBoard_cod(zone)
        return comments, mainboard, sideboard

    def _getBoard_cod(self, zone):
        board = {}
        for card in zone:
            if zone.attrib[NAME] == 'main':
                board[card.attrib[NAME]] = CardPair(card.attrib[NUMBER], self._makeCard(card.attrib[NAME]))
        return board

    # This is both for txt and mwDeck, because the only difference is the number of times you split the line
    # mwDeck is in the format `1 [ZEN] Marsh Flats`, so you want to skip the setID in the middle
    # txt doesn't have the setID, and that's the only difference
    def _from_mwDeck_txt(self, deckFile, ext):
        if ext == MWDECK:
            splitnum = 2
        else:
            splitnum = 1
        comments = []
        mainboard = {}
        sideboard = {}
        lines = deckFile.split('\n')
        for line in lines:
            if line[0] == '/':
                comments.append(line)
            elif line[0].isdigit:
                num, setid, card = line.split(' ', splitnum)
                mainboard[card] = CardPair(num, self._makeCard(card))
            elif line[0] == 'S':
                line = line[3:].strip()
                num, setid, card = line.split(' ', splitnum)
                sideboard[card] = CardPair(num, self._makeCard(card))
        return comments, mainboard, sideboard

    def _fromRaw(self, deckRaw):
        return self._from_mwDeck_txt(deckRaw, TXT)

    def _toText(self):
        deckText = ''
        if self.comments:
            comments = ['// ' + comment for comment in self.comments]
            deckText += '\n'.join(comments) + '\n'
        mainboard = [self.mainboard[card].num + ' ' + self.mainboard[card].cardobj.getName() for card in self.mainboard]
        deckText += '\n'.join(mainboard)
        if self.sideboard:
            sideboard = ['SB: ' + self.sideboard[card].num + ' '
                         + self.sideboard[card].cardobj.getName() for card in self.sideboard]
            deckText += '\n' + '\n'.join(sideboard)
        return deckText
        
    def toTxtFile(self):
        with open(self.savedir + self.name, 'w') as saveDeckFile:
            decktext = self._toText()
            saveDeckFile.write(decktext)

    def _toBanText(self, bannedsets, restrictedsets):
        out = "**Banned cards**"
        for banset in bannedsets:
            out += f'\n__{banset}__'
            for card in bannedsets[banset]:
                out += '\n' + card
        out += "\n**Restricted cards**"
        for restset in restrictedsets:
            out += f'\n__{restset}__'
            for card in restrictedsets[restset]:
                out += '\n' + card
        return out

    def getBans(self):
        bannedCards = {}
        restrictedCards = {}
        for card in {**self.mainboard, **self.sideboard}:
            legalities = self.mainboard[card].cardobj.getLegalities()
            for legality in legalities:
                if legalities[legality] == BANNED:
                    bannedCards[legality] = bannedCards.get(legality, []) \
                                            + [self.mainboard[card].cardobj.getName()]
                elif legalities[legality] == RESTRICTED:
                    restrictedCards[legality] = restrictedCards.get(legality, []) \
                                                + [self.mainboard[card].cardobj.getName()]
        bans = self._toBanText(bannedCards, restrictedCards)
        return bans

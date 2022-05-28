from src.Card import Card
from collections import namedtuple
import xml.etree.ElementTree as ET
import re

ZIP = "zip"
COD = "cod"
MWDECK = "mwDeck"
TXT = "txt"
RAW = "rawtext"
IMAGEPATH = "cardimages/"
JSONPATH = "jsoncards/"
SAVEPATH = "textfiles/"
NAME = 'name'
NUMBER = 'number'
BANNED = 'banned'
RESTRICTED = 'restricted'
LEGAL = 'legal'

CardPair = namedtuple("CardPair", "num cardobj")

class Deck:
    '''
        A deck is a collection of cards (implemented as Card objects).
    '''
    def __init__(self, deckFile, fileType, dataDir, infoSections, textDir):
        self.textdir = textDir
        self.datadir = dataDir
        self.name = deckFile
        self.jsonpaths = dataDir + JSONPATH
        self.imagepaths = dataDir + IMAGEPATH
        self.savedir = dataDir + SAVEPATH
        self.infoSections = infoSections
        formats = open('testdata/formats.txt')
        self.default_legality_formats = {line.strip().split(',')[0] : line.strip().split(',')[1]
                                         for line in formats}
        formats.close()
        self.comments, self.mainboard, self.sideboard = self._parseDeck(deckFile, fileType)

    def _makeCard(self, card):
        card = self._simplify(card)
        return Card(self.jsonpaths + card + '.json', self.imagepaths + card + '.jpg', self.infoSections)

    def _parseDeck(self, deckFile, fileType):
        if fileType == RAW:
            cardList = self._fromRaw(deckFile)
            comments, mainboard, sideboard = cardList
        else:
            cardList = self._fromFile(deckFile, fileType)
            comments, mainboard, sideboard = cardList
        return comments, mainboard, sideboard

    def _fromFile(self, deckFile, fileType):
        with open(self.datadir + "testdecks/" + deckFile + '.' + fileType) as read_deck_file:
            deckData = read_deck_file.read()
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
                comments += ["//" + line for line in zone.text.split('\n')]
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
            if not line:
                continue
            if line[0] == '/':
                comments.append(line)
            elif line[0] == 'S':
                # Cuts out the SB: and strips it so it's the same format as a non-sideboard line
                line = line.split(' ', 1)[1].strip()
                num, card = self._pull_num_card(line, splitnum)
                sideboard[card] = CardPair(num, self._makeCard(card))
            elif line[0].isdigit:
                num, card = self._pull_num_card(line, splitnum)
                mainboard[card] = CardPair(num, self._makeCard(card))
        return comments, mainboard, sideboard

    def _fromRaw(self, deckRaw):
        return self._from_mwDeck_txt(deckRaw, TXT)

    def _toText(self):
        deckText = ''
        if self.comments:
            comments = [comment for comment in self.comments]
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

    def _toBanText(self, bannedsets, restrictedsets, legalsets, set_legalities):
        out = "**Banned cards**"
        for banset in bannedsets:
            set_proper_name = set_legalities[banset]
            out += f'\n__{set_proper_name}__'
            for card in bannedsets[banset]:
                out += '\n' + card
        out += "\n**Restricted cards**"
        for restset in restrictedsets:
            set_proper_name = set_legalities[restset]
            out += f'\n__{set_proper_name}__'
            for card in restrictedsets[restset]:
                out += '\n' + card
        '''out += "\n**Legal cards**"
        for legset in legalsets:
            out += f'\n__{set_legalities[legset]}__'
            for card in legalsets[legset]:
                out += '\n' + card'''
        return out

    def _get_bans_from_legalities(self, set_legalities):
        bannedCards = {}
        restrictedCards = {}
        legal_cards = {}
        allboards = {**self.mainboard, **self.sideboard}
        for card in allboards:
            cardobj = allboards[card].cardobj
            legalities = [legalset for legalset in cardobj.getLegalities() if legalset in list(set_legalities.keys())]
            for legality in legalities:
                format_legality = self._simplify(cardobj.getLegality(legality))
                if format_legality == BANNED:
                    bannedCards[legality] = bannedCards.get(legality, []) + [cardobj.getName()]
                elif format_legality == RESTRICTED:
                    restrictedCards[legality] = restrictedCards.get(legality, []) + [cardobj.getName()]
                elif format_legality == LEGAL:
                    legal_cards[legality] = legal_cards.get(legality, []) + [cardobj.getName()]
        bans = self._toBanText(bannedCards, restrictedCards, legal_cards, set_legalities)
        return bans

    def get_bans(self, legalities=None):
        if not legalities:
            legalities = self.default_legality_formats
        return self._get_bans_from_legalities(legalities)

    def _simplify(self, string):
        return re.sub(r'[\W\s]', '', string).lower()

    # Pulls the number and the card from a line in a txt or mwDeck file line
    def _pull_num_card(self, line, numsplit):
        card_line_split = line.split(' ', numsplit)
        num = card_line_split[0]
        card = card_line_split[-1]
        return num, card


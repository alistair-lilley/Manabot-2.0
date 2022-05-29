""" Deck object """
import xml.etree.ElementTree as ET
from src.Card import Card
from src.named_tuples import CardPair
from src.globals import JSON_PATH, IMAGE_PATH, TEXT_FILE_PATH   # Paths
from src.globals import RAW, COD, MWDECK, TXT  # File extensions
from src.globals import NAME, NUMBER, BANNED, RESTRICTED, LEGAL  # card data features
from src.globals import simplify


class Deck:
    """
        A deck is a collection of cards (implemented as Card objects).
    """
    def __init__(self, deck_file, file_type, data_dir, info_sections, text_dir):
        self.textdir = text_dir
        self.datadir = data_dir
        self.name = deck_file
        self.jsonpaths = data_dir + JSON_PATH
        self.imagepaths = data_dir + IMAGE_PATH
        self.savedir = data_dir + TEXT_FILE_PATH
        self.info_sections = info_sections
        formats = open('testdata/formats.txt')
        self.default_legality_formats = {line.strip().split(',')[0]: line.strip().split(',')[1]
                                         for line in formats}
        formats.close()
        self.comments, self.mainboard, self.sideboard = self._parse_deck(deck_file, file_type)

    def _make_card(self, card):
        card = simplify(card)
        return Card(self.jsonpaths + card + '.json', self.imagepaths + card + '.jpg', self.info_sections)

    def _parse_deck(self, deck_file, file_type):
        if file_type == RAW:
            card_list = self._from_raw(deck_file)
            comments, mainboard, sideboard = card_list
        else:
            card_list = self._from_file(deck_file, file_type)
            comments, mainboard, sideboard = card_list
        return comments, mainboard, sideboard

    def _from_file(self, deck_file, file_type):
        with open(self.datadir + "testdecks/" + deck_file + '.' + file_type) as read_deck_file:
            deck_data = read_deck_file.read()
        if file_type == COD:
            return self._from_cod(deck_data)
        elif file_type in [MWDECK, TXT]:
            return self._from_mwdeck_txt(deck_data, file_type)
        else:
            return deck_data

    # cod file is basically an xml file, so we parse it like an XML tree
    # deckData is passed in as a string of the XML (cod) file
    def _from_cod(self, deck_data):
        codtree = ET.ElementTree(ET.fromstring(deck_data))
        codroot = codtree.getroot()
        comments = []
        mainboard = {}
        sideboard = {}
        for zone in codroot:
            if zone.tag in ['deckname','comments'] and zone.text:
                comments += ["//" + line for line in zone.text.split('\n')]
            elif zone.tag == "zone" and zone.attrib[NAME] == 'main':
                mainboard = self._get_cod_zone(zone)
            elif zone.tag == "zone" and zone.attrib[NAME] == 'side':
                sideboard = self._get_cod_zone(zone)
        return comments, mainboard, sideboard

    def _get_cod_zone(self, zone):
        board = {}
        for card in zone:
            if zone.attrib[NAME] == 'main':
                board[card.attrib[NAME]] = CardPair(card.attrib[NUMBER], self._make_card(card.attrib[NAME]))
        return board

    # This is both for txt and mwDeck, because the only difference is the number of times you split the line
    # mwDeck is in the format `1 [ZEN] Marsh Flats`, so you want to skip the setID in the middle
    # txt doesn't have the setID, and that's the only difference
    def _from_mwdeck_txt(self, deck_file, ext):
        if ext == MWDECK:
            splitnum = 2
        else:
            splitnum = 1
        comments = []
        mainboard = {}
        sideboard = {}
        lines = deck_file.split('\n')
        for line in lines:
            if not line:
                continue
            if line[0] == '/':
                comments.append(line)
            elif line[0] == 'S':
                # Cuts out the SB: and strips it so it's the same format as a non-sideboard line
                line = line.split(' ', 1)[1].strip()
                num, card = self._pull_num_card(line, splitnum)
                sideboard[card] = CardPair(num, self._make_card(card))
            elif line[0].isdigit:
                num, card = self._pull_num_card(line, splitnum)
                mainboard[card] = CardPair(num, self._make_card(card))
        return comments, mainboard, sideboard

    def _from_raw(self, deck_raw):
        return self._from_mwdeck_txt(deck_raw, TXT)

    def _to_text(self):
        deck_text = ''
        if self.comments:
            comments = [comment for comment in self.comments]
            deck_text += '\n'.join(comments) + '\n'
        mainboard = [self.mainboard[card].num + ' ' + self.mainboard[card].cardobj.get_name() for card in self.mainboard]
        deck_text += '\n'.join(mainboard)
        if self.sideboard:
            sideboard = ['SB: ' + self.sideboard[card].num + ' '
                         + self.sideboard[card].cardobj.get_name() for card in self.sideboard]
            deck_text += '\n' + '\n'.join(sideboard)
        return deck_text
        
    def to_txt_file(self):
        with open(self.savedir + self.name, 'w') as save_deck_file:
            decktext = self._to_text()
            save_deck_file.write(decktext)

    def _to_ban_text(self, bannedsets, restrictedsets, legalsets, set_legalities):
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
        # Makes the output too long; ignore this for now
        # out += "\n**Legal cards**"
        # for legset in legalsets:
            # out += f'\n__{set_legalities[legset]}__'
            # for card in legalsets[legset]:
                # out += '\n' + card
        return out

    def _get_bans_from_legalities(self, set_legalities):
        banned_cards = {}
        restricted_cards = {}
        # Stays empty (for now)
        legal_cards = {}
        allboards = {**self.mainboard, **self.sideboard}
        for card in allboards:
            cardobj = allboards[card].cardobj
            legalities = [legalset for legalset in cardobj.get_legalities() if legalset in list(set_legalities.keys())]
            for legality in legalities:
                format_legality = simplify(cardobj.get_legality(legality))
                if format_legality == BANNED:
                    banned_cards[legality] = banned_cards.get(legality, []) + [cardobj.get_name()]
                elif format_legality == RESTRICTED:
                    restricted_cards[legality] = restricted_cards.get(legality, []) + [cardobj.get_name()]
                # elif format_legality == LEGAL:
                    # legal_cards[legality] = legal_cards.get(legality, []) + [cardobj.getName()]
        bans = self._to_ban_text(banned_cards, restricted_cards, legal_cards, set_legalities)
        return bans

    def get_bans(self, legalities=None):
        if not legalities:
            legalities = self.default_legality_formats
        return self._get_bans_from_legalities(legalities)

    # Pulls the number and the card from a line in a txt or mwDeck file line
    def _pull_num_card(self, line, numsplit):
        card_line_split = line.split(' ', numsplit)
        num = card_line_split[0]
        card = card_line_split[-1]
        return num, card


""" Global variables across files"""
import re

# Paths and directories
IMAGE_PATH = "cardimages"
JSON_PATH = "jsoncards"
TEXT_FILE_PATH = "textfiles"

# Card info keys
NAME = "name"
POWER = "power"
TOUGHNESS = "toughness"
LEGALITIES = "legalities"
MANACOST = "convertedManaCost"
COLORS = "colors"
COLORID = "colorIdentity"
PT = "pt"
TEXT = "text"
TYPE = "type"
NUMBER = "number"
BANNED = "banned"
RESTRICTED = "restricted"
LEGAL = "legal"

# Deck file formats
ZIP = "zip"
COD = "cod"
MWDECK = "mwDeck"
TXT = "txt"
RAW = "rawtext"

# Values
DAY = 60*60*24


# Global methods
def simplify(string):
    return re.sub(r'[\W\s]', '', string).lower()

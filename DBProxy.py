
import aiohttp, re, json, filetype, urllib, os, asyncio
from PIL import Image

NAME = 'name'
IMAGE_PATH = 'cardimages'
JSON_PATH = 'jsoncards'
DAY = 60*60*24

class DBProxy:

    def __init__(self, jsonUrl: str, databaseDir: str, localUpdateHash: str, cardsUrl: str,
                 urlReplStr: str, DBIDtype: str, rulesURL: str):
        self.httpSession = aiohttp.ClientSession()
        self.jsonUrl = jsonUrl
        self.databaseDir = databaseDir
        self.localUpdateHash = localUpdateHash
        self.remoteUpdateHash = self.jsonUrl + '.sha256'
        self.cardsurl = cardsUrl
        self.urlReplStr = urlReplStr
        self.databaseIdType = DBIDtype
        self.rulesurl = rulesURL

    async def _shouldUpdate(self):
        try:
            with open(self.localUpdateHash) as updateHash:
                onlineHash = await self.httpSession.get(self.remoteUpdateHash)
                if updateHash.read() == await onlineHash.text():
                    return False
                else:
                    return True
        except:
            print("Remote update hash not reached.")

    async def _updateHash(self):
        with open(self.localUpdateHash, 'w') as updateHash:
            onlineHash = await self.httpSession.get(self.remoteUpdateHash)
            updateHash.write(await onlineHash.text())

    async def _fetchDatabase(self, databaseUrl: str):
        try:
            downloadDatabase = await self.httpSession.get(databaseUrl)
            return await downloadDatabase.json()
        except:
            print("JSON dastabase not reached.")

    def _splitUpJsonCards(self, jsonFile):
        jsonCardsSplitUp = []
        jsonCardSets = jsonFile['data']
        for cardSet in jsonCardSets:
            cardSetCards = jsonCardSets[cardSet]['cards']
            for card in cardSetCards:
                jsonCardsSplitUp.append(card)
        return jsonCardsSplitUp

    def _saveDatabase(self, databaseDir, jsonFiles):
        for card in jsonFiles:
            with open(f'{databaseDir}/{JSON_PATH}/{self._simplifyString(card[NAME])}.json', 'w') as jsonCardF:
                json.dump(card, jsonCardF)

    def _compressCardImage(self, cardpath, ext):
        with Image.open(cardpath + "." + ext) as cardfile:
            compressedCard = cardfile.resize((360,500))
            compressedCard.save(cardpath + ".jpg")

    async def _downloadOneCardImage(self, cardName, cardID):
        try:
            wizardsurl = self._makeRemoteImageURL(cardID)
            cardOnline = await self.httpSession.get(wizardsurl)
            cardData = await cardOnline.read()
            cardpath = self.databaseDir + "/" + IMAGE_PATH + "/" + self._simplifyString(cardName)
            ext = filetype.guess(cardData).extension
            with open(cardpath + '.' + ext, 'wb') as cardWrite:
                cardWrite.write(cardData)
            self._compressCardImage(cardpath, ext)
        except:
            print("Failed to download card -- wizards down?")

    async def _downloadCardImages(self, jsonCards):
        existingCards = set(os.listdir(self.databaseDir + '/' + IMAGE_PATH))
        for card in jsonCards:
            if card[NAME] in existingCards:
                continue
            await self._downloadOneCardImage(card[NAME], card['identifiers'][self.databaseIdType])

    async def _updateRules(self, rulesurl):
        rulesOnline = await self.httpSession.get(rulesurl)
        rulesText = await rulesOnline.text()
        with open(self.databaseDir + "/rules", 'w') as rulesfile:
            rulesfile.write(rulesText)

    async def _updateDB(self):
        print("Downloading database...")
        jsonCards = self._splitUpJsonCards(await self._fetchDatabase(self.jsonUrl))
        print("Database downloaded")
        print("Saving database...")
        self._saveDatabase(self.databaseDir, jsonCards)
        print("Database saved")
        print("Downloading card images")
        await self._downloadCardImages(jsonCards)
        print("Card images downloaded")
        await self._updateHash()
        await self._updateRules(self.rulesurl)

    async def loopCheckAndUpdate(self):
        while True:
            if await self._shouldUpdate():
                await self._updateDB()
            await asyncio.sleep(DAY)

    def _simplifyString(self, string):
        return re.sub(r'[\W\s]', '', string).lower()

    def _makeRemoteImageURL(self, cardName):
        return re.sub(self.urlReplStr, urllib.parse.quote(cardName), self.cardsurl)


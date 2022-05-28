
import aiohttp, re, json, filetype, urllib, os, asyncio
from PIL import Image

NAME = 'name'
IMAGE_PATH = 'cardimages'
JSON_PATH = 'jsoncards'
DAY = 60*60*24

class DBProxy:
    '''
        The DataBase Proxy sends requests and receives data from the remote databases that
        hold MtG card data. It also requests and receives data from the Rules database.
        It updates the local database files.
    '''
    def __init__(self, jsonUrl: str, databaseDir: str, localUpdateHash: str, cardsUrl: str,
                 urlReplStr: str, DBIDtype: str, rulesURL: str):
        self.httpSession = aiohttp.ClientSession()
        print("http session online")
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
                    print("Hash found -- database up to date.")
                    return False
                else:
                    print("New hash found -- updating database.")
                    return True
        except:
            print(f"Remote update hash not reached: {self.remoteUpdateHash}")
            return False

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
            with open(f'{databaseDir}/{JSON_PATH}/{self._simplify(card[NAME])}.json', 'w') as jsonCardF:
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
            cardpath = self.databaseDir + "/" + IMAGE_PATH + "/" + self._simplify(cardName)
            ext = filetype.guess(cardData).extension
            with open(cardpath + '.' + ext, 'wb') as cardWrite:
                cardWrite.write(cardData)
            self._compressCardImage(cardpath, ext)
        except:
            print("Failed to download card -- wizards down?")

    async def _downloadCardImages(self, jsonCards):
        print("Downloading cards: ")
        # This strips the file extension from each card file in the database, getting only the card name
        existingCards = set([cardname[:cardname.index('.')] for cardname in
                             os.listdir(self.databaseDir + '/' + IMAGE_PATH)])
        print(self.databaseDir+'/'+IMAGE_PATH)
        cardcount = 0
        numcards = len(jsonCards)
        for card in jsonCards:
            cardcount += 1
            self._cardDownloadMeter(cardcount, numcards)
            if self._simplify(card[NAME]) in existingCards:
                continue
            await self._downloadOneCardImage(card[NAME], card['identifiers'][self.databaseIdType])
        print("Complete")

    def _cardDownloadMeter(self, cardcount, jsoncardlen):
        totalbars = 100
        percent = cardcount / jsoncardlen
        numOfBars = int(percent * totalbars // 1)
        toprint = ' [' + '=' * numOfBars + '.' * (totalbars - numOfBars) + '] ' \
                  + str(cardcount) + '/' + str(jsoncardlen) + ' (' + str(round(percent * 100, 1)) + '%)'
        print(toprint, end="\r")


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
        print("Downloading card images...")
        await self._downloadCardImages(jsonCards)
        print("Card images downloaded")
        await self._updateHash()
        await self._updateRules(self.rulesurl)

    async def loopCheckAndUpdate(self):
        while True:
            if await self._shouldUpdate():
                await self._updateDB()
            await asyncio.sleep(DAY)

    def _simplify(self, string):
        return re.sub(r'[\W\s]', '', string).lower()

    def _makeRemoteImageURL(self, cardName):
        return re.sub(self.urlReplStr, urllib.parse.quote(cardName), self.cardsurl)


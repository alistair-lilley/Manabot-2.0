
import hashlib, json, os, asyncio, filetype, sys, aiohttp, urllib.parse


class DBProxy:

    def __init__(self, jsonUrl: str, databaseDir: str, localUpdateHash: str):
        self.httpSession = aiohttp.ClientSession()
        self.jsonUrl = jsonUrl
        self.databaseDir = databaseDir
        self.localUpdateHash = localUpdateHash
        self.remoteUpdateHash = self.jsonUrl + '.sha256'

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

    async def _updateDB(self):
        if self._shouldUpdate():
            pass

    def _fetchDatabase(self, databaseUrl: str):
        try:
            downloadDatabase = await self.httpSession.get(databaseUrl)
            return await downloadDatabase.json()
        except:
            print("JSON dastabase not reached.")

    def _splitUpJsonCards(self, jsonFile):


    def _saveDatabase(self, databaseDir, jsonFiles):
        pass

    def _downloadCard(self, cardName):
        pass

    async def _loopCheckAndUpdate(self):
        while True:
            if await self._shouldUpdate():
                await self._updateDB()


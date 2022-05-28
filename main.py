import asyncio
from src import DBProxy


async def makeProxy():
    jsonUrl = "https://mtgjson.com/api/v5/AllPrintings.json"
    databaseDir = "/home/akiahala/Programs/src/ManaBot2.0/testdata"
    localUpdateHash = "/home/akiahala/Programs/src/ManaBot2.0/testdata/updatehash"
    cardsURL = "https://api.scryfall.com/cards/#ID#?format=image"
    repl = "#ID#"
    dbidtype = "scryfallId"
    rulesURL = "https://media.wizards.com/2022/downloads/MagicCompRules%2020220429.txt"
    proxy = DBProxy.DBProxy(jsonUrl, databaseDir, localUpdateHash, cardsURL, repl, dbidtype, rulesURL)
    return proxy

async def runUpdate():
    proxy = await makeProxy()
    await proxy._updateDB()
    print("done")

if __name__ == "__main__":
    asyncio.run(runUpdate())
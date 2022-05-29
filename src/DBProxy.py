""" Database Proxy """
import aiohttp
import re
import json
import filetype
import urllib
import os
import asyncio
from PIL import Image
from src.globals import JSON_PATH, IMAGE_PATH
from src.globals import NAME
from src.globals import DAY
from src.globals import simplify
"""
    The object used to retrieve cards, images, and rules from
    remote databases (mtgjson, scryfall, and wotc)
"""


class DBProxy:
    """
        The DataBase Proxy sends requests and receives data from the remote databases that
        hold MtG card data. It also requests and receives data from the Rules database.
        It updates the local database files.
    """
    def __init__(self, json_url, database_dir, local_update_hash, cards_url,
                 url_repl_str, DBIDtype, rules_URL):
        self.http_session = aiohttp.ClientSession()
        print("http session online")
        self.json_url = json_url
        self.database_dir = database_dir
        self.local_update_hash = local_update_hash
        self.remote_update_hash = self.json_url + '.sha256'
        self.cardsurl = cards_url
        self.url_repl_str = url_repl_str
        self.database_id_type = DBIDtype
        self.rulesurl = rules_URL

    async def _should_update(self):
        try:
            with open(self.local_update_hash) as update_hash:
                online_hash = await self.httpSession.get(self.remote_update_hash)
                if update_hash.read() == await online_hash.text():
                    print("Hash found -- database up to date.")
                    return False
                else:
                    print("New hash found -- updating database.")
                    return True
        except:
            print(f"Remote update hash not reached: {self.remote_update_hash}")
            return False

    async def _update_hash(self):
        with open(self.local_update_hash, 'w') as update_hash:
            online_hash = await self.httpSession.get(self.remote_update_hash)
            update_hash.write(await online_hash.text())

    async def _fetch_database(self, database_url):
        try:
            download_database = await self.http_session.get(database_url)
            return await download_database.json()
        except:
            print("JSON dastabase not reached.")

    def _split_up_json_cards(self, json_file):
        json_cards_split_up = []
        json_card_sets = json_file['data']
        for card_set in json_card_sets:
            card_set_cards = json_card_sets[card_set]['cards']
            for card in card_set_cards:
                json_cards_split_up.append(card)
        return json_cards_split_up

    def _save_database(self, database_dir, json_files):
        for card in json_files:
            with open(f'{database_dir}/{JSON_PATH}/{simplify(card[NAME])}.json', 'w') as json_card_f:
                json.dump(card, json_card_f)

    def _compress_card_image(self, cardpath, ext):
        with Image.open(cardpath + "." + ext) as cardfile:
            compressed_card = cardfile.resize((360,500))
            compressed_card.save(cardpath + ".jpg")

    async def _download_one_card_image(self, card_name, cardID):
        try:
            wizardsurl = self._make_remote_image_URL(cardID)
            card_online = await self.http_session.get(wizardsurl)
            card_data = await card_online.read()
            cardpath = self.database_dir + "/" + IMAGE_PATH + "/" + simplify(card_name)
            ext = filetype.guess(card_data).extension
            with open(cardpath + '.' + ext, 'wb') as card_write:
                card_write.write(card_data)
            self._compress_card_image(cardpath, ext)
        except:
            print("Failed to download card -- wizards down?")

    async def _download_card_images(self, json_cards):
        print("Downloading cards: ")
        # This strips the file extension from each card file in the database, getting only the card name
        existing_cards = set([cardname[:cardname.index('.')] for cardname in
                             os.listdir(self.database_dir + '/' + IMAGE_PATH)])
        print(self.database_dir+'/'+IMAGE_PATH)
        cardcount = 0
        numcards = len(json_cards)
        for card in json_cards:
            cardcount += 1
            self._card_download_meter(cardcount, numcards)
            if simplify(card[NAME]) in existing_cards:
                continue
            await self._download_one_card_image(card[NAME], card['identifiers'][self.database_id_type])
        print("Complete")

    def _card_download_meter(self, cardcount, jsoncardlen):
        totalbars = 100
        percent = cardcount / jsoncardlen
        num_of_bars = int(percent * totalbars // 1)
        toprint = ' [' + '=' * num_of_bars + '.' * (totalbars - num_of_bars) + '] ' \
                  + str(cardcount) + '/' + str(jsoncardlen) + ' (' + str(round(percent * 100, 1)) + '%)'
        print(toprint, end="\r")

    async def _update_rules(self, rulesurl):
        rules_online = await self.http_session.get(rulesurl)
        rules_text = await rules_online.text()
        with open(self.database_dir + "/rules", 'w') as rulesfile:
            rulesfile.write(rules_text)

    async def _update_DB(self):
        print("Downloading database...")
        json_cards = self._split_up_json_cards(await self._fetch_database(self.json_url))
        print("Database downloaded")
        print("Saving database...")
        self._save_database(self.database_dir, json_cards)
        print("Database saved")
        print("Downloading card images...")
        await self._download_card_images(json_cards)
        print("Card images downloaded")
        await self._update_hash()
        await self._update_rules(self.rulesurl)

    async def loop_check_and_update(self):
        while True:
            if await self._should_update():
                await self._update_DB()
            await asyncio.sleep(DAY)

    def _make_remote_image_URL(self, card_name):
        return re.sub(self.url_repl_str, urllib.parse.quote(card_name), self.cardsurl)

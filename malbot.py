from discord.ext import commands
from difflib import SequenceMatcher
import asyncio
import xml.etree.cElementTree as ET
import requests
import html
import configparser
import operator


# API Related Info

config = configparser.RawConfigParser()
config.read('config.ini')


bot = commands.Bot(command_prefix="!")
user = config.get('discord', 'user')
password = config.get('discord', 'password')
anime_search_url = 'https://myanimelist.net/api/anime/search.xml?q='
manga_search_url = 'https://myanimelist.net/api/manga/search.xml?q='
anime_page_url = 'https://myanimelist.net/anime/%d/%s'
manga_page_url = 'https://myanimelist.net/manga/%d/%s'

# Markdown Info
bold = '**'
italic = '*'


# Determine similarity between entry title's and the actual searched title
def similar(search_name, result_name):
    return SequenceMatcher(None, search_name.lower(), result_name.lower()).ratio()


@bot.event
@asyncio.coroutine
def on_ready():
    print('Logged in as')
    bot.edit_profile(username="MAL Bot")
    print(bot.user.name)
    print(bot.user.id)
    print('MAL Account:')
    print(user)
    print('-------')


@bot.command()
@asyncio.coroutine
def anime(*name):
    fullname = ""
    for n in name:
        fullname += "{0} ".format(n)
    print("Searching full name: {0}".format(fullname))
    try:
        xml = get_anime_xml(fullname)
        anime_info = ResultInfo(xml)
        yield from bot.say(anime_info.to_string())
    except commands.CommandInvokeError:
        yield from bot.say('Search error')


@bot.command()
@asyncio.coroutine
def manga(*name):
    fullname = ""
    for n in name:
        fullname += "{0} ".format(n)
    print("Searching full name: {0}".format(fullname))
    try:
        xml = get_manga_xml(fullname)
        manga_info = ResultInfo(xml)
        yield from bot.say(manga_info.to_string())
    except commands.CommandInvokeError:
        yield from bot.say("Search error")


@bot.command()
@asyncio.coroutine
def waifu():
    yield from bot.say('You!')


def get_anime_xml(anime_name):
    # Building URL after converting name to lowercase and splitting it up
    url = anime_search_url
    split_name = anime_name.lower().split()
    for word in split_name:
        url += word
        if word != split_name[-1]:
            url += "+"
    print("Searching anime with URL: {0}".format(url))

    # Performing request to API and getting the XML results
    res = requests.get(url, auth=(user, password))
    xml_root = ET.fromstring(res.content)

    # Sorting entries by their likeness to the original search term
    result_list = []
    for entry in xml_root:
        result_list.append((entry, similar(anime_name.lower(), entry[1].text.lower())))

    result_list.sort(key=operator.itemgetter(1))
    result_list.reverse()
    search_result = result_list[0][0]
    return search_result


def get_manga_xml(manga_name):
    # Building URL after converting name to lowercase and splitting it up
    url = manga_search_url
    split_name = manga_name.lower().split()
    for word in split_name:
        url += word
        if word != split_name[-1]:
            url += "+"
    print("Searching manga with URL: {0}".format(url))

    # Performing request to API and getting the XML results
    res = requests.get(url, auth=(user, password))
    xml_root = ET.fromstring(res.content)

    # Sorting entries by their likeness to the original search term
    result_list = []
    for entry in xml_root:
        result_list.append((entry, similar(manga_name.lower(), entry[1].text.lower())))

    result_list.sort(key=operator.itemgetter(1))
    result_list.reverse()
    search_result = result_list[0][0]
    return search_result


# Anime XMl Format:
# id
# title
# english
# synonyms
# episodes
# type
# status
# start_date
# end_date
# synopsis
# image


# Manga XML Format:
# id
# title
# english
# synonyms
# chapters
# volumes
# score
# type
# status
# start_date
# end_date
# synopsis
# image

class ResultInfo:
    replace_dict = {'<br />': ' ',
                    '[i]': italic,
                    '[/i]': italic,
                    '[b]': bold,
                    '[/b]': bold}

    def __init__(self, xml_source):
        self.info = {}
        assert isinstance(xml_source, ET.Element)

        # Parse XML tags to obtain the information for the search result
        for xml_tag in xml_source:
            if xml_tag.text is None:
                self.info[xml_tag.tag] = 'N/A'
            else:
                text = xml_tag.text
                for key, value in self.replace_dict.items():
                    text = text.replace(key, value)
                self.info[xml_tag.tag] = html.unescape(text)

    def to_string(self):
        output = ''
        for k, v in self.info.items():
            output += bold + k + bold + ": " + v + '\n'
        return output


bot.run(config.get('discord', 'access_key'))

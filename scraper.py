URL = "https://unstats.un.org/unsd/methodology/m49/overview/"
COUNTRIES_GITHUB_URL = "https://codeforiati.org/country-codes/country_codes.csv"

from lxml import html
from os import environ, remove, makedirs
environ['SCRAPERWIKI_DATABASE_NAME'] = 'sqlite:///data.sqlite'

import scraperwiki
import requests
import shutil
from os.path import join
from glob import glob
import csv

output_dir = "output"
data_dir = join(output_dir, "data")

HEADERS = ['Global Code', 'Global Name', 'Region Code',
    'Region Name', 'Sub-region Code', 'Sub-region Name',
    'Intermediate Region Code', 'Intermediate Region Name',
    'Country or Area', 'M49 Code', 'ISO-alpha2 Code', 'ISO-alpha3 Code',
    'Least Developed Countries (LDC)', 'Land Locked Developing Countries (LLDC)',
    'Small Island Developing States (SIDS)', 'Developed / Developing Countries']

LANGS = ["ZH", "RU", "FR", "ES", "AR"]

LANG_COLS = ['Global Name', 'Region Name', 'Sub-region Name',
    'Intermediate Region Name', 'Country or Area']

def get_countries_data():
    print("Getting countries data...")
    r = requests.get(COUNTRIES_GITHUB_URL)
    data = list(csv.DictReader(r.iter_lines(decode_unicode=True)))
    return dict(map(lambda c: (c['code_3_digit'], c), data))

def get_page():
    r = requests.get(URL)
    return html.fromstring(r.text)

def run():
    print("Starting up...")
    countries_data = get_countries_data()
    print("Got countries data.")
    print("Getting UN M49 data.")
    page = get_page()

    bigdata = {}
    # Go through the EN table to get all basic data + EN data
    print("Getting basic data and EN data.")
    table = page.xpath("//table[@id='downloadTableEN']")[0]
    for row in table.xpath("tbody/tr"):
        cols = row.xpath("td")
        data = {}
        for i, header in enumerate(HEADERS):
            if i in [12, 13, 14]:
                if cols[i].find('i') is not None:
                    data[header] = True
                else:
                    data[header] = False
            elif i in [15]:
                if cols[i].find('code') is not None:
                    data[header] = cols[i].find('code').text
            else:
                data[header] = cols[i].text
        bigdata[data['M49 Code']] = data
    # Parse the language-dependent columns again for each language
    for lang in LANGS:
        print("Getting data for {} language".format(lang))
        table = page.xpath("//table[@id='downloadTable{}']".format(lang))[0]
        for row in table.xpath("tbody/tr"):
            cols = row.xpath("td")
            M49_CODE = cols[HEADERS.index('M49 Code')].text
            for lang_col in LANG_COLS:
                bigdata[M49_CODE].update({'{}_{}'.format(lang_col, lang): cols[HEADERS.index(lang_col)].text })
    # Save everything
    print("Saving data...")

    makedirs("output", exist_ok=True)
    with open(join("output", "country_region_codes.csv"), 'w') as csv_f:
        csvwriter = csv.DictWriter(csv_f, fieldnames=bigdata.values()[0].keys())
        csvwriter.writeheader()
        for bd in bigdata.values():
            country_data = countries_data.get(bd['ISO-alpha3 Code'])
            if country_data:
                bd['ISO-alpha2 Code'] = country_data['code']

            csvwriter.writerow(bd)
            if environ.get("GITHUB_PAGES", False) is False:
                scraperwiki.sqlite.save(unique_keys=['M49 Code'], data=bd)
    print("Done.")

run()

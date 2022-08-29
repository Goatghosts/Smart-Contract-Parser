import json
import traceback
import logging
import time
import re
import os

import requests
from selectolax.parser import HTMLParser

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")


BLOCKCHAINS = {
    "BSC": {
        "url": "https://bscscan.com",
    },
    "ETHER": {
        "url": "https://etherscan.io",
    },
    "POLYGON": {
        "url": "https://polygonscan.com",
    },
    "MOON": {
        "url": "https://moonscan.io",
    },
    "ARBI": {
        "url": "https://arbiscan.io",
    },
}

# Create dirs
MAIN_DIR = "./contracts"
if not os.path.exists(MAIN_DIR):
    os.mkdir(MAIN_DIR)
for blockchain in BLOCKCHAINS:
    if not os.path.exists(f"{MAIN_DIR}/{blockchain}"):
        os.mkdir(f"{MAIN_DIR}/{blockchain}")

CLEANER = re.compile(r"[^0-9/.]+")


def get_headers(blockchain: str) -> dict:
    referer = BLOCKCHAINS[blockchain]["url"]
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": f"{referer}/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    }


def get_page(url: str, blockchain: str) -> str:
    response = ""
    try:
        headers = get_headers(blockchain)
        response = requests.get(url, headers=headers).text
    except Exception as e:
        print(traceback.format_exc())
        logging.error(f"Filed to get page {url} for {blockchain} blockchain")
        print(e)
        time.sleep(10)

    return response


def parse_contract_abi(tree: HTMLParser) -> str:
    try:
        abi = tree.css_first("pre.wordwrap.js-copytextarea2")
        if abi:
            return json.loads(abi.text().strip())
    except Exception as e:
        print(traceback.format_exc())
        logging.error("Can't parse contract abi")
        print(e)
    return None


def parse_contract_code_files(tree: HTMLParser) -> dict:
    files = {}
    try:
        code_block = tree.css_first("div#dividcode")
        for i, code in enumerate(code_block.css("pre.editor")):
            filename = f"code_{i+1}.sol"
            files[filename] = code.text().strip()
    except Exception as e:
        print(traceback.format_exc())
        logging.error("Can't parse contract code files")
        print(e)
    return files


def parse_contract_data(blockchain: str, tree: HTMLParser) -> dict:
    data = {
        "tokens_balance": 0.0,
        "tokens_count": 0,
    }
    try:
        info_block = tree.css_first("div.row.mb-4")
        rows = info_block.css("div.row.align-items-center")
        for row in rows:
            tokens_balance = row.css_first("a#availableBalanceDropdown")
            if tokens_balance:
                data["tokens_balance"] = float(CLEANER.sub("", tokens_balance.text(deep=False).strip()))
                tokens_count = row.css_first("span")
                if tokens_count:
                    data["tokens_count"] = int(CLEANER.sub("", tokens_count.text(deep=False).strip()))
            creator_address = row.css_first('a[title="Creator Address"]')
            if creator_address:
                data["creator_address_url"] = BLOCKCHAINS[blockchain]["url"] + creator_address.attributes["href"]
                creator_txn = row.css_first('a[title="Creator Txn Hash"]')
                if creator_txn:
                    data["creator_txn_url"] = BLOCKCHAINS[blockchain]["url"] + creator_txn.attributes["href"]
            token = row.css_first('a[title$="Token Tracker Page"]')
            if token:
                data["token_url"] = BLOCKCHAINS[blockchain]["url"] + token.attributes["href"]
    except Exception as e:
        print(traceback.format_exc())
        logging.error("Can't parse contract data")
        print(e)
    return data


def get_contracts(blockchain: str, all_pages: bool = True) -> dict:
    contracts = {}
    last_page = 6 if all_pages else 2
    url = BLOCKCHAINS[blockchain]["url"]
    for page in range(1, last_page):
        try:
            html = get_page(f"{url}/contractsVerified/{page}?ps=100", blockchain)
            tree = HTMLParser(html)
            table_body = tree.css_first("tbody")
            rows = table_body.css("tr")
            for row in rows:
                try:
                    cols = row.css("td")
                    address = cols[0].text().strip()
                    balance, currency = cols[4].text().split()
                    contracts[address] = {
                        "blockchain": blockchain,
                        "address": address,
                        "url": f"{url}/address/{address}#code",
                        "name": cols[1].text().strip(),
                        "compiler": cols[2].text().strip(),
                        "version": cols[3].text().strip(),
                        "balance": float(balance.strip()),
                        "currency": currency.strip(),
                        "transactions": int(cols[5].text().strip()),
                        "verified": cols[7].text().strip(),
                        "license": cols[9].text().strip(),
                    }
                except:
                    continue
        except:
            continue
    return contracts


def get_contract_data(table_data: dict):
    try:
        tree = HTMLParser(get_page(table_data["url"], table_data["blockchain"]))
        contract_data = parse_contract_data(table_data["blockchain"], tree)
        contract_data.update(table_data)
        contract_code_files = parse_contract_code_files(tree)
        contract_abi = parse_contract_abi(tree)
        return contract_data, contract_code_files, contract_abi
    except Exception as e:
        print(traceback.format_exc())
        logging.error("Can't get contract data")
        print(e)
        return None, None, None


def test():
    test_urls = [
        "https://bscscan.com/address/0xeca88125a5adbe82614ffc12d0db554e2e2867c8#code",  # 4 files, have tracker
        "https://bscscan.com/address/0x0879dB3A4c289b7e3DFbdbB8Eb9494b2fDd31941#code",  # 7 files, not have tracker
        "https://bscscan.com/address/0xa9A4B9D7A192E75bE989Ce5D5F824Ae98Eab93f9#code",  # 1 file, have tracker
        "https://bscscan.com/address/0x8fa73c986fe6a76fecfd878090cba9bcd5687b4e#code",  # 1 file, not have tracker
    ]
    for url in test_urls:
        table_data = {
            "name": "test",
            "blockchain": "BSC",
            "url": url,
        }
        get_contract_data(table_data)


def main():
    while True:
        for blockchain in BLOCKCHAINS:
            contracts = get_contracts(blockchain, True)
            for address, table_data in contracts.items():
                logging.info(f"Parse [{blockchain}] address: {address}")
                path = f"{MAIN_DIR}/{blockchain}/{address}"
                if not os.path.exists(path) or not os.path.exists(f"{path}/abi.json"):
                    os.mkdir(path)
                    data, code_files, abi = get_contract_data(table_data)
                    if abi is None:
                        continue
                    # Write contract info
                    with open(f"{path}/info.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    # Write contract source code
                    for filename, code in code_files.items():
                        with open(f"{path}/{filename}", "w", encoding="utf-8") as f:
                            f.write(code)
                    # Write contract abi
                    with open(f"{path}/abi.json", "w", encoding="utf-8") as f:
                        json.dump(abi, f, indent=2)
                    time.sleep(1)
        time.sleep(600)


if __name__ == "__main__":
    main()

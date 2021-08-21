#!/usr/bin/env python3

# Author: Racterub (root@racterub.me)
# Licencse: MIT

from config import TOKEN
from aiogram import Bot, Dispatcher, types, executor
from json import loads
from time import time
from math import floor, log10
import httpx
import websockets
import zlib
"""
Bot Setup
"""
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


"""
Utility functions
"""
def process_digit(data):
    bases = ['',' K',' M',' B',' T']
    values = []
    for i in data:
        n = float(i["openInterest"])
        base = max(0, min(len(bases)-1, int(floor(0 if n == 0 else log10(abs(n))/3))))
        values.append(f"{round(n / 10**(3 * base), 3)}{bases[base]}")
    return values

async def getlatestoi():
    uri = "wss://ws.bybt.com:666/ws"
    async with websockets.connect(uri) as websocket:

        await websocket.send('{"method":"subscribe","params":[{"t":"h1","key":"BTC:Binance:1:USDT","channel":"openInterestKline"}]}')
        resp = await websocket.recv()
        btc_data = loads(zlib.decompress(resp, 16+zlib.MAX_WBITS))["data"]
        btc = process_digit([btc_data])[0]
        
        
        await websocket.send('{"method":"subscribe","params":[{"t":"h1","key":"ETH:Binance:1:USDT","channel":"openInterestKline"}]}')
        resp = await websocket.recv()
        eth_data = loads(zlib.decompress(resp, 16+zlib.MAX_WBITS))["data"]
        eth = process_digit([eth_data])[0]

        return btc, eth

async def getlatestlsur():
    uri = "wss://ws.bybt.com:666/ws"
    async with websockets.connect(uri) as websocket:

        await websocket.send('{"method":"subscribe","params":[{"t":"h1","key":"BTC:Binance:1:USDT","channel":"globalAccountsLSRatio"}]}')
        resp = await websocket.recv()
        btc_data = loads(zlib.decompress(resp, 16+zlib.MAX_WBITS))["data"]
        btc = btc_data["longShortRatio"]
        
        await websocket.send('{"method":"subscribe","params":[{"t":"h1","key":"ETH:Binance:1:USDT","channel":"globalAccountsLSRatio"}]}')
        resp = await websocket.recv()
        eth_data = loads(zlib.decompress(resp, 16+zlib.MAX_WBITS))["data"]
        eth = eth_data["longShortRatio"]

        return btc, eth


@dp.message_handler(commands=["start", "help"])
async def help_command(message: types.Message):
    await bot.delete_message(message.chat.id, message.message_id)
    await bot.send_message(message.chat.id, """
BYBT Bot

指令:
/fundingfee - 資金費率
/longshortratio - 多空比
/openinterest - 持倉
/uptrendrank - 漲幅榜
/downtrendrank - 跌幅榜
/help - 顯示此教學""")


@dp.message_handler(commands=["fundingfee"])
async def fundingfee_command(message: types.Message):
    async with httpx.AsyncClient() as client:
        res = await client.get("https://fapi.bybt.com/api/fundingRate/v2/home")
    resource = res.json()["data"]
    btc = {i["exchangeName"]:i["rate"] for i in resource[0]["uMarginList"]}
    eth = {i["exchangeName"]:i["rate"] for i in resource[1]["uMarginList"]}
    resp = f"""BYBT 資金費率:
BTC:
    Huobi: {btc["Huobi"]}
    Binance: {btc["Binance"]}
    Okex: {btc["Okex"]}
    FTX: {btc["FTX"]}
    Bybit: {btc["Bybit"]}
ETH:
    Huobi: {eth["Huobi"]}
    Binance: {eth["Binance"]}
    Okex: {eth["Okex"]}
    FTX: {eth["FTX"]}
    Bybit: {eth["Bybit"]}

資料來源: https://www.bybt.com/zh-tw/FundingRate"""
    await bot.delete_message(message.chat.id, message.message_id)
    await bot.send_message(message.chat.id, resp)


@dp.message_handler(commands=["openinterest"])
async def openinterest(message: types.Message):
    start_time = int((time() - 60 * 4 - 1) * 1000)
    end_time = int((time() - 1) * 1000 )
    async with httpx.AsyncClient() as client:
        btc_raw = await client.get(f"https://fapi.bybt.com/api/openInterest/kline?exName=Binance&pair=BTCUSDT&interval=h1&type=undefined&startTime={start_time}&endTime={end_time}")
        eth_raw = await client.get(f"https://fapi.bybt.com/api/openInterest/kline?exName=Binance&pair=ETHUSDT&interval=h1&type=undefined&startTime={start_time}&endTime={end_time}")
    btc_resource = btc_raw.json()["data"]
    eth_resource = eth_raw.json()["data"]
    btc_oi_data = process_digit(btc_resource[-5:-1])
    eth_oi_data = process_digit(eth_resource[-5:-1])
    btc, eth = await getlatestoi()
    resp = f"""BYBT 持倉數據(近4小時)
BTC:
    {btc_oi_data[0]} - {btc_oi_data[1]} - {btc_oi_data[2]} - {btc}
ETH:
    {eth_oi_data[0]} - {eth_oi_data[1]} - {eth_oi_data[2]} - {eth}

資料來源: https://www.bybt.com/"""
    await bot.delete_message(message.chat.id, message.message_id)
    await bot.send_message(message.chat.id, resp)

@dp.message_handler(commands=["longshortratio"])
async def longshortratio_command(message: types.Message):
    async with httpx.AsyncClient() as client:
        btc_resource_raw = await client.get("https://fapi.bybt.com/api/futures/longShortRate?timeType=2&symbol=BTC")
        btc_chart_raw = await client.get("https://fapi.bybt.com/api/futures/longShortChart?symbol=BTC&timeType=2")
        btc_kline_raw = await client.get("https://fapi.bybt.com/api/tradingData/kline?exName=Binance&pair=BTCUSDT&interval=h1&type=3&endTime=")
        eth_resource_raw = await client.get("https://fapi.bybt.com/api/futures/longShortRate?timeType=2&symbol=ETH")
        eth_chart_raw = await client.get("https://fapi.bybt.com/api/futures/longShortChart?symbol=ETH&timeType=2")
        eth_kline_raw = await client.get("https://fapi.bybt.com/api/tradingData/kline?exName=Binance&pair=ETHUSDT&interval=h1&type=3&endTime=")
    binance_btc, binance_eth = await getlatestlsur()
    btc_resource = btc_resource_raw.json()["data"][0]
    btc_chart = btc_chart_raw.json()["data"]
    btc_kline = btc_kline_raw.json()["data"][-4:]
    eth_resource = eth_resource_raw.json()["data"][0]
    eth_chart = eth_chart_raw.json()["data"]
    eth_kline = eth_kline_raw.json()["data"][-4:]
    btc = {i["exchangeName"]:[i["longRate"], i["shortRate"]] for i in btc_resource["list"]}
    btc["All"] = [btc_resource["longRate"], btc_resource["shortRate"]]
    eth = {i["exchangeName"]:[i["longRate"], i["shortRate"]] for i in eth_resource["list"]}
    eth["All"] = [eth_resource["longRate"], eth_resource["shortRate"]]
    resp = f"""BYBT 多空比 (1小時距):
(近4小時多空比)
BTC:
    {btc_chart["longShortRateList"][-4]} - {btc_chart["longShortRateList"][-3]} - {btc_chart["longShortRateList"][-2]} - {btc_chart["longShortRateList"][-1]}
ETH:
    {eth_chart["longShortRateList"][-4]} - {eth_chart["longShortRateList"][-3]} - {eth_chart["longShortRateList"][-2]} - {eth_chart["longShortRateList"][-1]}
---
(交易所多空比)
BTC:
    Huobi: {btc["Huobi"][0]}% / {btc["Huobi"][1]}% - {round(btc["Huobi"][0]/btc["Huobi"][1], 3)}
    Binance: {btc["Binance"][0]}% / {btc["Binance"][1]} - {round(btc["Binance"][0]/btc["Binance"][1], 3)}
    Okex: {btc["Okex"][0]}% / {btc["Okex"][1]}% - {round(btc["Okex"][0]/btc["Okex"][1], 3)}
    FTX: {btc["FTX"][0]}% / {btc["FTX"][1]}% - {round(btc["FTX"][0]/btc["FTX"][1], 3)}
    Bybit: {btc["Bybit"][0]}% / {btc["Bybit"][1]}% - {round(btc["Bybit"][0]/btc["Bybit"][1], 3)}
    全網： {btc["All"][0]}% / {btc["All"][1]}% - {round(btc["All"][0]/btc["All"][1], 3)}
ETH:
    Huobi: {eth["Huobi"][0]}% / {eth["Huobi"][1]}% - {round(eth["Huobi"][0]/eth["Huobi"][1], 3)}
    Binance: {eth["Binance"][0]}% / {eth["Binance"][1]}% - {round(eth["Binance"][0]/eth["Binance"][1], 3)}
    Okex: {eth["Okex"][0]}% / {eth["Okex"][1]}% - {round(eth["Okex"][0]/eth["Okex"][1], 3)}
    FTX: {eth["FTX"][0]}% / {eth["FTX"][1]}% - {round(eth["FTX"][0]/eth["FTX"][1], 3)}
    Bybit: {eth["Bybit"][0]}% / {eth["Bybit"][1]}% - {round(eth["Bybit"][0]/eth["Bybit"][1], 3)}
    全網： {eth["All"][0]}% / {eth["All"][1]}% - {round(eth["All"][0]/eth["All"][1], 3)}
---
Binance k線圖 近四小時多空比(LSUR)
BTC: {btc_kline[0]["longShortRatio"]} - {btc_kline[1]["longShortRatio"]} - {btc_kline[2]["longShortRatio"]} - {binance_btc}
ETH: {eth_kline[0]["longShortRatio"]} - {eth_kline[1]["longShortRatio"]} - {eth_kline[2]["longShortRatio"]} - {binance_eth}

資料來源: https://www.bybt.com/zh-tw/LongShortRatio"""
    await bot.delete_message(message.chat.id, message.message_id)
    await bot.send_message(message.chat.id, resp)



@dp.message_handler(commands=["uptrendrank"])
async def uptrendrank_command(message: types.Message):
    async with httpx.AsyncClient() as client:
        res = await client.get('https://fapi.bybt.com/api/futures/coins/priceChange')
    resource = res.json()["data"]
    rank = [[i["symbol"], {"change": i["h24PriceChangePercent"], "price": i["price"] }] for i in sorted(resource, key=lambda x:x["h24PriceChangePercent"], reverse=True)[:5]]
    resp = f"""BYBT 漲幅榜:
1. {rank[0][0]} - 24h漲幅: {rank[0][1]["change"]}%, 現價: {rank[0][1]["price"]}
2. {rank[1][0]} - 24h漲幅: {rank[1][1]["change"]}%, 現價: {rank[1][1]["price"]}
3. {rank[2][0]} - 24h漲幅: {rank[2][1]["change"]}%, 現價: {rank[2][1]["price"]}
4. {rank[3][0]} - 24h漲幅: {rank[3][1]["change"]}%, 現價: {rank[3][1]["price"]}
5. {rank[4][0]} - 24h漲幅: {rank[4][1]["change"]}%, 現價: {rank[4][1]["price"]}

資料來源: https://www.bybt.com/zh-tw/gainers-losers"""
    await bot.delete_message(message.chat.id, message.message_id)
    await bot.send_message(message.chat.id, resp)

@dp.message_handler(commands=["downtrendrank"])
async def downtrendrank_command(message: types.Message):
    async with httpx.AsyncClient() as client:
        res = await client.get('https://fapi.bybt.com/api/futures/coins/priceChange')
    resource = res.json()["data"]
    rank = [[i["symbol"], {"change": i["h24PriceChangePercent"], "price": i["price"] }] for i in sorted(resource, key=lambda x:x["h24PriceChangePercent"])[:5]]
    resp = f"""BYBT 漲幅榜:
1. {rank[0][0]} - 24h漲幅: {rank[0][1]["change"]}%, 現價: {rank[0][1]["price"]}
2. {rank[1][0]} - 24h漲幅: {rank[1][1]["change"]}%, 現價: {rank[1][1]["price"]}
3. {rank[2][0]} - 24h漲幅: {rank[2][1]["change"]}%, 現價: {rank[2][1]["price"]}
4. {rank[3][0]} - 24h漲幅: {rank[3][1]["change"]}%, 現價: {rank[3][1]["price"]}
5. {rank[4][0]} - 24h漲幅: {rank[4][1]["change"]}%, 現價: {rank[4][1]["price"]}

資料來源: https://www.bybt.com/zh-tw/gainers-losers"""
    await bot.delete_message(message.chat.id, message.message_id)
    await bot.send_message(message.chat.id, resp)

@dp.message_handler(commands=["about"])
async def about_command(message: types.Message):
    resp = f"""
BYBT Bot

- Source Code
https://github.com/racterub/bybtbot

- Report a issue
    - https://github.com/racterub/bybtbot/issues (Github Issue)
    - @racterub (PM me :p)

- Version
v1.0.2"""
    await bot.delete_message(message.chat.id, message.message_id)
    await bot.send_message(message.chat.id, resp)


if __name__=='__main__':
    executor.start_polling(dp, skip_updates=True)

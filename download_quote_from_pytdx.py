from pytdx.exhq import TdxExHq_API
from pytdx.params import TDXParams

api = TdxExHq_API()

with api.connect('180.153.18.176', 7721):
    markets = api.get_markets()
    for market in markets:
        print(market)
    
    for cursor in range(0, 100000, 1000):
        instrument_info = api.get_instrument_info(cursor, 1000)
        for instrument in instrument_info:
            if instrument["market"] == 30:
                print(instrument)

    # for cursor in range(0, 100000, 1000):
    #     print(f"cursor: {cursor}")
    #     instrument_info = api.get_instrument_info(cursor, 1000)
    #     # 打印数量
    #     print(f"instrument_info count: {len(instrument_info)}")
    #     markets = set([instrument["market"] for instrument in instrument_info])
    #     print(markets)

    # instrument_info = api.get_instrument_info(0, 30000)
    # # OrderedDict({'category': 0, 'market': 0, 'code': '00303', 'name': 'VTECH HOLDINGS', 'desc': ''})
    # # 打印其中包含的所有的market
    # markets = set([instrument["market"] for instrument in instrument_info])
    # print(markets)

    # for instrument in instrument_info:
    #     print(instrument)
    # for instrument in instrument_info:
    #     if instrument["market"] == 30:
    #         print(instrument)

    # instrument_count = api.get_instrument_count()
    # print(instrument_count)

    # bars = api.get_instrument_bars(TDXParams.KLINE_TYPE_DAILY, 47, "IF300", 0, 100)
    # print(bars)
    # quote = api.get_instrument_quote(47, "IF1709")
    # print(quote)
    # history_minute_time_data = api.get_history_minute_time_data(31, "00020", 20170811)
    # print(history_minute_time_data)

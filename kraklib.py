#!/usr/bin/env python3
# Simple Kraken operations

import krakenex
import time
import sys, getopt
from prettytable import *
from datetime import datetime,timedelta

import json
import argparse
 
sleepinterval = 8
k = krakenex.API()
k.load_key('kraken.key')
a = list()
dbdict = {}


def coin_to_pair(coin):
    return coin + 'ZEUR'

def pair_to_coin(pair):
    if (pair.endswith("ZEUR")):
        return pair.replace("ZEUR","")
    else:
        return pair.replace("EUR","")

def place_order(query):
    if not query:
        query = { 'pair': 'XXRPZEUR',
                  'type': 'sell',
                  'ordertype': 'limit',
                  'price': '1.5',
                  'volume': '30'
                }
    print("Will place order %s " % str(query))
    result = k.query_private('AddOrder', query)
    return result


def calculate_fees(trades):

    real_sum = {}
    for trade in trades:
        pair = trades[trade]['pair']
        try:
            real_sum[pair] += float(trades[trade]['fee'])
        except:
            real_sum[pair] = float(trades[trade]['fee'])
    return real_sum

def calculate_price(trades):

    real_sum = {}
    real_vol = {}
    for trade in trades:
        pair = trades[trade]['pair']
        calc = float(trades[trade]['price']) * float(trades[trade]['vol'])
        if trades[trade]['type'] == 'buy':
            calc = (-1) * calc
        try:
            real_sum[pair] += calc
        except:
            real_sum[pair] = calc

    for trade in trades:
        pair = trades[trade]['pair']
        calc = float(trades[trade]['vol'])
        if trades[trade]['type'] == 'buy':
            calc = (-1) * calc
        try:
            real_vol[pair] += calc
        except:
            real_vol[pair] = calc

    return (real_vol, real_sum)

def aggregate(trades):
    real_sum = {}
    for trade in trades:
        pair = trades[trade]['pair']
        typeof = trades[trade]['type']
        price = float(trades[trade]['price'])
        vol = float(trades[trade]['vol'])
        calc = price * vol
        if typeof == 'buy':
            calc = (-1) * calc
        try:
            real_sum[pair][typeof] += vol
        except:
            try:
                real_sum[pair][typeof] = vol
            except:
                real_sum[pair] = {}
                real_sum[pair][typeof] = vol
        try:
            real_sum[pair]['balance'] += calc
        except:
            real_sum[pair]['balance'] = calc

    return real_sum

def get_balance(query):
    result = k.query_private('Balance', query)
    return result

def cancel_order(query):
    print("Will Cancel order %s " % query['txid'])
    result = k.query_private('CancelOrder', query)
    return result

def tradehistory(query):
    result = k.query_private('TradesHistory', query);
    return result


def open_orders(query):
    result = k.query_private('OpenOrders', query)
    return result

def ticker(query):
    if not query:
        query = {'pair': 'XETHZEUR, XXBTZEUR, XREPZEUR,'
                          'BCHEUR, XZECZEUR, DASHEUR, XXRPZEUR, '
                          'XXMRZEUR, XETCZEUR, XLTCZEUR'}
    result = k.query_public('Ticker', query )
    return result

def analysis(tick):
    #print("COIN\tLAST\tAVG (DAY)\tTOTAL EURO SPENT (DAY)")
    mydict = list()
    for coin in tick:
        row = {}
        coindata = tick[coin]
        last = coindata['c']
        volume = coindata['v']
        low = coindata['l']
        high = coindata['h']
        avg = (float(high[1]) + float(low[1])) / 2
        toteuro = float(volume [0]) * (float(high[1]) + float(low[1])) / 2
        toteurom = toteuro / 1000000
        if int(toteuro / 1000000) > 0:
            toteuro = toteurom
            sign = 'm'
        else:
            toteuro = int(toteuro / 1000)
            sign = 'k'
        row['last'] = last[0]
        row['avg'] = avg
        row['toteuro'] = str(int(toteuro)) + sign
        row['coin'] = coin
        row['low'] = float(low[1])
        row['high'] = float(high[1])
        temp = (- avg + float(last[0]))/ float(last[0]) * 100
        row['pct'] = trunc(temp,3)
        mydict.append(row)
    return (mydict, ['coin', 'last', 'avg', 'toteuro', 'low', 'high', 'pct'])

def recommend():
    #Get ticker data
    query = {}
    res = run_func(ticker, query)
    tick = res['result']
    (mydict, row) = analysis(tick)

    # Get Balance
    res = run_func(get_balance, query)
    balance = res['result']

    # Find coins that could be potentially sold
    mylist = list()
    for item in mydict:
        coin = pair_to_coin(item['coin'])
        pct =item['pct']
        for i in balance:
            if i == coin and float(balance[i]) > 0.1:
                mylist.append((i,pct))
    mylist.sort(key=lambda tup: tup[1])

    # Get trade history data
    query = {'start':datetime.timestamp(datetime.now() - timedelta(days=int(20)))}
    res = run_func(tradehistory, query)
    trades = res['result']['trades']

    # calculate net spent per coin
    fees = calculate_fees(trades)
    (vol, spent) = calculate_price(trades)
    total = {}
    for item in fees:
        total[item] = spent[item] - fees[item]
    potsell = {}
    pricepercoin = {}
    for item in mydict:
        pair = item['coin']
        coin = pair_to_coin(pair)
        for x in balance:
            if coin == x:
                calc = float(balance[x]) * float(item['last']) 
                if calc > 1:
                    potsell[pair] = trunc(calc,3)
                
    # calculate difference in unit prices based on stats
    (mycoin, pct) = mylist[-1]
    listdict = {}
    for coin, pct in mylist:
        listdict[coin] = pct
    print_dict(listdict, ['coin', '% changed (last - avg) / last'])
        
    # calculate if selling of selected coins is profitable
    diff = {}
    diffpercoin = {}
    for item in mydict:
        pair = item['coin']
        if (pair in potsell) and (pair in spent):
            diff[pair] = trunc(potsell[pair] + spent[pair], 3)
            pricepercoin[pair] = trunc(spent[pair] / vol[pair],3)
            diffpercoin[pair] = trunc(-(pricepercoin[pair] - float(item['last'])),3)
    print_dict(pricepercoin,['coin', 'Unit Price Bought'])
    print_dict(diffpercoin, ['coin','Difference from last price'])
    print_dict(diff, ['coin','Diff in €'])
    print_dict(potsell, ['coin','Sell price in € (based on last price)'])

    # calculate potential total
    aggr = {}
    sum1 = 0
    for item in potsell:
        calc = potsell[item]
        sum1+=calc
    # account for fees
    key = str(trunc(sum1,3))
    aggr[key] = trunc((sum1 - 0.0026 * sum1),3)
    print_dict(aggr, ['Sub-total', 'Fees included'])

    total = {}
    # add current EUR balance
    total['total'] = trunc((float(balance['ZEUR']) + aggr[key]),3)
    print_dict(total, ['', 'Provisional total in €'])


def run_func(func, arg):
    retries = 0
    while True:
        try:
            result = func(arg)
            if result['error'] == []:
                break
            else:
                print(result['error'])
            if (retries > 10):
                print("Maximum retries exceeded")
                break
        except Exception as inst:
            print ("Got error response: %d" % inst.response.status_code) 
            retries = retries + 1;
        print("Will sleep for %d seconds" % sleepinterval)
        time.sleep(sleepinterval)
    return result

def printTable(myDict, colList=None):
        """ Pretty print a list of dictionaries (myDict) as a dynamically sized table.
        If column names (colList) aren't specified, they will show in random order.
        Author: Thierry Husson - Use it as you want but don't blame me.
        """
        if not colList: colList = list(myDict[0].keys() if myDict else [])
        myList = [colList] # 1st row = header
        for item in myDict: myList.append([str(item[col] or '') for col in colList])
        colSize = [max(map(len,col)) for col in zip(*myList)]
        formatStr = ' | '.join(["{{:<{}}}".format(i) for i in colSize])
        myList.insert(1, ['-' * i for i in colSize]) # Seperating line
        for item in myList: print(formatStr.format(*item))


def print_dict(dicttoprint, row=['key','value']):
        t = PrettyTable(row)
        for key, val in dicttoprint.items():
            #if (isinstance(val, dict)):
            #    vallist = list()
            #    for key1,val1 in val.items():
            #       vallist.append([key1,val1]) 
            #    t.add_row([key, vallist])
            #else:
                t.add_row([key, val])
        print(t)


def trunc(string,dec_to_trunc=3):
    return int(float(string) * 10**dec_to_trunc) / (10**dec_to_trunc)

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dbfile', help='DataBase file',required=False)
    parser.add_argument('-s','--stats', help='Show stats',required=False,action='store_true')
    parser.add_argument('-c','--cancel', help='Cancel Order <txid>',required=False)
    parser.add_argument('-o','--open', help='Open Orders ',required=False, action='store_true')
    parser.add_argument('-p','--place', help="Place Order ex: -p { 'pair': 'XXRPZEUR', 'type': 'sell', 'ordertype': 'limit', 'price': '1.5', 'volume': '30' } ",required=False)
    parser.add_argument('-b','--balance', help='Place Order ',required=False, action='store_true')
    parser.add_argument('-t','--history', help='Trade History ex: -t 2 (show last 2 days)',required=False)
    parser.add_argument('-f','--fees', help='show total fees paid)',required=False, action='store_true')
    parser.add_argument('-a','--aggregate', help='show aggregate stats per coin)',required=False, action='store_true')
    parser.add_argument('-r','--rec', help='show recommendation',required=False, action='store_true')
    args = parser.parse_args()
    if not args.dbfile:
        args.dbfile = "dbfile.json"

    
    query = {}
    #print ("Input file: %s" % args.dbfile)
    if args.stats:
        res = run_func(ticker, query)
        #print("Last price")
        tick = res['result']
        (mydict, row) = analysis(tick)
        printTable(mydict, row)
    elif args.cancel:
        query = { 'txid': args.cancel }
        res = run_func(cancel_order, query)
        print_dict(res['result'])
    elif args.open:
        query = { }
        myownlist = list()
        res = run_func(open_orders, query)
        #print_dict(res['result']['open'])
        openord = res['result']['open']
        for i in openord:
            vol = openord[i]['vol']
            item = openord[i]['descr']
            del item['price2']
            del item['leverage']
            del item['order']
            item['id'] = i
            item['vol'] = trunc(vol,3)
            myownlist.append(openord[i]['descr'])
        printTable(myownlist, ['id','type','ordertype','pair','price', 'vol'])

    elif args.place:
        query = eval(args.place)
        #res = run_func(place_order, query)
        exit = 0
        res = {}
        while (1):
            try:
                res = place_order(query)
                if res['error'] != []:
                    break
            except:
                print("got an exception")
                ores = run_func(open_orders, {})
                oorders = ores['result']['open']
                for item in oorders:
                    row = oorders[item]['descr']
                    if row['type'] == query['type'] and float(oorders[item]['vol']) == float(query['volume']) and float(row['price']) == float(query['price']):
                        print("order already placed, will not continue, orderid: %s " % item)
                        res['result'] = row
                        exit = 1
                        break
                if exit == 0:
                    print("will retry")
                else:
                    break
        print_dict(res['result'])
    elif args.balance:
        query = {}
        res = run_func(get_balance, query)
        print_dict(res['result'])
    elif args.history:
        query = {'start':datetime.timestamp(datetime.now() - timedelta(days=int(args.history)))}
        res = run_func(tradehistory, query)
        myList=list()
        myDict = {}
        for a,b in res['result']['trades'].items():
            row = {}
            row['id'] = a
            for c,d in b.items():
                row[c] = d
            del row['margin']
            row['fee' ] = trunc(row['fee'], 5)
            row['price'] = trunc(row['price'])
            row['cost'] = trunc(row['cost'])
            row['vol'] = float(row['vol'])
            row['time'] = "{:%Y-%m-%d.%H:%M}".format(datetime.fromtimestamp(row['time']))
            if row['ordertxid'] in myDict:
                ptr = myDict[row['ordertxid']]
                ptr['vol'] += row['vol']
                ptr['cost'] += row['cost']
                ptr['fee'] += row['fee']
            else:
                myDict[row['ordertxid']] = row
        for it in myDict:
            row = myDict[it]
            row['id'] = it
            myList.append(row)

        printTable(myList, ['id', 'type', 'pair','price', 'vol', 'fee', 'time','ordertype'])
        #print_dict(res['result']['trades'])
    elif args.fees:
        query = {}
        res = run_func(tradehistory, query)
        trades = res['result']['trades']
        print_dict(calculate_fees(trades))
    elif args.aggregate:
        query = {}
        res = run_func(tradehistory, query)
        trades = res['result']['trades']
        myList = list()
        real_sum =aggregate(trades)
        for a,b in real_sum.items():
            row = {}
            row['coin'] = a
            row['buy'] = 0
            row['sell'] = 0
            row['balance'] = 0
            #import pdb;pdb.set_trace()
            for c,d in b.items():
                row[c] = d
            myList.append(row)
        printTable(myList,['coin','buy','sell', 'balance'])
    elif args.rec:
        recommend()

    
    
    #odict = json.dumps(tick)

    #f = open(args.dbfile,"a")
    #f.write(odict)
    #f.close()



if __name__ == "__main__":
   main(sys.argv[1:])


#result = run_func(get_balance, 0)
#print(result)
##result = run_func(order, 0)
##print(result)
#res = run_func(open_orders, 0)
#print(res)
##result['result']['
#
#
#
#
#
#
#
## Query open orders and cancel them all
##res = run_func(open_orders, 0)
##print(result)
##orders = res['result']['open']
##for order in orders:
##    result = run_func(cancel, order);
##    print(result)
#

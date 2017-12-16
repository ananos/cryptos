#!/usr/bin/env python3
# Simple Kraken operations

import krakenex
import time
import sys, getopt
from prettytable import *

import json
import argparse
 
sleepinterval = 8
k = krakenex.API()
k.load_key('kraken.key')
a = list()
dbdict = {}

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
        mydict.append(row)
        #print("{0}\t{1}\t{2}\tε{3}{4} ".format(coin, last[0], avg, int(toteuro), sign))
        #print_dict(row)
    printTable(mydict, ['coin', 'last', 'avg', 'toteuro'])

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


def print_dict(dicttoprint):
        t = PrettyTable(['key', 'value'])
        for key, val in dicttoprint.items():
            #if (isinstance(val, dict)):
            #    vallist = list()
            #    for key1,val1 in val.items():
            #       vallist.append([key1,val1]) 
            #    t.add_row([key, vallist])
            #else:
                t.add_row([key, val])
        print(t)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dbfile', help='DataBase file',required=False)
    parser.add_argument('-s','--stats', help='Show stats',required=False,action='store_true')
    parser.add_argument('-c','--cancel', help='Cancel Order <txid>',required=False)
    parser.add_argument('-o','--open', help='Open Orders ',required=False, action='store_true')
    parser.add_argument('-p','--place', help="Place Order ex: -p { 'pair': 'XXRPZEUR', 'type': 'sell', 'ordertype': 'limit', 'price': '1.5', 'volume': '30' } ",required=False)
    parser.add_argument('-b','--balance', help='Place Order ',required=False, action='store_true')
    args = parser.parse_args()
    if not args.dbfile:
        args.dbfile = "dbfile.json"

    
    query = {}
    #print ("Input file: %s" % args.dbfile)
    if args.stats:
        res = run_func(ticker, query)
        #print("Last price")
        tick = res['result']
        analysis(tick)
    elif args.cancel:
        query = { 'txid': args.cancel }
        res = run_func(cancel_order, query)
        print_dict(res['result'])
    elif args.open:
        query = { }
        res = run_func(open_orders, query)
        print_dict(res['result']['open'])
    elif args.place:
        query = eval(args.place)
        res = run_func(place_order, query)
        print_dict(res['result'])
    elif args.balance:
        query = {}
        res = run_func(get_balance, query)
        print_dict(res['result'])
    
    
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

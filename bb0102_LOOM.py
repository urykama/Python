#Бот для trailing stop (на примере Binance)

import sqlite3
import logging
import time
import os
import math
from datetime import datetime
from binance_api import Binance

bot = Binance(     API_KEY = 'RzP45uN1Vk1izyxino2rNvqOHSLu2FO9JbA2gQ3UGcfiHzjCIdp1xkQoZyqXk3jz',
                API_SECRET = 'zar0z7felabYwTZ0lCz8CW6wXZLLKqUDvP588Z2X8sSkh1iNbsW0HMWy1Pq6HmXA')

coin1 = 'LOOM'
coin2 = 'BTC'
settings = dict(
    symbol          = coin1 + coin2,    # Пара для отслеживания
    strategy        = "SELL",       # Стратегия - SELL (повышение), BUY (понижение)           
    stop_loss_perc  = 1,          # % оставания от цены
    stop_loss_fixed = 0.00006000,   # Изначальный stop-loss, можно установить руками нужную сумму, потом бот подтянет.
                                    # Можно указать 0, тогда бот высчитает, возьмет текущую цену и применит к ней процент
    amount          = 0.00001       # Кол-во монет, которое планируем продать (в случае SELL) или купить (в случае BUY)
                                    # Если указываем SELL, то альты для продажи (Например, продать 0.1 ETH в паре ETHBTC)
    )                               # Если BUY, то кол-во, на которое покупать, например купить на 0.1 BTC по паре ETHBTC

                                    # Получаем ограничения торгов по всем парам с биржи
limits = bot.exchangeInfo()         # Наши жесткие ограничения перечислены


def fBalance(coin):                 # Получаем балансы с биржи по указанным валютам
    return{balance['asset']:float(balance['free']) for balance in bot.account()['balances']if balance['asset']in[coin]}

def fCreatOrder(sy, si, qu):
    # Создает ордер по Маркету
    res = bot.createOrder(          symbol      = sy,           recvWindow  = 15000,            side        = si,
                                    type        = 'MARKET',     quantity    = qu    )
    print('Результат создания ордера', res)
    return res

def fLimits (sy):               # Получаем лимиты пары с биржи
    for elem in limits['symbols']:
        if elem['symbol'] == sy:                        
            CURR_LIMITS = elem
    return ( float(CURR_LIMITS['filters'][0]['tickSize']), float(CURR_LIMITS['filters'][2]['stepSize']), float(CURR_LIMITS['filters'][3]['minNotional']))

                # Получаем текущие курсы по паре
current_rates = bot.depth(symbol=settings['symbol'], limit=5)
settings['stop_loss_fixed'] = 0.00000213                                                                 # float(current_rates['bids'][0][0])
bid0 = ( 1 + 0.01 * settings['stop_loss_perc'] ) * settings['stop_loss_fixed']
print ('bid0 = = {sl:0.8f}'.format(sl=bid0))
print ("settings['stop_loss_fixed'] = = {sl:0.8f}".format(sl=settings['stop_loss_fixed']))

i = 0
while i < 6000:
    i+=1
    try:

        if settings['strategy'] == "SELL":
            current_rates = bot.depth(symbol=settings['symbol'], limit=5)           # Получаем текущие курсы по паре
            bid=float(current_rates['bids'][0][0])
            curr_rate_applied = ( 1 + 0.01 * settings['stop_loss_perc'] ) * bid     # Считаем, каким был бы stop-loss, если применить к нему %
            # Выбрана стратегия , пытаемся продать монеты как можно выгоднее
            if bid > bid0:
                if settings['stop_loss_fixed'] < bid:
                    # print("Текущая цена выше цены Stop-Loss")
                    if  settings['stop_loss_fixed'] < curr_rate_applied:                    
                        settings['stop_loss_fixed'] = curr_rate_applied
                        print("Пора изменять stop-loss, новое значение {sl:0.8f}".format(sl=curr_rate_applied))                    
                else:
                    tickSize, stepSize, minNotional = fLimits(settings['symbol'])
                    minQuantity = stepSize * ( minNotional / stepSize // curr_rate_applied + 1 )
                    print ('i = ', i , settings['symbol'], settings['strategy'], fBalance(coin1))
                    i = 600

                    
                res = fCreatOrder (settings['symbol'], settings['strategy'], fBalance(coin1))
                    # Текущая цена ниже или равна stop loss,                                                                 продажа по рынку

                if 'orderId' in res:
                    # Создание ордера прошло успешно, выход
                    break
            print ( 'i = ', i , "   bid = {s0:0.8f}   s_l_f = {s1:0.8f}  bid0 = {s2:0.8f}"
                                .format(s0=bid, s1=settings['stop_loss_fixed'], s2=bid0) )

        else:
            # Выбрана стратегия BUY, пытаемся                                                                 купить монеты как можно выгоднее
            if settings['stop_loss_fixed'] > curr_rate :
                # print("Текущая цена ниже stop-loss")
                if  settings['stop_loss_fixed'] > curr_rate_applied:                    
                    settings['stop_loss_fixed'] = curr_rate_applied
                    print("Пора изменять stop-loss, новое значение {sl:0.8f}".format(sl=curr_rate_applied))                    
            else:
                # Цена поднялась выше Stop-Loss,                                                               Покупка по рынку
                tickSize, stepSize, minNotional = fLimits(settings['symbol'])
                minQuantity = stepSize * ( minNotional / stepSize // curr_rate_applied + 1 )
#                quantity = math.floor((settings['amount']/curr_rate)*(1/step_sizes[settings['symbol']]))/(1/step_sizes[settings['symbol']])
                print("Цена поднялась выше Stop-Loss, Покупка по рынку, кол-во монет {minQuantity:0.8f}".format(quantity=quantity))
                # math.Floor(coins*(1/stepSize)) / (1 / stepSize)
                fCreatOrder (settings['symbol'], settings['strategy'], minQuantity)

                if 'orderId' in res:
                    # Создание ордера прошло успешно, выход
                    break

    except Exception as e:
        print(e)
    time.sleep(1)
#print(bot.myTrades(symbol='PPTETH'))


'''
price = 0.0018
tickSize, stepSize, minNotional = fLimits(settings['symbol'])
minQuantity = stepSize * ( minNotional / stepSize // price + 1 )

print ('tickSize = ', tickSize)
print ('stepSize = ', stepSize)
print ('minNotional = ', minNotional)
print (minQuantity)
'''

#def adjust_to_step(value, step, increase=False):
#    return ((int(value * 100000000) - int(value * 100000000) % int(float(step) * 100000000)) / 100000000)
#    +(float(step) if increase else 0)


    
#    else:
#        raise Exception("Не удалось найти настройки выбранной пары " + 'BNBBTC')

        
#for 'BNB' in limits['symbols']:

#    if elem['symbol'] == orders_info[order]['order_pair']:
#        print("TEST", elem['symbol'], orders_info[order]['order_pair'])
#        CURR_LIMITS = elem
#        break
#else:
#    raise Exception("Не удалось найти настройки выбранной пары " + pair_name)

'''
        # print('Проверяю пару {pair}, стратегия {strategy}'.format(pair=settings['symbol'], strategy=settings['strategy']))
        # Получаем текущие курсы по паре
        current_rates = bot.depth(symbol=settings['symbol'], limit=5)

        bid=float(current_rates['bids'][0][0])
        ask=float(current_rates['asks'][0][0])

        # Если играем на повышение, то ориентируемся на цены, по которым продают, иначе на цены, по которым покупают
        curr_rate = bid if settings['strategy'] == "SELL" else ask
        
        if settings['stop_loss_fixed'] == 0:
           settings['stop_loss_fixed'] = (curr_rate/100) * (settings['stop_loss_perc']*multiplier+100)
 
        print('i = ', i, "Текущие курсы bid {bid:0.8f}, ask {ask:0.8f}, выбрана {cr:0.8f} stop_loss {sl:0.8f}".format(
            bid=bid, ask=ask, cr=curr_rate, sl=settings['stop_loss_fixed']
        ))

        # Считаем, каким был бы stop-loss, если применить к нему %
        curr_rate_applied = (curr_rate/100) * (settings['stop_loss_perc']*multiplier+100)
'''

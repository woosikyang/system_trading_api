import time, copy
import yaml
import requests
import json
import pandas as pd
from collections import namedtuple
from datetime import datetime
import pymysql
from config import *
from utils import *
from utils_sql import *
from pandas_datareader import data as pdr
import yfinance as yf
from tqdm import tqdm

bse_date = '20230704'

auth(svr='prod', product='01')

code_to_name, name_to_code = get_code_name('kospi')
code_to_name2, name_to_code2 = get_code_name('kosdaq')
# target_company = '현대차'

#국내기관_외국인 매매종목가집계

def daily_foreign(bse_date) :
    url = '/uapi/domestic-stock/v1/quotations/foreign-institution-total'
    tr_id = "FHPTJ04400000"

    div_cls_cd = ['0','1']
    rank_cls_cd = ['0','1']

    for d_ in div_cls_cd :
        for r_ in rank_cls_cd :
            params = {
            'FID_COND_MRKT_DIV_CODE': 'V', # default
            'FID_COND_SCR_DIV_CODE': '16449', # default
            'FID_INPUT_ISCD': '0000', # 0000:전체, 0001:코스피, 1001:코스닥
            'FID_DIV_CLS_CODE': d_, # 0: 수량정열, 1: 금액정열
            'FID_RANK_SORT_CLS_CODE': r_, # 0: 순매수상위, 1: 순매도상위
            'FID_ETC_CLS_CODE': '0'
            }

            t1 = url_fetch(url, tr_id, params)
            result = t1.getBody().output
            insert_data = []
            for k in result :
                insert_data.append(tuple([bse_date, d_, r_] + list(k.values())))
            execute_sql(big_fish_sql,insert_data)



#주식현재가 일자별

def stock_price_range(stock_cd, data_type, st_date, end_date) :
    '''
    한건당 최대 100건

    :param stock_cd: 시장분류코드
    :param data_type: 종목코드
    :param st_date: 시작일자
    :param end_date: 종료일자
    :return: stock_info INSERT
    '''
    url = '/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice'
    tr_id = "FHKST03010100"


    params = {
    'FID_COND_MRKT_DIV_CODE': 'J', #
    'FID_INPUT_ISCD': stock_cd, #
    'FID_INPUT_DATE_1': st_date, #
    'FID_INPUT_DATE_2': end_date, #
    'FID_PERIOD_DIV_CODE': data_type, # 기간분류코드 DWMY
    'FID_ORG_ADJ_PRC': '0', # 0: 수정주가, 1: 원주가
    }

    t1 = url_fetch(url, tr_id, params)
    result = t1.getBody().output

    # insert_data = []
    # for k in result :
    #     insert_data.append(tuple([bse_date, d_, r_] + list(k.values())))
    #
    # execute_sql(big_fish_sql,insert_data)



'''
#전체 데이터 적재
'''


def daily_stock_price_yf(st_date=None, end_date=None) :
    global name_to_code, name_to_code2, bse_date
    yf.pdr_override()

    kospi_code = list(name_to_code.values())
    kosdaq_code = list(name_to_code2.values())
    not_done = []
    for k_ in tqdm(kospi_code + kosdaq_code) :
        if st_date and end_date :
            data = pdr.get_data_yahoo(f"{k_}.KS", st_date, end_date)
        else :
            data = pdr.get_data_yahoo(f"{k_}.KS")
        data = data.reset_index()
        data['Date'] = data['Date'].astype('str')
        data['Date'] = data['Date'].str.replace('-','')
        tmp = [tuple([k_] + list(k)) for k in data.values]
        # print(tmp[:10])
        sql = stock_price_sql
        try :
            execute_sql(sql,tmp)
            print(f"{k_} DONE")

        except pymysql.err.DataError :
            not_done.append(k_)
            print(f"{k_} NOT DONE")
            pd.DataFrame(not_done).to_csv(f'not_done_{bse_date}.txt')

daily_stock_price_yf()
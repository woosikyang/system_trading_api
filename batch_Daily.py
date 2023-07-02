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

bse_date = '20230702'

auth(svr='prod', product='01')

# code_to_name, name_to_code = un.get_code_name('kospi')
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


daily_foreign(bse_date)
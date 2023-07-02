import config
import time, copy
import yaml
import requests
import json
import pandas as pd
from collections import namedtuple
from datetime import datetime
import pymysql
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode



with open(r'kisdev_vi.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)

_cfg['my_app'] = config.my_app
_cfg['my_sec'] = config.my_sec

_TRENV = tuple()
_last_auth_time = datetime.now()
_autoReAuth = False
_DEBUG = True
_isPaper = True

_base_headers = {
    "Content-Type": "application/json",
    "Accept": "text/plain",
    "charset": "UTF-8",
    'User-Agent': _cfg['my_agent'] 
}

def _getBaseHeader():
    if _autoReAuth: reAuth()
    return copy.deepcopy(_base_headers)

def _setTRENV(cfg):
    nt1 = namedtuple('KISEnv', ['my_app','my_sec','my_acct', 'my_prod', 'my_token', 'my_url'])
    d = {
        'my_app': cfg['my_app'],
        'my_sec': cfg['my_sec'],
        'my_acct': cfg['my_acct'],
        'my_prod': cfg['my_prod'],
        'my_token': cfg['my_token'],
        'my_url' : cfg['my_url']
    }
    
    global _TRENV 
    _TRENV = nt1(**d)
    

def isPaperTrading():
    return _isPaper
    

def changeTREnv(token_key, svr='prod', product='01'):
    cfg = dict()

    global _isPaper
    if svr == 'prod':
        ak1 = 'my_app'
        ak2 = 'my_sec'
        _isPaper = False
    elif svr == 'vps':
        ak1 = 'paper_app'
        ak2 = 'paper_sec'
        _isPaper = True
        
    cfg['my_app'] = _cfg[ak1]
    cfg['my_sec'] = _cfg[ak2]   
    
    if svr == 'prod' and product == '01':
        cfg['my_acct'] = _cfg['my_acct_stock']
    elif svr == 'prod' and product == '03':
        cfg['my_acct'] = _cfg['my_acct_future']
    elif svr == 'vps' and product == '01':        
        cfg['my_acct'] = _cfg['my_paper_stock']
    elif svr == 'vps' and product == '03':        
        cfg['my_acct'] = _cfg['my_paper_future']

    cfg['my_prod'] = product
    cfg['my_token'] = token_key
    cfg['my_url'] = _cfg[svr] 
    
    _setTRENV(cfg)
    

def auth(svr='prod', product='01'):
    global _cfg
    p = {
        "grant_type": "client_credentials",
    }
    print(svr)
    if svr == 'prod':
        ak1 = 'my_app'
        ak2 = 'my_sec'
    elif svr == 'vps':
        ak1 = 'paper_app'
        ak2 = 'paper_sec'
        
    p["appkey"] = _cfg[ak1]
    p["appsecret"] = _cfg[ak2]
    

    url = f'{_cfg[svr]}/oauth2/tokenP'

    res = requests.post(url, data=json.dumps(p), headers=_getBaseHeader())
    rescode = res.status_code
    if rescode == 200:
        my_token = _getResultObject(res.json()).access_token
    else:
        print('Get Authentification token fail!\nYou have to restart your app!!!')  
        return
 
    changeTREnv(f"Bearer {my_token}", svr, product)
    
    _base_headers["authorization"] = _TRENV.my_token
    _base_headers["appkey"] = _TRENV.my_app
    _base_headers["appsecret"] = _TRENV.my_sec
    
    global _last_auth_time
    _last_auth_time = datetime.now()
    
    if (_DEBUG):
        print(f'[{_last_auth_time}] => get AUTH Key completed!')
    

def getEnv():
    return _cfg

def getTREnv():
    return _TRENV

def _getResultObject(json_data):
    _tc_ = namedtuple('res', json_data.keys())

    return _tc_(**json_data)



def _url_fetch(api_url, ptr_id, params, appendHeaders=None, postFlag=False, hashFlag=True):
    url = f"{getTREnv().my_url}{api_url}"

    headers = _getBaseHeader()

    # 추가 Header 설정
    tr_id = ptr_id
    if ptr_id[0] in ('T', 'J', 'C'):
        if isPaperTrading():
            tr_id = 'V' + ptr_id[1:]

    headers["tr_id"] = tr_id
    headers["custtype"] = "P"

    if appendHeaders is not None:
        if len(appendHeaders) > 0:
            for x in appendHeaders.keys():
                headers[x] = appendHeaders.get(x)

    if (_DEBUG):
        print("< Sending Info >")
        print(f"URL: {url}, TR: {tr_id}")
        print(f"<header>\n{headers}")
        print(f"<body>\n{params}")

    if (postFlag):
        if (hashFlag): set_order_hash_key(headers, params)
        res = requests.post(url, headers=headers, data=json.dumps(params))
    else:
        res = requests.get(url, headers=headers, params=params)

    if res.status_code == 200:
        ar = APIResp(res)
        if (_DEBUG): ar.printAll()
        return ar
    else:
        print("Error Code : " + str(res.status_code) + " | " + res.text)
        return None

def url_fetch(api_url, ptr_id, params, appendHeaders=None, postFlag=False, hashFlag=True):
    url = f"{getTREnv().my_url}{api_url}"

    headers = _getBaseHeader()

    # 추가 Header 설정
    tr_id = ptr_id
    if ptr_id[0] in ('T', 'J', 'C'):
        if isPaperTrading():
            tr_id = 'V' + ptr_id[1:]

    headers["tr_id"] = tr_id
    headers["custtype"] = "P"

    if appendHeaders is not None:
        if len(appendHeaders) > 0:
            for x in appendHeaders.keys():
                headers[x] = appendHeaders.get(x)

    if (_DEBUG):
        print("< Sending Info >")
        print(f"URL: {url}, TR: {tr_id}")
        print(f"<header>\n{headers}")
        print(f"<body>\n{params}")

    if (postFlag):
        if (hashFlag): set_order_hash_key(headers, params)
        res = requests.post(url, headers=headers, data=json.dumps(params))
    else:
        res = requests.get(url, headers=headers, params=params)

    if res.status_code == 200:
        ar = APIResp(res)
        if (_DEBUG): ar.printAll()
        return ar
    else:
        print("Error Code : " + str(res.status_code) + " | " + res.text)
        return None


#주문 API에서 사용할 hash key값을 받아 header에 설정해 주는 함수
# Input: HTTP Header, HTTP post param
# Output: None
def set_order_hash_key(h, p):
   
    url = f"{getTREnv().my_url}/uapi/hashkey"
  
    res = requests.post(url, data=json.dumps(p), headers=h)
    rescode = res.status_code
    if rescode == 200:
        h['hashkey'] = _getResultObject(res.json()).HASH
    else:
        print("Error:", rescode)


class APIResp:
    def __init__(self, resp):
        self._rescode = resp.status_code
        self._resp = resp
        self._header = self._setHeader()
        self._body = self._setBody()
        self._err_code = self._body.rt_cd
        self._err_message = self._body.msg1

    def getResCode(self):
        return self._rescode

    def _setHeader(self):
        fld = dict()
        for x in self._resp.headers.keys():
            if x.islower():
                fld[x] = self._resp.headers.get(x)
        _th_ = namedtuple('header', fld.keys())

        return _th_(**fld)

    def _setBody(self):
        _tb_ = namedtuple('body', self._resp.json().keys())

        return _tb_(**self._resp.json())

    def getHeader(self):
        return self._header

    def getBody(self):
        return self._body

    def getResponse(self):
        return self._resp

    def isOK(self):
        try:
            if (self.getBody().rt_cd == '0'):
                return True
            else:
                return False
        except:
            return False

    def getErrorCode(self):
        return self._err_code

    def getErrorMessage(self):
        return self._err_message

    def printAll(self):
        print("<Header>")
        for x in self.getHeader()._fields:
            print(f'\t-{x}: {getattr(self.getHeader(), x)}')
        print("<Body>")
        for x in self.getBody()._fields:
            print(f'\t-{x}: {getattr(self.getBody(), x)}')

    def printError(self):
        print('-------------------------------\nError in response: ', self.getResCode())
        print(self.getBody().rt_cd, self.getErrorCode(), self.getErrorMessage())
        print('-------------------------------')

    # end of class APIResp
    
    

# end of initialize
def reAuth(svr='prod', product='01'):
    n2 = datetime.now()
    if (n2 - _last_auth_time).seconds >= 86400:
        auth(svr, product)

        
def get_acct_balance(rtCashFlag=False):
    url = '/uapi/domestic-stock/v1/trading/inquire-psbl-order'
    tr_id = "TTTC8434R"

    params = {
        'CANO': getTREnv().my_acct,
        'ACNT_PRDT_CD': '01',
        'AFHR_FLPR_YN': 'N',
        'FNCG_AMT_AUTO_RDPT_YN': 'N',
        'FUND_STTL_ICLD_YN': 'N',
        'INQR_DVSN': '01',
        'OFL_YN': 'N',
        'PRCS_DVSN': '01',
        'UNPR_DVSN': '01',
        'CTX_AREA_FK100': '',
        'CTX_AREA_NK100': ''
    }

    t1 = _url_fetch(url, tr_id, params)
    if rtCashFlag and t1.isOK():
        r2 = t1.getBody().output2
        return int(r2[0]['dnca_tot_amt'])

    if t1.isOK() and t1.getBody().output1:  # body 의 rt_cd 가 0 인 경우만 성공
        tdf = pd.DataFrame(t1.getBody().output1)
        tdf.set_index('pdno', inplace=True)
        cf1 = ['prdt_name', 'hldg_qty', 'ord_psbl_qty', 'pchs_avg_pric', 'evlu_pfls_rt', 'prpr', 'bfdy_cprs_icdc',
               'fltt_rt']
        cf2 = ['종목명', '보유수량', '매도가능수량', '매입단가', '수익율', '현재가', '전일대비', '등락']
        tdf = tdf[cf1]
        tdf[cf1[1:]] = tdf[cf1[1:]].apply(pd.to_numeric)
        ren_dict = dict(zip(cf1, cf2))
        return tdf.rename(columns=ren_dict)

    else:
        t1.printError()
        return pd.DataFrame()

    
    
    

# 종목의 주식, ETF, 선물/옵션 등의 구분값을 반환. 현재는 무조건 주식(J)만 반환
def _getStockDiv(stock_no):
    return 'J'
    

# 종목별 현재가를 dict 로 반환
# Input: 종목코드
# Output: 현재가 Info dictionary. 반환된 dict 가 len(dict) < 1 경우는 에러로 보면 됨

def get_current_price(stock_no):
    url = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = "FHKST01010100"

    params = {
        'FID_COND_MRKT_DIV_CODE': _getStockDiv(stock_no),
        'FID_INPUT_ISCD': stock_no
    }

    t1 = _url_fetch(url, tr_id, params)

    if t1.isOK():
        return t1.getBody().output
    else:
        t1.printError()
        return dict()    
    

# 주문 base function
# Input: 종목코드, 주문수량, 주문가격, Buy Flag(If True, it's Buy order), order_type="00"(지정가)
# Output: HTTP Response

def do_order(stock_code, order_qty, order_price, prd_code="01", buy_flag=True, order_type="00"):
    url = "/uapi/domestic-stock/v1/trading/order-cash"

    if buy_flag:
        tr_id = "TTTC0802U"  # buy
    else:
        tr_id = "TTTC0801U"  # sell

    params = {
        'CANO': getTREnv().my_acct,
        'ACNT_PRDT_CD': prd_code,
        'PDNO': stock_code,
        'ORD_DVSN': order_type,
        'ORD_QTY': str(order_qty),
        'ORD_UNPR': str(order_price),
        'CTAC_TLNO': '',
        'SLL_TYPE': '01',
        'ALGO_NO': ''
    }

    t1 = _url_fetch(url, tr_id, params, postFlag=True, hashFlag=True)

    if t1.isOK():
        return t1
    else:
        t1.printError()
        return None
    

# 팔자 주문. 내부적으로는 do_order 를 호출한다.
# Input: 종목코드, 주문수량, 주문가격
# Output: True, False

def do_sell(stock_code, order_qty, order_price, prd_code="01", order_type="00"):
    t1 = do_order(stock_code, order_qty, order_price, buy_flag=False, order_type=order_type)
    return t1.isOK()
    


# 사자 주문. 내부적으로는 do_order 를 호출한다.
# Input: 종목코드, 주문수량, 주문가격
# Output: True, False

def do_buy(stock_code, order_qty, order_price, prd_code="01", order_type="00"):
    t1 = do_order(stock_code, order_qty, order_price, buy_flag=True, order_type=order_type)
    return t1.isOK()


# 정정취소 가능한 주문 목록을 DataFrame 으로 반환
# Input: None
# Output: DataFrame

def get_orders(prd_code='01'):
    url = "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"

    tr_id = "TTTC8036R"

    params = {
        "CANO": getTREnv().my_acct,
        "ACNT_PRDT_CD": prd_code,
        "CTX_AREA_FK100": '',
        "CTX_AREA_NK100": '',
        "INQR_DVSN_1": '0',
        "INQR_DVSN_2": '0'
    }

    t1 = _url_fetch(url, tr_id, params)
    if t1.isOK() and len(t1.getBody().output) >= 1:
        tdf = pd.DataFrame(t1.getBody().output)
        tdf.set_index('odno', inplace=True)
        cf1 = ['pdno', 'ord_qty', 'ord_unpr', 'ord_tmd', 'ord_gno_brno', 'orgn_odno']
        cf2 = ['종목코드', '주문수량', '주문가격', '시간', '주문점', '원번호']
        tdf = tdf[cf1]
        ren_dict = dict(zip(cf1, cf2))

        return tdf.rename(columns=ren_dict)

    else:
        t1.printError()
        return pd.DataFrame()
    
    

# 특정 주문 취소(01)/정정(02)
# Input: 주문 번호(get_orders 를 호출하여 얻은 DataFrame 의 index  column 값이 취소 가능한 주문번호임)
#       주문점(통상 06010), 주문수량, 주문가격, 상품코드(01), 주문유형(00), 정정구분(취소-02, 정정-01)
# Output: APIResp object

def _do_cancel_revise(order_no, order_branch, order_qty, order_price, prd_code, order_dv, cncl_dv, qty_all_yn):
    url = "/uapi/domestic-stock/v1/trading/order-rvsecncl"

    tr_id = "TTTC0803U"

    params = {
        "CANO": getTREnv().my_acct,
        "ACNT_PRDT_CD": prd_code,
        "KRX_FWDG_ORD_ORGNO": order_branch,
        "ORGN_ODNO": order_no,
        "ORD_DVSN": order_dv,
        "RVSE_CNCL_DVSN_CD": cncl_dv,  # 취소(02)
        "ORD_QTY": str(order_qty),
        "ORD_UNPR": str(order_price),
        "QTY_ALL_ORD_YN": qty_all_yn
    }

    t1 = _url_fetch(url, tr_id, params=params, postFlag=True)

    if t1.isOK():
        return t1
    else:
        t1.printError()
        return None
    

# 특정 주문 취소
#
def do_cancel(order_no, order_qty, order_price="01", order_branch='06010', prd_code='01', order_dv='00', cncl_dv='02',
              qty_all_yn="Y"):
    return _do_cancel_revise(order_no, order_branch, order_qty, order_price, prd_code, order_dv, cncl_dv, qty_all_yn)


# 특정 주문 정정
#
def do_revise(order_no, order_qty, order_price, order_branch='06010', prd_code='01', order_dv='00', cncl_dv='01',
              qty_all_yn="Y"):
    return _do_cancel_revise(order_no, order_branch, order_qty, order_price, prd_code, order_dv, cncl_dv, qty_all_yn)




# 모든 주문 취소
# Input: None
# Output: None

def do_cancel_all():
    tdf = get_orders()
    od_list = tdf.index.to_list()
    qty_list = tdf['주문수량'].to_list()
    price_list = tdf['주문가격'].to_list()
    branch_list = tdf['주문점'].to_list()
    cnt = 0
    for x in od_list:
        ar = do_cancel(x, qty_list[cnt], price_list[cnt], branch_list[cnt])
        cnt += 1
        print(ar.getErrorCode(), ar.getErrorMessage())
        time.sleep(.2)


# 내 계좌의 일별 주문 체결 조회
# Input: 시작일, 종료일 (Option)지정하지 않으면 현재일
# output: DataFrame

def get_my_complete(sdt, edt=None, prd_code='01', zipFlag=True):
    url = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
    tr_id = "TTTC8001R"

    if (edt is None):
        ltdt = datetime.now().strftime('%Y%m%d')
    else:
        ltdt = edt

    params = {
        "CANO": getTREnv().my_acct,
        "ACNT_PRDT_CD": prd_code,
        "INQR_STRT_DT": sdt,
        "INQR_END_DT": ltdt,
        "SLL_BUY_DVSN_CD": '00',
        "INQR_DVSN": '00',
        "PDNO": "",
        "CCLD_DVSN": "00",
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "INQR_DVSN_3": "00",
        "INQR_DVSN_1": "",
        "INQR_DVSN_2": "",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }

    t1 = _url_fetch(url, tr_id, params)

    # output1 과 output2 로 나뉘어서 결과가 옴. 지금은 output1만 DF 로 변환
    if t1.isOK():
        tdf = pd.DataFrame(t1.getBody().output1)
        tdf.set_index('odno', inplace=True)
        if (zipFlag):
            return tdf[
                ['ord_dt', 'orgn_odno', 'sll_buy_dvsn_cd_name', 'pdno', 'ord_qty', 'ord_unpr', 'avg_prvs', 'cncl_yn',
                 'tot_ccld_amt', 'rmn_qty']]
        else:
            return tdf
    else:
        t1.printError()
        return pd.DataFrame()
    
    

# 매수 가능(현금) 조회
# Input: None
# Output: 매수 가능 현금 액수
def get_buyable_cash(stock_code='', qry_price=0, prd_code='01'):
    url = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
    tr_id = "TTTC8908R"

    params = {
        "CANO": getTREnv().my_acct,
        "ACNT_PRDT_CD": prd_code,
        "PDNO": stock_code,
        "ORD_UNPR": str(qry_price),
        "ORD_DVSN": "02",
        "CMA_EVLU_AMT_ICLD_YN": "Y",  # API 설명부분 수정 필요 (YN)
        "OVRS_ICLD_YN": "N"
    }

    t1 = _url_fetch(url, tr_id, params)

    if t1.isOK():
        return int(t1.getBody().output['ord_psbl_cash'])
    else:
        t1.printError()
        return 0


# 시세 Function

# 종목별 체결 Data
# Input: 종목코드
# Output: 체결 Data DataFrame
# 주식체결시간, 주식현재가, 전일대비, 전일대비부호, 체결거래량, 당일 체결강도, 전일대비율
def get_stock_completed(stock_no):
    url = "/uapi/domestic-stock/v1/quotations/inquire-ccnl"

    tr_id = "FHKST01010300"

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_no
    }

    t1 = _url_fetch(url, tr_id, params)

    if t1.isOK():
        return pd.DataFrame(t1.getBody().output)
    else:
        t1.printError()
        return pd.DataFrame()    
    
    


# 종목별 history data (현재 기준 30개만 조회 가능)
# Input: 종목코드, 구분(D, W, M 기본값은 D)
# output: 시세 History DataFrame
def get_stock_history(stock_no, gb_cd='D'):
    url = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    tr_id = "FHKST01010400"

    params = {
        "FID_COND_MRKT_DIV_CODE": _getStockDiv(stock_no),
        "FID_INPUT_ISCD": stock_no,
        "FID_PERIOD_DIV_CODE": gb_cd,
        "FID_ORG_ADJ_PRC": "0000000001"
    }

    t1 = _url_fetch(url, tr_id, params)

    if t1.isOK():
        return pd.DataFrame(t1.getBody().output)
    else:
        t1.printError()
        return pd.DataFrame()


# 종목별 history data 를 표준 OHLCV DataFrame 으로 반환
# Input: 종목코드, 구분(D, W, M 기본값은 D), (Option)adVar 을 True 로 설정하면
#        OHLCV 외에 inter_volatile 과 pct_change 를 추가로 반환한다.
# output: 시세 History OHLCV DataFrame
def get_stock_history_by_ohlcv(stock_no, gb_cd='D', adVar=False):
    hdf1 = get_stock_history(stock_no, gb_cd)

    chosend_fld = ['stck_bsop_date', 'stck_oprc', 'stck_hgpr', 'stck_lwpr', 'stck_clpr', 'acml_vol']
    renamed_fld = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']

    hdf1 = hdf1[chosend_fld]
    ren_dict = dict()
    i = 0
    for x in chosend_fld:
        ren_dict[x] = renamed_fld[i]
        i += 1

    hdf1.rename(columns=ren_dict, inplace=True)
    hdf1[['Date']] = hdf1[['Date']].apply(pd.to_datetime)
    hdf1[['Open', 'High', 'Low', 'Close', 'Volume']] = hdf1[['Open', 'High', 'Low', 'Close', 'Volume']].apply(
        pd.to_numeric)
    hdf1.set_index('Date', inplace=True)

    if (adVar):
        hdf1['inter_volatile'] = (hdf1['High'] - hdf1['Low']) / hdf1['Close']
        hdf1['pct_change'] = (hdf1['Close'] - hdf1['Close'].shift(-1)) / hdf1['Close'].shift(-1) * 100

    return hdf1


# 투자자별 매매 동향
# Input: 종목코드
# output: 매매 동향 History DataFrame (Date, PerBuy, ForBuy, OrgBuy) 30개 row를 반환
def get_stock_investor(stock_no):
    url = "/uapi/domestic-stock/v1/quotations/inquire-investor"
    tr_id = "FHKST01010900"

    params = {
        "FID_COND_MRKT_DIV_CODE": _getStockDiv(stock_no),
        "FID_INPUT_ISCD": stock_no
    }

    t1 = _url_fetch(url, tr_id, params)

    if t1.isOK():
        hdf1 = pd.DataFrame(t1.getBody().output)

        chosend_fld = ['stck_bsop_date', 'prsn_ntby_qty', 'frgn_ntby_qty', 'orgn_ntby_qty']
        renamed_fld = ['Date', 'PerBuy', 'ForBuy', 'OrgBuy']

        hdf1 = hdf1[chosend_fld]
        ren_dict = dict()
        i = 0
        for x in chosend_fld:
            ren_dict[x] = renamed_fld[i]
            i += 1

        hdf1.rename(columns=ren_dict, inplace=True)
        hdf1[['Date']] = hdf1[['Date']].apply(pd.to_datetime)
        hdf1[['PerBuy', 'ForBuy', 'OrgBuy']] = hdf1[['PerBuy', 'ForBuy', 'OrgBuy']].apply(pd.to_numeric)
        hdf1['EtcBuy'] = (hdf1['PerBuy'] + hdf1['ForBuy'] + hdf1['OrgBuy']) * -1
        hdf1.set_index('Date', inplace=True)
        # sum을 맨 마지막에 추가하는 경우
        # tdf.append(tdf.sum(numeric_only=True), ignore_index=True) <- index를 없애고  만드는 경우
        # tdf.loc['Total'] = tdf.sum() <- index 에 Total 을 추가하는 경우
        return hdf1
    else:
        t1.printError()
        return pd.DataFrame()    
    
    

# AES256 DECODE
def aes_cbc_base64_dec(key, iv, cipher_text):
    """
    :param key:  str type AES256 secret key value
    :param iv: str type AES256 Initialize Vector
    :param cipher_text: Base64 encoded AES256 str
    :return: Base64-AES256 decodec str
    """
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    return bytes.decode(unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size))


# 웹소켓 접속키 발급
def get_approval(key, secret):
    
    # url = https://openapivts.koreainvestment.com:29443' # 모의투자계좌     
    url = 'https://openapi.koreainvestment.com:9443' # 실전투자계좌
    headers = {"content-type": "application/json"}
    body = {"grant_type": "client_credentials",
            "appkey": key,
            "secretkey": secret}
    PATH = "oauth2/Approval"
    URL = f"{url}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    approval_key = res.json()["approval_key"]
    return approval_key


# 주식체결 출력라이브러리
def stockhoka(data):
    """ 넘겨받는데이터가 정상인지 확인
    print("stockhoka[%s]"%(data))
    """
    recvvalue = data.split('^')  # 수신데이터를 split '^'

    print("유가증권 단축 종목코드 [" + recvvalue[0] + "]")
    print("영업시간 [" + recvvalue[1] + "]" + "시간구분코드 [" + recvvalue[2] + "]")
    print("======================================")
    print("매도호가10 [%s]    잔량10 [%s]" % (recvvalue[12], recvvalue[32]))
    print("매도호가09 [%s]    잔량09 [%s]" % (recvvalue[11], recvvalue[31]))
    print("매도호가08 [%s]    잔량08 [%s]" % (recvvalue[10], recvvalue[30]))
    print("매도호가07 [%s]    잔량07 [%s]" % (recvvalue[9], recvvalue[29]))
    print("매도호가06 [%s]    잔량06 [%s]" % (recvvalue[8], recvvalue[28]))
    print("매도호가05 [%s]    잔량05 [%s]" % (recvvalue[7], recvvalue[27]))
    print("매도호가04 [%s]    잔량04 [%s]" % (recvvalue[6], recvvalue[26]))
    print("매도호가03 [%s]    잔량03 [%s]" % (recvvalue[5], recvvalue[25]))
    print("매도호가02 [%s]    잔량02 [%s]" % (recvvalue[4], recvvalue[24]))
    print("매도호가01 [%s]    잔량01 [%s]" % (recvvalue[3], recvvalue[23]))
    print("--------------------------------------")
    print("매수호가01 [%s]    잔량01 [%s]" % (recvvalue[13], recvvalue[33]))
    print("매수호가02 [%s]    잔량02 [%s]" % (recvvalue[14], recvvalue[34]))
    print("매수호가03 [%s]    잔량03 [%s]" % (recvvalue[15], recvvalue[35]))
    print("매수호가04 [%s]    잔량04 [%s]" % (recvvalue[16], recvvalue[36]))
    print("매수호가05 [%s]    잔량05 [%s]" % (recvvalue[17], recvvalue[37]))
    print("매수호가06 [%s]    잔량06 [%s]" % (recvvalue[18], recvvalue[38]))
    print("매수호가07 [%s]    잔량07 [%s]" % (recvvalue[19], recvvalue[39]))
    print("매수호가08 [%s]    잔량08 [%s]" % (recvvalue[20], recvvalue[40]))
    print("매수호가09 [%s]    잔량09 [%s]" % (recvvalue[21], recvvalue[41]))
    print("매수호가10 [%s]    잔량10 [%s]" % (recvvalue[22], recvvalue[42]))
    print("======================================")
    print("총매도호가 잔량        [%s]" % (recvvalue[43]))
    print("총매도호가 잔량 증감   [%s]" % (recvvalue[54]))
    print("총매수호가 잔량        [%s]" % (recvvalue[44]))
    print("총매수호가 잔량 증감   [%s]" % (recvvalue[55]))
    print("시간외 총매도호가 잔량 [%s]" % (recvvalue[45]))
    print("시간외 총매수호가 증감 [%s]" % (recvvalue[46]))
    print("시간외 총매도호가 잔량 [%s]" % (recvvalue[56]))
    print("시간외 총매수호가 증감 [%s]" % (recvvalue[57]))
    print("예상 체결가            [%s]" % (recvvalue[47]))
    print("예상 체결량            [%s]" % (recvvalue[48]))
    print("예상 거래량            [%s]" % (recvvalue[49]))
    print("예상체결 대비          [%s]" % (recvvalue[50]))
    print("부호                   [%s]" % (recvvalue[51]))
    print("예상체결 전일대비율    [%s]" % (recvvalue[52]))
    print("누적거래량             [%s]" % (recvvalue[53]))
    print("주식매매 구분코드      [%s]" % (recvvalue[58]))



# 주식체결처리 출력라이브러리
def stockspurchase(data_cnt, data):
    print("============================================")
    menulist = "유가증권단축종목코드|주식체결시간|주식현재가|전일대비부호|전일대비|전일대비율|가중평균주식가격|주식시가|주식최고가|주식최저가|매도호가1|매수호가1|체결거래량|누적거래량|누적거래대금|매도체결건수|매수체결건수|순매수체결건수|체결강도|총매도수량|총매수수량|체결구분|매수비율|전일거래량대비등락율|시가시간|시가대비구분|시가대비|최고가시간|고가대비구분|고가대비|최저가시간|저가대비구분|저가대비|영업일자|신장운영구분코드|거래정지여부|매도호가잔량|매수호가잔량|총매도호가잔량|총매수호가잔량|거래량회전율|전일동시간누적거래량|전일동시간누적거래량비율|시간구분코드|임의종료구분코드|정적VI발동기준가"
    menustr = menulist.split('|')
    pValue = data.split('^')
    i = 0
    for cnt in range(data_cnt):  # 넘겨받은 체결데이터 개수만큼 print 한다
        print("### [%d / %d]" % (cnt + 1, data_cnt))
        for menu in menustr:
            print("%-13s[%s]" % (menu, pValue[i]))
            i += 1



# 주식체결통보 출력라이브러리
def stocksigningnotice(data, key, iv):
    menulist = "고객ID|계좌번호|주문번호|원주문번호|매도매수구분|정정구분|주문종류|주문조건|주식단축종목코드|체결수량|체결단가|주식체결시간|거부여부|체결여부|접수여부|지점번호|주문수량|계좌명|체결종목명|신용구분|신용대출일자|체결종목명40|주문가격"
    menustr1 = menulist.split('|')

    # AES256 처리 단계
    aes_dec_str = aes_cbc_base64_dec(key, iv, data)
    pValue = aes_dec_str.split('^')

    if pValue[12] == '2': # 체결통보
        print("#### 국내주식 체결 통보 ####")
    else:
        print("#### 국내주식 주문·정정·취소·거부 접수 통보 ####")
    
    i = 0
    for menu in menustr1:
        print("%s  [%s]" % (menu, pValue[i]))
        i += 1
    
    
    
    
    
    
    
    
    
# kospi / kosdaq 종목코드 및 종목명 리턴 함수
def get_code_name(name) :
    if  name == 'kospi' : 
        kospi = pd.read_table('kospi_code_mst.csv', sep= ',')
        cols = ['단축코드', '한글명','그룹코드']
        kospi = kospi[cols]
        kospi = kospi[kospi['그룹코드'] =='ST']
        kospi = kospi.iloc[:, :2]
        code_to_name = {}
        name_to_code = {}
        for k in kospi.values : 
            code_to_name[k[0]] = k[1]
            name_to_code[k[1]] = k[0]
    else : 
        kosdaq = pd.read_table('kosdaq_code_mst.csv', sep= ',')
        cols = ['단축코드', '한글종목명','증권그룹구분코드']
        kosdaq = kosdaq[cols]
        kosdaq = kosdaq[kosdaq['증권그룹구분코드'] =='ST']
        kosdaq = kosdaq.iloc[:, :2]
        code_to_name = {}
        name_to_code = {}
        for k in kosdaq.values : 
            code_to_name[k[0]] = k[1]
            name_to_code[k[1]] = k[0]
            
    return code_to_name, name_to_code





    
#DB 연계 함수 
def execute_sql(sql, values) :
    # global ip, password
    conn = pymysql.connect(host=config.ip,
                       user=config.user,
                       password=config.password,
                       charset='utf8',
                       database= config.database,
                       port=config.port_num)

    cur = conn.cursor()
    if ('select' in sql) or ('SELECT' in sql) : 
        cur.execute(sql)
        result = cur.fetchall()
        conn.commit()
        conn.close()
        return result
    elif ('insert' in sql) or ('INSERT' in sql) : 
        cur.executemany(sql, values)
        conn.commit()
        conn.close()
    else : 
        cur.execute(sql)
        conn.commit()
        conn.close()
    return print(f'||{sql}|| DONE') 
##한국투자증권 KIS_DEVELOPERS 기준 시스템 구축




### API 파라미터 참고 문서
https://apiportal.koreainvestment.com/apiservice/apiservice-domestic-stock-quotations#L_07802512-4f49-4486-91b4-1050b6f5dc9d


#####Function Lists 

--

_getStockDiv : 종목의 주식, ETF, 선물/옵션 등의 구분값을 반환
get_current_price : 종목별 현재가를 dict 로 반환
do_order : 주문 base function
do_sell : 사자 주문. 내부적으로는 do_order 를 호출한다.
do_buy : 팔자 주문. 내부적으로는 do_order 를 호출한다.
get_orders : 정정취소 가능한 주문 목록을 DataFrame 으로 반환
_do_cancel_revise : 특정 주문 취소(01)/정정(02)
do_cancel : 특정 주문 취소
do_revise : 특정 주문 정정
do_cancel_all : 모든 주문 취소
get_my_complete : 내 계좌의 일별 주문 체결 조회
get_buyable_cash : 매수 가능(현금) 조회
get_stock_completed : 종목별 체결 Data
get_stock_history : 종목별 history data (현재 기준 30개만 조회 가능)
get_stock_history_by_ohlcv : 종목별 history data 를 표준 OHLCV DataFrame 으로 반환
get_stock_investor : 투자자별 매매 동향


--







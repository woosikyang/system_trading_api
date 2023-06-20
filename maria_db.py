import pymysql
# import configs
ip = '192.168.0.5'
password = '100djrqnwk!'
# slack_api_token = 'xoxb-2196031379702-2188126140887-h1wJ64A2MOwGJgVemhjjMmXo'


'''
RISE : 급상승 종목 속성 저장 테이블


'''



conn = pymysql.connect(host=ip,
                       user='root',
                       password=password,
                       charset='utf8',
                       database='uprising',
                       port=3306)

cur = conn.cursor()


sql = "create table employees(employee_id varchar(10), employee_name varchar(100))"

sql = "insert into employees values \
('emp10', 'Bryan Nelson'), \
('emp12', 'Rosalyn Sanders'), \
('emp13', 'Rose Tudler'), \
('emp20', 'Julio Gomez'), \
('emp30', 'Ian McGregor'), \
('emp40', 'Anne Hatt')"


# 종목코드, 시간, 대비부호, 대비, 현재가, 시가, 매도호가, 매수호가, 거래량, 거래대금, 전일거래량, 체결강도

option = 'select'

if option == 'create' :
    sql = "create table if not exists RISE(code varchar(10), cur_time char(5), daebi_buho char(1), daebi varchar(5)," \
          " cur_price int, start_price int, ask_price int, sell_price int, amout int, money_amount int, previous_amount int, power float)"
elif option == 'insert' :
    sql = "insert RISE"
elif option == 'delete' :
    sql = "delete RISE"

#sql 실행

sql = "select * from employees"


cur.execute(sql)

#저장
conn.commit()

#종료
conn.close()




sql = "select * from employees"
cur.execute(sql)
result = cur.fetchall()
for data in result :
    print(data)

sql = "select * from employees where employee_id like 'emp1%' and employee_name like 'Ro%'"

cur.execute(sql)
result = cur.fetchall()
for data in result :
    print(data)

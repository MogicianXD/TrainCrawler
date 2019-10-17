import csv
import math

import pandas as pd
import pymysql

import re

base = 0.05861
switch = [0, 200, 500, 1000, 1500, 2500]
discount_table = {switch[0]: 1, switch[1]: 0.9, switch[2]: 0.8, switch[3]: 0.7, switch[4]: 0.6, switch[5]: 0.5}
amul_table = {0: 0}
pre_m = 0
for m in switch[1:]:
    amul_table[m] = (m - pre_m) * discount_table[pre_m] * base + amul_table[pre_m]
    pre_m = m
price_rate_table = {'硬座': 1, '无座': 1, '软座': 2, '普快': 0.2, '快速': 0.65, '特快': 0.65,
                    '硬卧上': 1.1, '硬卧中': 1.2, '硬卧下': 1.3, '软卧上': 1.75, '软卧下': 1.95,
                    '动车二等': 1.5, '动车一等': 2.25,
                    '高铁二等': 2.25, '高铁一等': 3.95, '高铁特等': 7.3}


def get_price(mileage):
    case = 0
    for each in range(len(switch)):
        if mileage > switch[each]:
            case = each
        else:
            break
    base_price = base * (mileage - switch[case]) * discount_table[switch[case]] + amul_table[switch[case]]
    # add_price = 0
    # if type in price_rate_table:
    #     add_price = price_rate_table[type] * base_price
    return round(base_price, 2)


seat_table = {'G':1070,'K':1546,'Z':1472,'T':1472,'D':1058,'0':758}


def proposal():
    tids = pd.read_csv('data/tid.csv')['tid'].tolist()
    df = pd.read_csv('data/info.csv')
    df = df[df['tid'].isin(tids)]
    df = df.drop_duplicates(subset=['tid', 'sno'])
    df['sno'] = df['sno'].apply(lambda x: x-1)

    alloc_func = lambda m, n, s: math.pow((n - m) * (s - m) * n / s ** 3, 1 / 3)
    columns = ['tid', 'sname1', 'sname2', 'price', 'tkt_alloc']
    res_df = pd.DataFrame(columns=columns)

    with open('data/proposal.csv', 'w+', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for group in df.groupby(['tid']):
            tid = group[0]
            i = 0
            print(tid)
            for row in group[1].iterrows():
                value = row[1]
                sname1 = value['sname']
                sno1 = value['sno']
                sum = group[1].shape[0]-1
                for row2 in group[1].iterrows():
                    value2 = row2[1]
                    sno2 = value2['sno']
                    if sno2 > sno1:
                        sname2 = value2['sname']
                        mileage = value2['mileage'] - value['mileage']
                        price = get_price(mileage)
                        alloc = alloc_func(sno1, sno2, sum)
                        if tid[0] in seat_table:
                            seat_sum = seat_table[tid[0]]
                        else:
                            seat_sum = seat_table['0']
                        writer.writerow([sname1, sname2, tid, price, int(alloc * seat_sum)])


def carriage():
    tids = pd.read_csv('data/tid.csv')['tid'].tolist()
    columns = ['tid', 'cid', 'ctype', 'seat_num']
    with open('data/carriage.csv', 'w+', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for tid in tids:
            if tid[0] == 'G':
                for i in range(2+4+10):
                    if i in [0, 15]:
                        writer.writerow([tid, i+1, '商务', 6])
                    elif i in [2, 3, 13, 14]:
                        writer.writerow([tid, i+1, '一等', 13*4])
                    else:
                        writer.writerow([tid, i+1, '二等', 17*5])
            elif tid[0] == 'D':
                for i in range(4+10):
                    if i in [0, 1, 12, 13]:
                        writer.writerow([tid, i+1, '一等', 13*4])
                    else:
                        writer.writerow([tid, i+1, '二等', 17*5])
            elif tid[0] == 'T' or tid[0] == 'Z':
                for i in range(18):
                    if i == 0:
                        writer.writerow([tid, i+1, '高级软卧', 16])
                    elif i == 1:
                        writer.writerow([tid, i+1, '软卧', 36])
                    elif i <= 11:
                        writer.writerow([tid, i+1, '硬卧', 66])
                    elif i <= 16:
                        writer.writerow([tid, i+1, '硬座', 128])
                    else:
                        writer.writerow([tid, i + 1, '无座', 120])
            elif tid[0] == 'K':
                for i in range(16):
                    if i == 0:
                        writer.writerow([tid, i+1, '软卧', 36])
                    elif i <= 6:
                        writer.writerow([tid, i+1, '硬卧', 66])
                    elif i <= 14:
                        writer.writerow([tid, i+1, '硬座', 118])
                    else:
                        writer.writerow([tid, i + 1, '无座', 170])
            else:
                for i in range(8):
                    if i == 0:
                        writer.writerow([tid, i+1, '软卧', 36])
                    elif i <= 3:
                        writer.writerow([tid, i+1, '硬卧', 66])
                    elif i <= 6:
                        writer.writerow([tid, i+1, '硬座', 118])
                    else:
                        writer.writerow([tid, i + 1, '无座', 170])


def seat_info():
    carriages = pd.read_csv('data/carriage.csv')
    carriages['bitmap'] = carriages['seat_num'].apply(lambda x: "0b"+'1'*x)
    tid_snames = pd.read_csv('data/via.csv')
    tid_snames = tid_snames[~tid_snames['depart_time'].isin(['-99:00'])][['tid', 'sname']]
    columns = ['sname', 'tid', 'cid', 'bitmap']
    df = pd.merge(carriages, tid_snames, on='tid')
    df = df[columns]
    df.to_csv('data/seat.csv', index=0)



def insert_day():
    dates = pd.date_range('2019-09-01', '2019-09-30', normalize=True)
    print(dates)
    pd.DataFrame(dates).to_csv('data/tb_date.csv', index=0)



def init():
    dates = pd.date_range('2019-09-01', '2019-09-30', normalize=True)
    df = pd.read_csv('data/proposal.csv')

    columns = ['ride_day', 'tid', 'sname1', 'sname2', 'price', 'tkt_alloc']
    # info_df = pd.DataFrame(columns=columns)
    for date in dates:
        print(date)
        df['ride_day'] = date
        df = df[columns]
        df.to_csv('data/train_info.csv', index=0, mode='a+')
    #     info_df = info_df.append(df, ignore_index=True, sort=False)
    # info_df.to_csv('data/train_info.csv', index=0)


def connDB():
    # 连接数据库
    conn = pymysql.connect(host='localhost', user='root', passwd='root1037', db='train_ticket', charset='utf8')
    cur = conn.cursor()
    return (conn, cur)


def exeUpdate(conn, cur, sql):
    # 更新语句，可执行Update，Insert语句
    sta = cur.execute(sql)
    conn.commit()
    return (sta)


def exeQuery(cur, sql):
    # 查询语句
    cur.execute(sql)
    result = cur.fetchone()
    return (result)


def connClose(conn, cur):
    # 关闭所有连接
    cur.close()
    conn.close()


def seat_info_insert():
    conn, cur = connDB()
    seat_info = pd.read_csv('data/seat.csv')
    seat_info['ride_day'] = '2019-09-01'
    dates = pd.date_range('2019-09-01', '2019-09-20', normalize=True)
    seat_info = seat_info[['ride_day', 'sname', 'tid', 'cid', 'bitmap']]
    seat_info['cid'] = seat_info['cid'].apply(lambda x: str(x))
    # seat_info['bitmap'] = seat_info['bitmap'].apply(lambda x: int(x,2))
    sqls = []
    for date in dates:
        date = date.strftime('%Y-%m-%d')
        print(date)
        seat_info['ride_day'] = date
        vlist = []
        for row in seat_info.iterrows():
            list = row[1].values.tolist()
            sql = 'insert into seat_info value'
            list[0] = "'" + list[0] + "'"
            list[1] = "'" + list[1] + "'"
            list[2] = "'" + list[2] + "'"
            sql += '('+','.join(list) + ')'
            cur.execute(sql)
            # vlist.append('('+','.join(row[1].values.tolist()) + ')')
        # sql += ','.join(vlist)
        # sqls.append(sql)
        # seat_info.to_csv('data/seat_info.csv', mode='a+', index=0)
        # cur.executemany('insert into seat_info values(%s,%s,%s,%s,%x)', seat_info.values.tolist())
        # cur.execute(sql)
        break

    # conn, cur = connDB()
    # for sql in sqls:
    #     cur.execute(sql)
    conn.commit()
    connClose(conn, cur)

# seat_info()
seat_info_insert()


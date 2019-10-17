import csv
import re
import pandas as pd
import time
import random
import numpy as np
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent

encoding = 'utf-8-sig'

station_url = 'https://www.12306.cn/index/script/core/common/station_name_v10036.js'

headers = {'Cookie': '',
           'Host': 'www.12306.cn',
           'Upgrade-Insecure-Requests': '1',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}

s = requests.session()
# s.keep_alive = False


def crawl_station_name():
    r = s.get(station_url, timeout=30)
    r.encoding = encoding
    # print(r.text)
    dic1 = dict(re.findall('@\w+\|([\u4e00-\u9fa5]+)\|([A-Z]+)', r.text))
    dic2 = {}
    with open('data/sname.txt', 'w+', encoding=encoding) as f:
        for key, value in dic1.items():
            f.write(key + '\t' + value + '\n')
            dic2[value] = key
    return dic1, dic2



def dispose_city(cname, location):
    if cname[-1] == '区':
        cname = re.match('(.+)市', location).group(1)
    return cname



def get_city_and_map():
    df = pd.read_excel('data\station_city.xlsx', names=['uid', 'sname', 'code', 'pinyin',
                                                        'abbr', 'city', 'location'])
    df['city'] = df.apply(lambda row: dispose_city(row['city'], row['location']), axis=1)
    s_c_dic = df.loc[:, ['sname', 'city']].set_index('sname').T.to_dict('list')
    print(s_c_dic)
    dic1, dic2 = read_sname()
    map_dic = {}
    for sname in dic1.keys():
        if sname in s_c_dic:
            map_dic[sname] = s_c_dic[sname]
        else:
            map_dic[sname] = ''
    pd.DataFrame.from_dict(map_dic, orient='index', columns=['city'])\
        .to_csv('data/sname_city.csv', encoding=encoding, header=None)


def get_city():
    df = pd.read_csv('data/sname_city.csv', names=['sname', 'city'], encoding=encoding)
    c_df = df.drop_duplicates(subset='city').loc[:,['city']]
    c_df.to_csv('data/city.csv', encoding=encoding, index=False, header=False)


data_table = []

ua = UserAgent()


# 12306爬取太慢，已弃用，改爬huochepiao网
def get_query_url(dic1, date, from_station, to_station):
    # 构建用于查询列车车次信息的url
    # 参数：日期，出发地，到达地
    # key为车站名称， value为车站代号

    date = date
    from_station = dic1[from_station]
    to_station = dic1[to_station]  # 新的url
    url = ("https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date={}"
           "&leftTicketDTO.from_station={}"
           "&leftTicketDTO.to_station={}"
           "&purpose_codes=ADULT"
           ).format(date, from_station, to_station)
    return url

# http_list = []
# https_list = []

def get_info(dic1, dic2, data, from_station, to_station, writer):
    while True:
        try:
            time.sleep(random.random() * 2)
            r = s.get(get_query_url(dic1, data, from_station, to_station),
                      headers={'User-Agent': ua.random}, timeout=5)
            trains = r.json()['data']['result']  # 获取所有车次信息for one_train in all_trains:  # 遍历取出每辆车的信息
            break
        except:
            print(from_station, to_station)
            time.sleep(random.random() * 5)
    for train in trains:
        data_list = train.split('|')
        train_number = data_list[3]  # 车次
        from_station_code = data_list[6]  # 出发站代号
        from_station_name = dic2[from_station_code]  # 出发站名称
        to_station_code = data_list[7]  # 到达站代号
        to_station_name = dic2[to_station_code]  # 到达站名称
        go_time = data_list[8]  # 出发时间
        arrive_time = data_list[9]  # 到达时间
        cost_time = data_list[10]  # 历时
        vip_seat = data_list[32] or '--'  # 商务/特等座
        first_class_seat = data_list[31] or '--'  # 一等座
        second_class_seat = data_list[30] or '--'  # 二等座
        vip_sleep = data_list[21] or '--' #高级软卧
        soft_sleep = data_list[23] or '--'  # 软卧
        mid_sleep = data_list[33] or '--' #动卧
        hard_sleep = data_list[28] or '--'  # 硬卧
        soft_seat = data_list[24] or '--' #软座
        hard_seat = data_list[29] or '--'  # 硬座
        no_seat = data_list[26] or '--'  # 无座
        print(train_number, from_station_code, from_station_name, to_station_code, to_station_name,
              go_time, arrive_time, cost_time, vip_seat, first_class_seat, second_class_seat,
              soft_sleep, hard_sleep, hard_seat, no_seat)
        writer.writerow([train_number, from_station_code, from_station_name, to_station_code, to_station_name,
                           go_time, arrive_time, cost_time, vip_seat, first_class_seat, second_class_seat,
                           vip_sleep, soft_sleep, mid_sleep, hard_sleep, soft_seat, hard_seat, no_seat])


date = '2019-09-25'


def read_sname():
    dic1, dic2 = {}, {}
    with open('data/sname.txt', 'r', encoding=encoding) as f:
        for line in f:
            pair = line.strip().split('\t')
            dic1[pair[0]] = pair[1]
            dic2[pair[1]] = pair[0]
    return dic1, dic2


def save():
    dic1, dic2 = read_sname()
    # with open('http_list.txt', 'r') as f:
    #     global http_list
    #     http_list = f.read().split('\n')
    # with open('https_list.txt', 'r') as f:
    #     global https_list
    #     https_list = f.read().split('\n')
    with open('data/data.csv', 'w+', newline='') as f:
        writer = csv.writer(f, encoding=encoding)
        for sname1 in dic1.keys():
            for sname2 in dic1.keys():
                if sname1 != sname2:
                    get_info(dic1, dic2, date, sname1, sname2, writer)
    # df = pd.DataFrame(data_table, columns=['tid', 'sno1', 'sname1', 'sno2', 'sname2',
    #                                        'go_time', 'arrive_time', 'cost_time',
    #                                        'vip_seat', 'c1_seat', 'c2_seat', 'soft_sleep', 'hard_sleep',
    #                                        'hard_seat', 'no_seat'])
    # df.to_csv('data/data.csv')


save()


# df = pd.read_csv('data/data.csv')
# get_city()

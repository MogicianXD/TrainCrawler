import csv
import json
import re
import pandas as pd
import time
import random
import numpy as np
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent
import chardet


encoding = 'utf-8-sig'

train_url = 'https://kyfw.12306.cn/otn/resources/js/query/train_list.js?scriptVersion=1.0'

s = requests.session()
# s.keep_alive = False

def get_train():
    r = s.get(train_url, timeout=30)
    r.encoding = 'utf-8'
    text = re.match('var train_list =(.+)', r.text).group(1)

    train_list = []
    content = json.loads(text).items()
    temp = []
    for item in content:
        dic = item[1]
        break
    with open('data/train.csv', 'w+', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['tid'])
        for list in dic.values():
            for dic_item in list:
                # train_list.append(re.match('(.+)\(', item['station_train_code']).group(1))
                writer.writerow([re.match('(.+)\(', dic_item['station_train_code']).group(1)])


columns = ['tid', 'sno', 'sname', 'arrv_time', 'depart_time', 'day', 'mileage']
pad_time = '-99:00'


def get_train_info(tid, writer):
    while True:
        try:
            r = s.get('http://search.huochepiao.com/chaxun/resultc.asp?txtCheci='+ str(tid) + '&cc.x=0&cc.y=0', timeout=20)
            r.encoding = 'gbk'
            soup = BeautifulSoup(r.text, 'html.parser')
            time.sleep(random.random() * 8)
            center = soup.find('center')
            tables = center.find_all('table')
            if len(tables) < 2:
                return
            for tr in tables[1].find_all('tr')[1:]:
                tds = tr.find_all('td')
                arrv_time = tds[3].string if re.match('\d', tds[3].string) else pad_time
                depart_time = tds[4].string if re.match('\d', tds[4].string) else pad_time
                info = [tid, tds[1].string, tds[2].string, arrv_time, depart_time, tds[7].string, tds[8].string]
                print(info)
                writer.writerow(info)
            break
        except:
            print(tid)
            time.sleep(20)


def get_trains_info():
    tids = pd.read_csv('data/train.csv')
    print(tids)
    with open('data/info.csv', 'w+', encoding=encoding, newline='') as fw:
        writer = csv.writer(fw)
        writer.writerow(columns)
        for row in tids.iterrows():
            tid = row[1].item()
            info = get_train_info(tid, writer)


def combine_time_and_day(time:str, day:int):
    return str(day-1) + ' ' + time


map_dic = {}
exclude = []


def calculate(group):
    i = 0
    for row in group[1].iterrows():
        value = row[1]
        if i == 0:
            pre_value = value
            i += 1
        else:
            key = (value['sname'], pre_value['sname'])
            if key not in map_dic and key[::-1] not in map_dic:
                distance = value['mileage'] - pre_value['mileage']
                if distance > 0:
                    map_dic[key] = distance
                else:
                    exclude.append(group[0])
                    return
            pre_value = value


def concat_day_and_time(day, time):
    if time == pad_time:
        return time
    else:
        return str(day) + ' ' + time


def extract():
    snames = pd.read_csv('data/sname_city.csv')['sname'].tolist()
    df = pd.read_csv('data/info.csv')
    df = df.drop_duplicates(subset=['tid', 'sno'])

    for group in df.groupby(['tid']):
        skip = False
        for sname in group[1]['sname'].tolist():
            if sname not in snames:
                skip = True
                exclude.append(group[0])
                break
        if not skip:
            calculate(group)

    df = df[~df['tid'].isin(exclude)]
    df['sno'] = df['sno'].apply(lambda x: x-1)
    df['day'] = df['day'].apply(lambda x: x - 1)
    df['arrv_time'] = df.apply(lambda row: concat_day_and_time(row['day'], row['arrv_time']), axis=1)
    df['depart_time'] = df.apply(lambda row: concat_day_and_time(row['day'], row['depart_time']), axis=1)
    df.iloc[:, 0:5].to_csv('data/via.csv', encoding=encoding, index=0)

    tids = df.drop_duplicates(subset='tid').loc[:, ['tid']]
    tids.to_csv('data/tid.csv', index=False)

    map_pd = pd.DataFrame.from_dict(map_dic, orient='index', columns=['mileage']).reset_index()
    map_pd = pd.concat([map_pd['index'].apply(pd.Series), map_pd['mileage']], axis=1)
    map_pd.columns = ['station_a', 'station_b', 'mileage']
    map_pd.to_csv('data/map.csv', encoding=encoding, index=0)



extract()
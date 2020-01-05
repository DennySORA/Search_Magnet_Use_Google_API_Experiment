# -*- coding:utf-8 -*-

import os
import re
import ast
import sys
import time
import json
import pprint
import urllib
import sqlite3
import requests
import subprocess


# =====================================================

Google_Search_Data = {
    'q': '',
    'c2coff': '0',
    'cx': "",
    'exactTerms': r'magnet:?',
    'filter': '1',
    'num': '10',
    'start': '1',
    'key': ''
}

# q 查詢
# c2coff 簡繁通用
# cx 收尋引擎
# exactTerms (內容要有的)關鍵字
# start 開始的頁數(第一頁、第二頁)
# num 回傳的數量
# filter 重複資料過濾
# excludeTerms 標識不應出現在搜索結果中的任何文檔中的單詞或短語
# hq AND功能
# orTerms (內容要有的)關鍵字

headers = {}

txts = ['歡迎使用Google search API', "此系統能幫你找到磁鐵連結", "系統尚未成熟"]

# ==============================
conn = sqlite3.connect('Google_Search_API_Magnet.sqlite')
cur = conn.cursor()
# ==============================
# ======================================================


def Init_Database():
    cur.executescript('''
    CREATE TABLE Main_Data (
        _id                     INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        Name                    TEXT UNIQUE,
        Create_Time             TEXT,
        Search_Time             INTEGER,
        Search_Total            INTEGER,
        Finish_URL_Index        BIT,
        Finish_Magnet_Index     BIT
    );
    
    CREATE TABLE Search_List (
        _id                     INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        Name                    TEXT UNIQUE,
        Input_Time              TEXT
    );

    CREATE TABLE URL_List (
        _id                     INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        Main_Link               INTEGER,
        URL                     TEXT,
        Search_Title            TEXT
    );

    CREATE TABLE Magnet_List (
        _id                     INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        URL_Link                INTEGER,
        Magnet                  TEXT,
        Magnet_Hash             TEXT UNIQUE,
        Status                  TEXT,
        Transfer_Time           TEXT,
        Finish_Transfer_Index   BIT
    );
    ''')
    return 'OK'
# ====================================================


def Get_Magnet(Input_Data):
    # =============================================

    count = 1
    # =============================================

    def Input_DB(URL_id, Status, Magnet_Data='Null'):
        if Magnet_Data != 'Null':
            try:
                Magnet_Hash = Magnet_Data.split(
                    ":")[3].split("&")[0].upper()
            except IndexError as e:
                print(e)
                return None
        else:
            Magnet_Hash = 'Null'
        try:
            if len(Magnet_Hash) == 40:
                cur.execute('''INSERT INTO Magnet_List (URL_Link,Magnet,Magnet_Hash,Status,Transfer_Time,Finish_Transfer_Index) VALUES (?,?,?,?,?,?) ''',
                            (URL_id, Magnet_Data, Magnet_Hash, Status, 0, 0))
        except sqlite3.IntegrityError as e:
            print(e, "\n此磁鐵以重複：", Magnet_Hash)

    # =============================================
    # ---------------------------------------------
    while True:
        Link_Data = Input_Data.get(str(count), None)
        if Link_Data == None:
            print("\n\n===========================完成==========================\n\n")
            return "OK"

        cur.execute('SELECT _id FROM URL_List WHERE URL = ? ',
                    (Link_Data.get('Link'), ))
        URL_id = cur.fetchone()[0]
        # --------------------------------------------
        print("目前處理的是第", count, '筆')
        print('\t\t標題為:', Link_Data.get('title'))
        print('\t\t鏈結為:', Link_Data.get('Link'))
        # --------------------------------------------

        if HTTP_lift(Link_Data.get('Link', None)) == None:
            print("-----------------失敗-----------------")
        else:
            # -------------------------------------------------------
            try:
                html = requests.get(url=Link_Data.get('Link'), headers=headers,
                                    timeout=10, verify=True)
            except:
                print("-----------------失敗-----------------")
                count += 1
                continue
            html.encoding = 'utf-8'
            # -------------------------------------------------------
            if html.text.find('CAPTCHA') == -1:
                Temp_Data = re.findall(
                    "magnet:\?xt[0-9A-Za-z.=&:;%+-]*", html.text)
                if Temp_Data == []:
                    print("-----------------無所需資料-----------------")
                else:
                    # --------------------------------------------
                    print("正在輸入資料庫\n請稍後")
                    for Magnet_Data in Temp_Data:
                        sys.stdout.write('#')
                        sys.stdout.flush()
                        Input_DB(URL_id, "GET", Magnet_Data)
                    # --------------------------------------------
                    print("-----------------以獲取-----------------")
                    pprint.pprint(Temp_Data)
                    print("----------------------------------------")
            else:
                Input_DB(URL_id, "CAPTCHA")
                print("-----------------需人工驗證-----------------")
        count += 1
        conn.commit()
        print("\n==================================================\n")

# =====================================================


def Transfer_CMD():
    Times = time.asctime(time.localtime(time.time()))
    Datas = [i for i in cur.execute(
        '''select _id,Magnet from Magnet_List  where Finish_Transfer_Index = 0;''')]
    Cho = input("使用哪一套BT下載軟體:\n\t1.µTorrent\n\t2.BitComet\n\t3.都使用\n\n\t請輸入：")
    Transfer_toto = input("\n請問要傳送幾筆：")

    count = 0
    for index, Trans in Datas:
        count += 1
        print("\n\t\t目前傳送的是第：", count, "筆資料\n", "\t\t序列編號為：", index)
        print("\nMagnet碼為：", Trans)
        sys.stdout.write("傳送中...")
        sys.stdout.flush()
        print("===============================================")
        if Cho == '1' or Cho == '3':
            subprocess.Popen(
                r"E:\BT\uTorrent\uTorrent.exe " + "\"" + Trans + "\"")
        elif Cho == '2' or Cho == '4':
            subprocess.Popen(
                "\"E:\\BT\\BitComet\\BitComet.exe\" --url " + "\"" + Trans + "\"" + " -s")
        else:
            print('選擇錯誤：', Cho)
            break
        cur.execute(
            '''update Magnet_List set Finish_Transfer_Index = 1 , Transfer_Time = (?)where _id = (?);''', (Times, index))
        sys.stdout.write("\r")
        print("=======傳送完成=======\n")
        sys.stdout.write("========休息中==========")
        sys.stdout.flush()
        conn.commit()
        time.sleep(2)
        sys.stdout.write("\r")
        print("                          ")
        if count >= int(Transfer_toto):
            if Cho == '3':
                Cho = '4'
                count = 0
            else:
                break
    return "OK"
# =====================================================


def batch():
    if not os.path.exists(".\\data"):
        os.mkdir(".\\data")
    if not os.path.isfile(".\\data\\Search_List.txt"):
        return None
    Search_List = open('.\\data\\Search_List.txt', 'r',
                       encoding='utf-8').read().split("\n")
    count = input("請說入收尋深度:")
    for name in Search_List:
        if name != '' and name != [] and name != None:
            print("收尋資料為", name)
            try:
                Times = time.asctime(time.localtime(time.time()))
                cur.execute(
                    '''INSERT INTO Search_List (Name,Input_Time) VALUES ( ?,?) ''', (name, Times))
                conn.commit()
                if Get_Range(name, int(count)) == None:
                    cur.execute(
                        'DELETE FROM Search_List WHERE Name = ? ', (name,))
                    conn.commit()
                    return None
            except sqlite3.IntegrityError as e:
                print(e, "\n\n以收尋過：", name)

    print("總共有：", len(Search_List), "筆資料")
    return "OK"
# =====================================================


def Json_Resolve(Input_Data, count, Json_Datas):
    Output_Data = dict()
    try:
        if Json_Datas == dict():
            Json_Datas['Search_Total'] = 0
        # ============================================
        Json_data = json.loads(Input_Data)
        Output_Data['Search_Time'] = Json_data['searchInformation']['searchTime']
        Output_Data['Search_Total'] = str(int(
            Json_data['searchInformation']['totalResults']) + int(Json_Datas['Search_Total']))
        # ============================================
        print("資料收尋時間：", Output_Data['Search_Time'])
        print("資料收尋數量：", Output_Data['Search_Total'])
        print("擷取中")
    except:
        print(Json_data)
        os.system("PAUSE")
        return None, None, None
    # ============================================
    try:
        for Items_Data in Json_data['items']:
            sys.stdout.write('#')
            sys.stdout.flush()
            Output_Data[str(count)] = dict()
            Output_Data[str(count)]['title'] = Items_Data['title']
            Output_Data[str(count)]['Link'] = Items_Data['link']
            count += 1
        print("\n完成\n")
        time.sleep(5)
        if count <= 10:
            return Output_Data, 0, count
        else:
            return Output_Data, 1, count
    except:
        print(Json_data)
        time.sleep(60)
        return Output_Data, 0, count

# =====================================================


def HTTP_lift(url):
    count = 0
    try:
        html = requests.get(url=url, headers=headers,
                            timeout=10, verify=True)
        return "OK"
    except requests.exceptions.HTTPError as e:
        print(e)
        return None
    except:
        return None

# =====================================================


def Get_Range(name, count):
    Json_Data = dict()
    # ---------------------------------------
    Google_Search_Data['q'] = name
    for start in range(1, count * 10, 10):
        print("Google 收尋深度第：", start)
        # -------------------------------
        Google_Search_Data['start'] = start
        url = 'https://www.googleapis.com/customsearch/v1?' + \
            urllib.parse.urlencode(Google_Search_Data)
        html = requests.get(url=url, headers=headers, timeout=10, verify=True)
        html.encoding = 'utf-8'
        Data_Temp, index, Quantity = Json_Resolve(html.text, start, Json_Data)
        if Data_Temp == None and index == None:
            return None
        Json_Data = dict(Json_Data, ** Data_Temp)
        if index == 0:
            break
    print("------------------------完成Google收尋------------------------")

    # ----------------------------------------
    Times = time.asctime(time.localtime(time.time()))
    cur.execute(
        '''INSERT INTO Main_Data (Name,Create_Time,Search_Time,Search_Total,Finish_URL_Index,Finish_Magnet_Index) VALUES ( ?,?,?,?,?,?) ''', (name, Times, Json_Data['Search_Time'], Json_Data['Search_Total'], 0, 0))
    cur.execute('SELECT _id FROM Main_Data WHERE Name = ? ', (name, ))
    Main_id = cur.fetchone()[0]
    # ----------------------------------------
    print("正在輸入資料庫\n請稍後")
    for count in range(1, Quantity):
        sys.stdout.write('#')
        sys.stdout.flush()
        try:
            cur.execute('''INSERT INTO URL_List (Main_Link,URL,Search_Title) VALUES ( ?,?,?) ''',
                        (Main_id, Json_Data[str(count)]['Link'], Json_Data[str(count)]['title']))
        except KeyError as e:
            print(e)
    # ----------------------------------------
    cur.execute(
        '''UPDATE Main_Data  SET (Finish_URL_Index) = ? where _id = ?''', (1, Main_id))
    conn.commit()

    print("\n完成資料庫輸入===============\n\n")

    Get_Magnet(Json_Data)
    cur.execute(
        '''UPDATE Main_Data  SET (Finish_Magnet_Index) = ? where _id = ?''', (1, Main_id))
    conn.commit()
    return "OK"
    # ----------------------------------------

# =============================================================
# =============================================================


def display():
    for txt in txts:
        print(txt)
    os.system("PAUSE && cls")
    print("================模式選擇================\n")
    print("選擇1:\n\t一般單一收尋\n-------------------------")
    print("選擇2:\n\t批量收尋\n-----------------------------")
    print("選擇3:\n\t批量傳送下載\n--------------------------")

# =============================================================


def main():
    display()
    try:
        Hash_Data = [Get_Data[0] for Get_Data in cur.execute(
            '''SELECT Magnet_Hash FROM Magnet_List;''')]
    except sqlite3.OperationalError:
        Init_Database()
    # =========================================
    Cho = input("\t\t請輸入模式:")
    if Cho == "1":
        name = input("請輸入要收尋的名稱：")
        count = input("請輸入收尋深度：")
        Get_Range(name, int(count))
    elif Cho == "2":
        if batch() == None:
            print("已結束==============")
        else:
            print("全部收尋完成========")
    elif Cho == "3":
        Transfer_CMD()
    else:
        return None
    print("-----------------------finish----------------------")
    os.system("PAUSE")

# =====================================================
# =====================================================
# =====================================================


if __name__ == '__main__':
    main()

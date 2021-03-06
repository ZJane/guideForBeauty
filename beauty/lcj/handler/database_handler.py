#!/usr/bin/python
# -*- coding:utf-8 -*-
from gensim.models import word2vec
from operator import itemgetter
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core import serializers
import pymysql
import jieba
import json
import copy


#获取应该去哪些数据库表中查询
def get_tables_and_keywords(keyword):
    if keyword.find('唇')>=0 or keyword.find('口')>=0 or keyword.find('嘴')>=0:
        tables = ['product_lipstick']
    elif keyword.find('眼')>=0 or keyword.find('睫毛')>=0 or keyword.find('眉')>=0:
        tables = ['product_eye']
    elif keyword.find('香水')>=0:
        tables = ['product_perfume','product_other_perfume']
    else:
        tables = ['product_baseMakeup']

    #获取需要模糊匹配的单词
    temp = list(jieba.cut(keyword))
    keywords = []
    for i in temp:
        keywords.append('%'+i+'%')
    return tables,keywords

def get_other_tables(tables):
    kinds = ['product_lipstick','product_eye','product_perfume', 'product_baseMakeup','product_other_perfume']
    for i in tables:
        kinds.remove(i)
    return kinds

def execute_sql(sql,data):
    try:
        db = pymysql.connect(host="39.108.185.66", user="root", password="1234", db="beautyGirls_database", port=3306,
                             charset="utf8")
        cur = db.cursor()  # 获取操作游标
        cur.execute(sql,data)  # 执行sql语句
        results = cur.fetchall()  # 获取查询的所有记录
        if len(results) <= 0:
            print("no such items in this table")
        return results
    except Exception as err:
        print("handler err:"+str(err))
        return []
    finally:
        db.close()  # 关闭连接

def handle_sql_results(tables,keywords,page_no):
    #获取需要进行查询的sql语句
    sql_list = []
    for i in tables:
        sql = 'select name,price,img1_address,address,good_comment_percentage,comment_count,platform,description from '+i+' where description like %s'
        for j in range(len(keywords)-1):
            sql = sql+' and description like %s'
        sql_list.append(sql)

    #进行sql查询并处理查询结果
    all_list = []
    for i in sql_list:
        temp = list(execute_sql(i,keywords))
        if len(temp)==0:
            continue
        for j in temp:
            item = list(j)
            comment_num = item[5]
            index = comment_num.find('万')
            if index>0:
                item[5] = float(comment_num[0:index])*10000
            else:
                index = comment_num.find('+')
                if index>0:
                    item[5] = float(comment_num[0:index])
                else:
                    item[5] = float(comment_num)
            all_list.append(item)

    if len(all_list) ==0:
        result = {}
        result['count'] = 0
        result['page_count'] = 0
        return result

    all_list.sort(key=itemgetter(5,4), reverse=True)

    result = {}
    count = 0
    start = (page_no-1)*20
    for i in range(start,start+20):
        if(i<len(all_list)):
            temp = {}
            temp["name"] = all_list[i][0]
            temp["price"] = float(all_list[i][1])
            temp["img1_address"] = all_list[i][2]
            temp["address"] = all_list[i][3]
            # if all_list[i][4].find('%')<=0:
            #     temp["good_comment_percentage"] = all_list[i][4]+'%'
            # else:
            temp["good_comment_percentage"] = all_list[i][4]
            temp["comment_count"] = int(all_list[i][5])
            temp["platform"] = all_list[i][6]
            temp["description"] = all_list[i][7]
            result[str(count)] = temp
            count += 1

    result['count'] = count
    page_count = int(len(all_list)/20)
    if len(all_list)%20>0 :
        page_count +=1
    result['page_count'] = page_count

    return result

def get_products_page(keyword,page_no):
    result = get_tables_and_keywords(keyword)
    tables = result[0]
    keywords = result[1]
    result = handle_sql_results(tables, keywords, page_no)
    # print(result)
    lenght = int(result['count'])
    page_count = int(result['page_count'])
    print(lenght,page_count)

    if lenght > 0:
        pass
        # for i in range(0, lenght):
        #         print(result[str(i)])
    elif page_count==0:
        tables = get_other_tables(tables)
        result = json.loads(handle_sql_results(tables, keywords, page_no))
        lenght = int(result['count'])
        page_count = int(result['page_count'])
        # print(result)
        # print(lenght, page_count)
        if lenght > 0:
            for i in range(0, lenght):
                print(result[str(i)])

    # print(result)
    return result


@require_http_methods(["GET"])
def handle_search(request):
    if request.method == 'GET':
        keywords = request.GET.get('searchKeyWords')
        page_no = request.GET.get('PageNo')
        # print (request)
        print (keywords,page_no)
        results = get_products_page(keywords,int(page_no))
        print (results)
        return JsonResponse(results,safe=False)

if __name__ == '__main__':
    # http://127.0.0.1:8000/productsList/getProductsPage?searchKeyWords=美宝莲唇彩&PageNo=1
    keyword = '卡姿兰蜗牛气垫调控霜'
    # keyword = '女士淡香'
    page_no = 4
    get_products_page(keyword,page_no)








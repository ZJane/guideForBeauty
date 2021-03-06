#!/usr/bin/python
# -*- coding:utf-8 -*-
import codecs
import json
import re
import requests
import urllib
import urllib.request
import chardet
import jieba
import random
import os

from BeautifulGirls.lcj.spider import proxy_ip

class Spider:
    PROXY = {}

    #爬取页面的信息，返回的是HTML格式的信息
    def get_html(self,url):
        try:
            #1.创建一个代理处理器ProxyHandler
            proxy_support = urllib.request.ProxyHandler(self.PROXY)
            #2.创建和定制一个opener
            opener = urllib.request.build_opener(proxy_support)
            opener.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0")]
            #3.安装和使用opener
            urllib.request.install_opener(opener)
            response = urllib.request.urlopen(url).read()

            # 获取页面的编码方式，然后才可以根据编码方式进行解码
            charset = chardet.detect(response)
            encoding = charset['encoding']
            # 根据页面编码方式进行解码，不然会乱码
            html_data = response.decode(encoding, 'ignore')
        except Exception as err:
            self.PROXY = proxy_ip.get_proxy()
            print("fail to get html data,err:"+str(err))
            return -1
        return html_data

    #获取每个商品的评论
    def get_comments(self,file_path,sku):
        s = requests.session()
        url = 'https://club.jd.com/comment/productPageComments.action'
        data = {
            'callback': 'fetchJSON_comment98vv13933',
            'productId': sku,
            'score': 0,
            'sortType': 5,  # 评论按照什么排序：推荐排序和时间排序，默认5
            'page': 0,  # 当前是第几页评论，从0开始递增
            'pageSize': 10,  # 指定每一页展示多少评论，默认10
            'isShadowSku': 0,
            'fold': 1
        }
        item_file = codecs.open(file_path + 'item_comments/'+sku + '.txt', 'w', encoding='utf-8')
        all_file = codecs.open(file_path+ 'solved_comments/all_comments.txt', 'a', encoding='utf-8')
        # pos_file = codecs.open(filePath + '/solved_comments/positive.txt', 'a', encoding='utf-8')
        # neg_file = codecs.open(filePath + '/solved_comments/negative.txt', 'a', encoding='utf-8')
        cut_file = codecs.open(file_path + 'solved_comments/cut_stop_words.txt', 'a', encoding='utf-8')
        jieba.analyse.set_stop_words(file_path + 'procedure_files/stop_words.txt')  # 去除停用词
        try:
            while True:
                t = s.get(url, params=data).text
                try:
                    t = re.search(r'(?<=fetchJSON_comment98vv13933\().*(?=\);)', t).group(0) #fetchJSON_comment98vv13933(t的结果就是这里的内容)
                except Exception as e:
                    print("no more page:"+str(e))
                    break
                j = json.loads(t)
                # print(j)
                comment_summary = j['comments']
                if comment_summary is None:
                    break
                for comment in comment_summary:
                    c_content = comment['content']  # 评论
                    score = comment['score']
                    # if score > 4:
                    #     pos_file.write(c_content + '\n')
                    # if score <= 3:
                    #     neg_file.write(c_content + '\n')
                    all_file.write(c_content+'\n')
                    item_file.write(c_content + '\n')
                    cut_file.write(' '.join(jieba.cut(c_content)))
                data['page'] += 1
                page = data['page']
                print('comment page:'+str(page))
                if page>=100:
                    break
        except Exception as e:
            print(e)
            return -1
        finally:
            item_file.close()
            all_file.close()
            # pos_file.close()
            # neg_file.close()
            cut_file.close()

    # 获取商品的价格
    def get_price(self,sku):
        try:
            url = "https://p.3.cn/prices/mgets?skuIds=J_" + sku
            proxy_support = urllib.request.ProxyHandler(self.PROXY)
            opener = urllib.request.build_opener(proxy_support)
            opener.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0")]
            urllib.request.install_opener(opener)
            hjson = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))
            return float(hjson[0]['op'])
        except Exception as err:
            self.PROXY = proxy_ip.get_proxy()
            print('fail to get price,err:'+str(err))
            return -1

    def get_rate(self,file_path,sku):
        s = requests.session()
        url = 'https://club.jd.com/comment/productPageComments.action'
        data = {
            'callback': 'fetchJSON_comment98vv13933',
            'productId': sku,
            'score': 0,
            'sortType': 5,  # 评论按照什么排序：推荐排序和时间排序，默认5
            'page': 0,  # 当前是第几页评论，从0开始递增
            'pageSize': 10,  # 指定每一页展示多少评论，默认10
            'isShadowSku': 0,
            'fold': 1
        }
        sku_file = codecs.open(file_path + 'procedure_files/sloved_skus.txt', 'a', encoding='utf-8')
        rate_file = codecs.open(file_path + 'procedure_files/rate.txt', 'a', encoding='utf-8')
        try:
                t = s.get(url, params=data).text
                try:
                    t = re.search(r'(?<=fetchJSON_comment98vv13933\().*(?=\);)', t).group(0)  # fetchJSON_comment98vv13933(t的结果就是这里的内容)
                except Exception as e:
                    print("no more page:" + str(e))
                j = json.loads(t)
                # print(j)
                comment_summary = j['productCommentSummary']
                good_rate = float(comment_summary['goodRate'])
                poor_rate = float(comment_summary['poorRate'])
                comment_count = int(comment_summary['commentCount'])
                list = []
                list.append(sku)
                list.append(good_rate)
                list.append(poor_rate)
                list.append(comment_count)
                list = str(list)
                print(list)
                rate_file.write(list + '\n')
                sku_file.write(sku + '\n')
        except Exception as e:
            print(e)
            return -1
        finally:
            sku_file.close()
            rate_file.close()
            return 1

    def get_proxy_ip(self):
        proxy_ip_list = [
            {'https': '119.5.1.16:808'},
            {'https': '180.119.65.112:808'},
            {'http': '111.155.116.216:8123'}
        ]
        self.PROXY = random.choice(proxy_ip_list)

def getSpider():
    spider = Spider()
    spider.PROXY = {'http': '61.135.217.7:80'}
    # spider.PROXY = {'http': '119.5.1.22:808'}
    # spider.PROXY = {'http': '171.37.156.184:8123'}
    return spider

if __name__== '__main__':
    file_path = ( os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath("jd_search_product.py")))) + '/data/').replace('\\', '/')
    spider = Spider()
    # spider.get_comments( file_path, "1592994")
    spider.get_rate(file_path, '14102602376')
    spider.get_rate(file_path, '12582916863')

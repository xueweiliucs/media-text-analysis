
# coding: utf-8

# In[21]:


import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from bs4 import UnicodeDammit
from selenium import webdriver

#纽约时报的网站里，并没有历史报道的目录，也就是说不可能通过Linkcrawler遍历
#没有按时间排序的目录，除了通过站内搜索引擎，搜索关键词并按时间查找外没有其他的办法
#搜索结果页面要模拟click“show more"(查看更多)才能看更多搜索结果
#所幸没有会员也可以在源码中查看内容。似乎找到了一条盗版之路。

#全局变量，链接列表，集合自动去重
news_link_lists = set()
global news_link_lists

#获取搜索结果链接列表的函数
def crawler(queryStr,startDate,endDate):
    searchUrl = "https://www.nytimes.com/search?endDate="+endDate+"&query="+queryStr+"&sort=oldest&startDate="+startDate
    #此处仅能使用firefox，如果安装chrome可以改成webdriver.Chrome(),会弹出浏览器窗口，
    #如果不想弹出窗口可以使用headless参数
    driver = webdriver.Firefox()
    driver.get(searchUrl)
    
    #循环模拟点击
    while(True):
        element = driver.find_element_by_css_selector("div.Search-showMore--Plid0 button")
        element.click()
        #没有这个停顿就是一开始失败的原因
        time.sleep(3)
        bsObj = BeautifulSoup(driver.page_source,"lxml")
        #判断是否出现有“show more”按钮
        if not bsObj.find('div',attrs={"class":'Search-showMore--Plid0'}):
            break
    #解析页面，获取搜索结果        
    bsObj = BeautifulSoup(driver.page_source,"lxml")
    searchresult = bsObj.find("div",attrs={"class":'SearchResults-main--3t9sI'})
    links_list = searchresult.find("ol")
    links = links_list.findAll("a")
    for link in links:  
        #表达式匹配，虽然是正则模块但是没有用正则
        m = re.match("http",link.attrs['href'])
        if m:
            #如果链接呈现绝对链接形式 如https://www.nytimes.com/2018/05/27/us/politics/ 
            newPage = link.attrs['href']
        else:
            #如果链接呈现相对链接形式：/2018/05/27/us/politics/ 
            newPage = "https://www.nytimes.com"+link.attrs['href']
            
        #添加新链接至链接列表
        news_link_lists.add(newPage)
        print(newPage)
        


#request，解析，存储的函数
def parse(news_link_lists, filename):
    news=[]
    
    #不一定非要转换成list，此处是方便排序
    news_link_lists = list(news_link_lists)
    news_link_lists.sort()
    for d in news_link_lists:
        #打印链接
        print(d)

        #关闭会话多线程，防止出现http错误
        s = requests.session()
        s.keep_alive = False
        #request 获取 beautifulsoup解析
        web_data = requests.get(d)
        #encodong是防止乱码的关键
        web_data.encoding = 'utf-8' 
        soup = BeautifulSoup(web_data.text,"lxml")
        requests.adapters.DEFAULT_RETRIES = 5


        new={}
        a = ""

        #因为文章页面大致有三种类型，并不一致，所以有三种选择文章内容的选择器
        if (soup.find('p',attrs={"class":['story-content','story-body-text']})):
            shits = soup.findAll('p',attrs={"class":['story-content','story-body-text']})
        else:
            shits = soup.findAll('p',attrs={"itemprop":"articleBody"})
        #获取每个p中的内容，加在一起
        for shit in shits:
            a = a + shit.get_text().strip()+" \n"
        #对每一个key赋值。
        new['content'] = a
        new['link'] = d
        new['time'] = soup.find(attrs={"class":"dateline"}).get_text().strip()
        new['title'] = soup.find('h1').get_text().strip()
        news.append(new)
        time.sleep(3)
    #存储为csv
    df = pd.DataFrame(news)
    df.to_csv(filename,index=False,encoding="utf-8")
    #结束
    print('complete')



#两种关键词的检索
crawler("davos forum china","20050101","20101231")
crawler("davos forum chinese","20050101","20101231")
#得到所有文章链接
len(news_link_lists)
#解析并存储到路径内文件名
parse(news_link_lists,'Desktop/news-nytimes.csv')


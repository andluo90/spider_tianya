# -*- coding: utf8 -*-

import urllib2,json,time,re
from docx import Document
from docx.shared import Inches
import sys,socket,pickle,os


# http://bbs.tianya.cn/post-no05-305785-1.shtml

#楼主主贴
headers = {'Referer':'http://www.tianya.cn/2213624/bbs?t=post','User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'}

def get_all_urls():
    next_id = '2147483647'
    url_list = []
    date_list = []
    for index in range(0,19):
        print index+1
        louzu_url = 'http://www.tianya.cn/api/tw?me' \
            'thod=userinfo.ice.getUserTotalArti' \
            'cleList&params.userId=2213624&params.' \
            'pageSize=20&params.bMore=true&params.publ' \
            'icNextId=%s&params.techNextId=2147483647&params.cityNextId=2147483647' %next_id
        resquest = urllib2.Request(louzu_url,headers=headers)
        rep = urllib2.urlopen(resquest)
        date_json = json.load(rep)
        if date_json['success'] == '1':
            date_list.append(date_json)
            next_id = date_json['data']['public_next_id']
            print next_id
        time.sleep(3)

    for date_json in date_list:
        if date_json['success'] == '1':
            for row in date_json['data']['rows']:
                print 'http://bbs.tianya.cn/post-%s-%s-1.shtml' %(row['item'],row['art_id'])
                url_list.append('http://bbs.tianya.cn/post-%s-%s-1.shtml' %(row['item'],row['art_id']))

def get_all_page(index_url):
    "获取此贴的所有页面保存到本地"

    try:
        req = urllib2.Request(index_url, headers=headers)
        html = urllib2.urlopen(req,timeout=120).read()
        if html is None:sys.exit('获取不到首页内容')
        #获取基本信息
        global host,page_len,title,d_value
        d_value = set([])
        host = getHost(html)
        page_len = getPageLen(html)
        title = getTitle(html)

        print '基础信息获取成功...'

        html_list = os.listdir('./html')
        if len(html_list) != page_len:
            local_html_set = set([int(html[:-6]) for html in html_list])
            all_html_set = set(range(1,page_len+1))
            d_value =  all_html_set - local_html_set

            for i in d_value:
                try:
                    url = 'http://bbs.tianya.cn/post-no05-305785-'+str(i)+'.shtml'
                    req = urllib2.Request(url,headers=headers)
                    html = urllib2.urlopen(req).read()
                    file_name = './html/%d.shtml' %i
                    with open(file_name,'wb') as f:
                        f.write(html)
                    time.sleep(5)
                except urllib2.URLError:
                    print 'get %s raise a error' %url
                except IOError:
                    print 'write the %s raise a error' %file_name


    except urllib2.URLError,e:
        print 'URLError'
        print e
    except socket.error:
        print 'socket error...'



def getMainContent():
    "获取主贴内容，默认为本地1开头的第一个shtml"
    #if len(d_value) == 0 : return

    with open('./html/1.shtml','rb') as f:
        html = f.read()
    res = re.findall(r'<div class="bbs-content clearfix">(.*?)</div>',html,re.S)

    if not len(res):
        sys.exit('楼主主贴没有获取到内容...')
    elif len(res) > 1:
        sys.eixt('楼主主贴获取的内容超过一个...')
    global _main_body
    with open('./txt/temp.txt','wb') as f:
        #f.write(formatHtml(res[0]))
        f.write(res[0])
    with open('./txt/mainContent.txt','wb') as f:
        with open('./txt/temp.txt','rb') as f2:
            for line in f2:
                f.write(formatHtml(line))





def getComment():
    "获取楼主的评论"

    html_list = os.listdir('./html')
    with open('./txt/comment.txt','wb+') as f2:

        for html in d_value:
            file_name = './html/%s.shtml' %html
            with open(file_name,'rb') as f:
                html = f.read()
            comment_regx = r'<div class="atl-item" _host="%s".*?<div class="bbs-content">(.*?)</div>' %host
            res = re.findall(comment_regx,html,re.S)
            if len(res):
                for comment in res:
                    comment = formatHtml(comment)
                    f2.write(comment)




def saveImg(img_url):
    "保存图片在当前项目下，默认图片名为demo"
    url = re.findall(r'http.*\.[a-z]{3}',img_url)
    img_name = re.findall(r'http:.*m/([0-9]+)',img_url)
    form = url[0][-3:]
    img_name_complete = img_name[0]+'.'+form

    img_list = os.listdir('./img')
    if img_name_complete in img_list : return img_name_complete

    try:
        req = urllib2.Request(url[0],headers=headers)
        rsp = urllib2.urlopen(req).read()

        with open('./img/'+img_name_complete,'wb') as f:
            f.write(rsp)
        return img_name_complete
    except urllib2.URLError:
        return 0

def save2Word():
    file_name = title+'.docx'


    with open('./txt/mainContent.txt','a') as f1:
        with open('./txt/comment.txt','rb') as f2:
            f1.write(f2.read())

    with open('./txt/mainContent.txt','rb') as article_complete:

        document = Document()

        for line in article_complete:
            if 'http://img3' in line:
                line.strip()
                imgName = saveImg(line)
                if not imgName:
                    document.add_picture('./img'+imgName, width=Inches(4.25))
                else:
                    document.add_paragraph(u'图片加载失败....')
                    document.add_paragraph(line.decode('UTF-8'))
            else:
                document.add_paragraph(line.decode('UTF-8'))
        document.save(file_name.decode('UTF-8'))


def formatHtml(line):

    line = line.replace('<br>','') #去掉<br>标签
    line = re.sub(r'<img src="http://static.*?original="','',line)
    line = line.replace('<img src="http://img3','http://img3')
    line = line.replace('" />','')

    line = line.replace('\t','') #去掉\t
    line = line.lstrip()
    if line == '\n' : line = ''
    return line


def getHost(html):
    "获取楼主host"
    res = re.findall(r'<div class="atl-item host-item" _host="(.*?)">',html,re.S)
    if not len(res):
        sys.exit('获取不到楼主的host')
    elif len(res) > 1:
        sys.exit('楼主的host不是唯一')
    return res[0]

def getPageLen(html):
    #获取贴子的总页数
    res = re.findall(r'return goPage\(this,.*,(.*?)\);">',html,re.S)
    if not len(res):
        sys.exit('没有获取到总页数')
    elif len(res) > 1:
        sys.exit('获取到%s个总页面'%len(res))
    return int(res[0])

def getTitle(html):
    title = re.findall(r'<h1 class="atl-title">(.*?)</h1>',html,re.S)
    if len(title) != 1:sys.exit('获取标题有误。。。')
    title = re.sub(r'<[^>]+>','',title[0]).strip()
    return title

def run():
    "运行脚本"
    print '请输入要获取的天涯贴子的第一页...'
    while False:
        input_url = raw_input()
        input_url = input_url.strip().lower()
        if input_url == 'q':sys.exit('退出成功.')
        result = re.findall(r'^http://.*html$',input_url)
        if len(result) != 1:
            print '地址格式不正确，请重新输入...或按 q 退出.'
        else:
            break
    dir_list = os.listdir('./')
    if 'html' not in dir_list:os.mkdir('./html')
    get_all_page('http://bbs.tianya.cn/post-no05-305785-1.shtml')
    getMainContent()
    getComment()
    save2Word()


if __name__ == '__main__':
    run()
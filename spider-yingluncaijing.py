import json
from os import makedirs
from os.path import exists
import requests
import logging
from urllib.parse import urljoin
import cloudscraper
import multiprocessing
from lxml import etree

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')

BASE_URL = 'https://cn.investing.com/news/cryptocurrency-news'
PRO_BASE_URL = 'https://cn.investing.com/'
TOTAL_PAGE = 3

RESULTS_DIR = 'results'
exists(RESULTS_DIR) or makedirs(RESULTS_DIR)


def scrape_page(url):
    try:
        # 获取页面的内容
        # response = requests.get(url)
        # 制裁Cloudflare的反爬虫机制制裁
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        response = scraper.get(url)
        if response.status_code == 200:
            return response.text
        logging.error('get invalid status code %s while scraping %s',
                      response.status_code, url)
    except requests.RequestException:
        logging.error('error occurred while scraping %s', url, exc_info=True)


def scrape_index(page):
    """
    scrape index page and return its html
    :param page: page of index page
    :return: html of index page
    """
    index_url = f'{BASE_URL}/{page}'
    return scrape_page(index_url)


def parse_index(html):
    h = etree.HTML(html)
    # 获取标题内容
    # result = h.xpath('//section[@id="leftColumn"]//div[@class="textDiv"]//a[@class="title"]//text()')
    # #print(result)
    # 获取超链接里面的内容 获取内容详情
    detail_urls = h.xpath('//section[@id="leftColumn"]//div[@class="textDiv"]//a//@href')
    print(type(detail_urls))
    score = []
    # 取出包含有comments的内容
    for item in detail_urls:
        comments_a = "comments" not in item
        if comments_a:
            score.append(item)
    for url in score:
        detail_url = urljoin(PRO_BASE_URL, url)
        logging.info('get detail url %s', detail_url)
        yield detail_url  # 返回一个经过处理的detail_url 集合

    # for item in detail_urls:
    #     # # 如果
    #     # result = "comments" in item
    #     # if result:
    #     #     break
    #     detail_url = urljoin(PRO_BASE_URL, item)
    #     logging.info('get detail url %s', detail_url)
    #     yield detail_url
    # 分割字符串
    # last_url = ""
    # print(detail_url)
    # last_url+=detail_url.split('/')[3]
    # print(last_url)


def scrape_detail(url):
    """
    scrape detail page and return its html
    :param url:
    :param page: page of detail page
    :return: html of detail page
    """
    return scrape_page(url)


def save_data(data):
    """
    save to json file
    :param data:
    :return:
    """
    name = data.get('title')
    print(name)
    data_path = f'{RESULTS_DIR}/{name}.json'
    json.dump(data, open(data_path, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)


# 获取文本里面的内容
def parse_detail(detail_html):
    h = etree.HTML(detail_html)
    # 获取文本标题
    get_title = h.xpath('//h1[@class="articleHeader"]/text()')

    #获取时间
    get_time = h.xpath('//div[@class="contentSectionDetails"]/span/text()')

    # contains 表示属性多值选择器
    # 获取文本内容
    content_text = h.xpath('//div[contains(@class,"WYSIWYG")]/p//text()')

    return {
        'title': get_title,
        'time' : get_time,
        'text' : content_text
    }


# def main():
#     # 获取主页的内容
#     for page in range(0, 1+3):
#         index_html = scrape_index(page)
#         # 解析主页的内容 获取到主页列表的所有详情页
#         detail_urls = parse_index(index_html)
#     for detail_url in detail_urls:
#         # 解析单个详情页内容
#         detail_html = scrape_detail(detail_url)
#         data = parse_detail(detail_html)
#         # logging.info('get detail data %s', data)
#         # logging.info('saving data to json file')
#         # 保存内容
#         print(data)
#         save_data(data)
#         logging.info('data saved successfully')


def main(page):
    index_html = scrape_index(page)
    detail_urls = parse_index(index_html)
    for detail_url in detail_urls:
        detail_html = scrape_detail(detail_url)
        data = parse_detail(detail_html)
        # logging.info('get detail data %s', data)
        # logging.info('saving data to mongodb')
        print(data)
        save_data(data)
        logging.info('data saved successfully')


if __name__ == '__main__':
    pool = multiprocessing.Pool()
    pages = range(1, TOTAL_PAGE + 1)
    # pages 为 1-11   pool.map 表示 main是调用的方法，pages需要遍历的页码 既1-11
    pool.map(main, pages)
    pool.close()
    pool.join()

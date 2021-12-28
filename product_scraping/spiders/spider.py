import scrapy
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
import json
import random
import re
from product_scraping.items import Product
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class CaWalmartBot(scrapy.Spider):
    name = 'ca_walmart'
    allowed_domains = ['walmart.ca']
    # start_urls = ['https://www.walmart.ca/en/grocery/fruits-vegetables/fruits/N-3852']
    header = {
        'Host': 'www.walmart.ca',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive'
    }

    def request_products_page(self, url):
        return SeleniumRequest(url=url, callback=self.parse, wait_until=EC.any_of(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@data-automation=\'product\']')),
            EC.presence_of_all_elements_located((By.XPATH, '//div[@data-automation=\'grocery-product\']'))
        ), wait_time=30.0)


    def start_requests(self):
        start_urls = [
            'https://www.walmart.ca/en/grocery/fruits-vegetables/fruits/N-3852'
        ]

        for url in start_urls:
            yield self.request_products_page(url)

    def parse(self, response):
        prod_link_extractor = LxmlLinkExtractor(restrict_xpaths=[
            '//div[@data-automation=\'product\']/a[1]',
            '//div[@data-automation=\'grocery-product\']/a[1]'
        ])

        prod_links = prod_link_extractor.extract_links(response)
        random.shuffle(prod_links)
        for prod_link in prod_links:
            url = prod_link.url
            yield SeleniumRequest(url=url, callback=self.parse_html, cb_kwargs={'url': url})
        
        next_link_extractor = LxmlLinkExtractor(restrict_xpaths=[
            '//div[@data-automation=\'pagination-root\']/*/a[text()=\'Next\']'
        ])
        next_links = next_link_extractor.extract_links(response)

        if len(next_links) > 0:
            url = next_links[0].url
            yield self.request_products_page(url)

    def parse_html(self, response, url):

        item = Product()
        # branches = {'3106': ['43.656422', '-79.435567'], '3124': ['48.412997', '-89.239717']}

        # gral_dict = json.loads(re.findall(r'(\{.*\})', response.xpath("/html/body/script[1]/text()").get())[0])
        # prod_dict = json.loads(response.css('.evlleax2 > script:nth-child(1)::text').get())

        # sku = prod_dict['sku']
        # description = prod_dict['description']
        # name = prod_dict['name']
        # brand = prod_dict['brand']['name']
        # image_url = prod_dict['image']

        # upc = gral_dict['entities']['skus'][sku]['upc']
        # category = gral_dict['entities']['skus'][sku]['facets'][0]['value']

        # for i in range(3):
        #     category = ' | '.join([gral_dict['entities']['skus'][sku]['categories'][0]['hierarchy'][i]['displayName']['en'], category])

        # package = gral_dict['entities']['skus'][sku]['description']

        # item['barcodes'] = ', '.join(upc)
        # item['store'] = response.xpath('/html/head/meta[10]/@content').get()
        # item['category'] = category
        # item['package'] = package
        # item['url'] = self.start_urls[0] + url
        # item['brand'] = brand
        # item['image_url'] = ', '.join(image_url)
        # item['description'] = description.replace('<br>', '')
        # item['sku'] = sku
        # item['name'] = name

        # url_store = 'https://www.walmart.ca/api/product-page/find-in-store?' \
        #     'latitude={}&longitude={}&lang=en&upc={}'

        # for k in branches.keys():
        #     yield scrapy.http.Request(url_store.format(branches[k][0], branches[k][1], upc[0]),
        #                               callback=self.parse_api, cb_kwargs={'item': item},
        #                               meta={'handle_httpstatus_all': True},
        #                               dont_filter=False, headers=self.header)

    def parse_api(self, response, item):
        store_dict = json.loads(response.body)

        branch = store_dict['info'][0]['id']
        stock = store_dict['info'][0]['availableToSellQty']

        if 'sellPrice' not in store_dict['info'][0]:
            price = 0
        else:
            price = store_dict['info'][0]['sellPrice']

        item['branch'] = branch
        item['stock'] = stock
        item['price'] = price

        yield item

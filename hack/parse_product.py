import json
import re
import requests
import scrapy
import sys

try:
    filename = sys.argv[1]
except:
    filename = 'product_1.txt'

with open(filename, 'r+b') as f:
    body = f.read()
    r = scrapy.http.TextResponse('https://www.walmart.ca', body=body, encoding='utf-8')

scripts = r.xpath('//script/text()').getall()
for script in scripts:
    if script.find('__PRELOADED_STATE__') > -1:
        m = re.findall(r'\{.*\}', script)
        if m:
            preloaded_state = json.loads(m[0])
            # print(json.dumps(preloaded_state))
            
            try:
                products = preloaded_state['results']['entities']['products'].values()
                price_offer_req = {
                    'experience': 'grocery',
                    'fsa': 'N2R',
                    'lang': 'en',
                    'fulfillmentStoreId': '1061',
                    'pricingStoreId': '1061',
                    'products': list()
                }

                for product in products:
                    price_offer_req['products'].append({
                        'productId': product['id'],
                        'skuIds': product['skuIds']
                    })

                # print(json.dumps(price_offer_req))

                price_url = "https://www.walmart.ca/api/bsp/v2/price-offer"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0',
                    'Accept': 'application/json',
                    'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin'
                }

                # response = requests.request("POST", price_url, headers=headers, cookies=cookies, json=price_offer_request)
                response = requests.request("POST", price_url, headers=headers, json=price_offer_req)
                response = response.json()
                # print(json.dumps(response))

                for product in products:
                    product_id = product['id']
                    offers = dict()
                    try:
                        sku_ids = product['skuIds']
                        for sku_id in sku_ids:
                            offer_ids = response['skus'][sku_id]
                            for offer_id in offer_ids:
                                offer = response['offers'][offer_id]
                                if offer['offerRank'] == 1 and offer['sellerInfo']['en'] == 'Walmart':
                                    offers[sku_id] = offer
                    except Exception as e:
                        sys.stderr.write('Could not get offers for product \'{}\': {}\n'.format(product_id, str(e)))
                    product['offers'] = offers
                
                print(json.dumps(list(products)))
            except Exception as e:
                print('Error parsing response: {}'.format(e))
            
            break
            
            


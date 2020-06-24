# -*- coding: utf-8 -*-
import json

from scrapy.exceptions import DropItem
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from zalando_crawler.items import ZalandoItem


class ZalandoNormalSpiderSpider(CrawlSpider):
    name = 'zalando_spider'
    allowed_domains = ['zalando.co.uk']
    start_urls = ['https://www.zalando.co.uk/catalog']

    RESTRICT_CSS = [r'div.z-navicat-header_genders',
                    r'ul.z-navicat-header_categories',
                    r'li.catalogArticlesList_item',
                    r'a.catalogPagination_button-next']

    DENY_REGEX = (r'/myaccount', r'/wishlist', r'/cart', 'r/faq', r'/about-us')

    rules = (
        Rule(LinkExtractor(deny=DENY_REGEX, unique=True), follow=True),
        Rule(LinkExtractor(allow=r'.html$', unique=True), callback='parse_item')
    )

    def parse_item(self, response):
        self.logger.info("Parsing product page %s", response.url)
        zalando_item = ZalandoItem()
        initialize_item(item_fields=zalando_item.fields, item=zalando_item)
        item_populated = populate_item(response, zalando_item)
        return item_populated


def initialize_item(item_fields, item):
    for field in item_fields:
        if field == 'currency':
            item[field] = u'GBP'
        else:
            item[field] = u''
    return item


def populate_item(response, item):
    data_text = response.css(r"script[type='application/ld+json']").xpath('text()').extract()
    if data_text:
        data_json = json.loads(data_text[0])
    else:
        raise DropItem("Item at %s is not parsable" % response.url)
    item['title'] = data_json['name']
    item['remote_id'] = data_json['sku']
    item['main_image'] = data_json['image']
    item['brand'] = data_json['brand']
    item['color'] = data_json['color']
    item['product_condition'] = u'New' if data_json['itemCondition'] == u'http://schema.org/NewCondition' else u'Used'

    price_list = []
    for offer in data_json['offers']:
        price_list.append(offer['price'])
    if offer['availability'] == "https://schema.org/InStock":
        item['availability'] = True

    item['price'] = min(map(float, price_list))

    return item

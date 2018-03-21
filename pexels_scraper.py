from imagecrawler.items import ImagecrawlerItem
from scrapy.item import Item
import scrapy
import re
from scrapy.linkextractor import LinkExtractor
from scrapy.selector import Selector
from bs4 import BeautifulSoup
import urllib
import shutil
import wget
import requests
import os
import sys
#import urllib.request
#import urllib.request.urlretrieve()
#import urllib.urlretrieve()

IETM_PIPELINES = {'scrapy.pipelines.images.ImagesPipeline':1}
IMAGES_STORE = '/Users/dong/imagecrawler/pictures' 
URL = "https://www.pexels.com"
TAG = "river"

class PexelsScraper(scrapy.Spider): 
	name = "pexels" # Define the regex we'll need to filter the returned links 
	url_matcher = re.compile('^https:\/\/www\.pexels\.com\/photo\/') # Create a set that'll keep track of ids we've crawled 
	crawled_ids = set()
	src_extractor = re.compile('src="([^"]*)"')
	tags_extractor = re.compile('alt="([^"]*)"')

	def start_requests(self): 
		SetTAG = False
		url = "https://www.pexels.com/"
		if SetTAG:
			url = "https://www.pexels.com/search/"
			url = url+TAG+'/'
			yield scrapy.Request(url,self.parse_by_tag)
		else:
			yield scrapy.Request(url, self.parse) 
	
	def parse_by_tag(self, response):
		body = Selector(text=response.body)
		images = body.css('img.photo-item__img').extract()
		directory = "/Users/dong/imagecrawler/pictures/"+TAG
		if not os.path.exists(directory):
			os.makedirs(directory)
		for image in images:
			img_url = PexelsScraper.src_extractor.findall(image)[0]
			tags = [tag.replace(',','').lower() for tag in PexelsScraper.tags_extractor.findall(image)[0].split(' ')]
			response = requests.get(img_url)
			with open("/Users/dong/imagecrawler/pictures/{}/{}.png".format(TAG,tags),'wb') as f:
				f.write(response.content)
			print("URL: ")
			print(img_url)
			print("TAGS: ")
			print(tags)
		
	def parse(self, response):
		USER = True
		next_links = []
		body = Selector(text=response.body) 
		images = body.css('img.photo-item__img').extract()
		for image in images: 
			img_url = PexelsScraper.src_extractor.findall(image)[0] 
			tags = [tag.replace(',', '').lower() for tag in PexelsScraper.tags_extractor.findall(image)[0].split(' ')]
			print("Tags_check: ")
			print tags 
		link_extractor = LinkExtractor(allow=PexelsScraper.url_matcher) 
		next_links = [link.url for link in link_extractor.extract_links(response) if not self.is_extracted(link.url)] # Crawl the filtered links 
		next_page_url = response.css('div.pagination a[rel="next"]::attr(href)').extract_first()
		if next_page_url:
			next_page_url = URL+next_page_url
			next_links.append(next_page_url)
		print("next_page_url")
		print(next_page_url)
		if USER:
			links = response.css("a.pull-left::attr(href)").extract_first()
			print(links)
			if links:
				links = "https://www.pexels.com"+links
				for i in range(10):
					next_links.append(links+"?page="+str(i))
				print("go into user parse")
				#request.meta['main_url'] = URL
				#yield request
				for each in next_links:
					yield scrapy.Request(each,self.parse_by_user)
				print("should have done user parse")
				print("Links_check: {}".format(links))

		for link in next_links:
			print("next_links")
			print link 
			yield scrapy.Request(link, self.parse)
	'''
	def find_all_user_links(self,response):
		next_link = response.css('div.pagination a[rel="next"]::attr(href)').extract_first()
		original_link = response.meta['main_url']
		print(original_link)
		print(next_link)
		if next_link:
			next_link = original_link+next_link
			yield scrapy.Request(next_link,self.parse_by_user)
			request = scrapy.Request(next_link,self.find_all_user_links)
			request.meta['main_url'] = original_link
			yield request
	'''

	def parse_by_user(self,response):
		print("Here")
		body = Selector(text=response.body)
		title = body.css('title::text').extract_first().strip().encode("utf-8")
		if "Free" not in title:
			print("TITLE: ")
			print(title)
			images = body.css('img.photo-item__img').extract()
			directory = "/Users/dong/imagecrawler/pictures/"+title
			if not os.path.exists(directory):
				os.makedirs(directory)
			for image in images:
				img_url = PexelsScraper.src_extractor.findall(image)[0]
				tags = [tag.replace(',','').lower() for tag in PexelsScraper.tags_extractor.findall(image)[0].split(' ')]
				response = requests.get(img_url)
				with open("/Users/dong/imagecrawler/pictures/{}/{}.png".format(title.strip(),tags),'wb') as f:
					f.write(response.content)
				print("User url:")
				print(img_url)
				print("User tag:")
				print(tags)

	def is_extracted(self, url): # Image urls are of type: https://www.pexels.com/photo/asphalt-blur-clouds-dawn-392010/ 
		id = int(url.split('/')[-2].split('-')[-1]) 
		if id not in PexelsScraper.crawled_ids:
			PexelsScraper.crawled_ids.add(id) 
			return False
		return True

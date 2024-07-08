import scrapy

class SpiderCrawler(scrapy.Spider):
    name = "spider2"
    allowed_domains = ["fatsecret.co.in"]
    start_urls = ["https://www.fatsecret.co.in/calories-nutrition/search?q=cookies&pg=0"]

    # Set the download delay to 6 seconds
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
    }

    def parse(self, response):
        # Extract all table rows with class 'borderBottom'
        rows = response.css('td.borderBottom')
        for row in rows:
            link = row.css('a.prominent::attr(href)').get()
            sweet_name = row.css('a.prominent::text').get()
            if link:
                yield response.follow(link, self.parse_nutrition, meta={'sweet_name': sweet_name})

        # Find the link to the next page and follow it
        next_page = response.css('a:contains("Next")::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_nutrition(self, response):
        sweet_name = response.meta['sweet_name']
        
        # Find and click all links after the blue bullet image
        for link in response.xpath('//img[@src="https://m.ftscrt.com/static/images/icons/blue_bullet.png"]/following-sibling::a'):
            label = link.xpath('text()').get()
            href = link.attrib['href']
            if href:
                yield response.follow(href, self.parse_food_details, meta={'sweet_name': sweet_name, 'label': label})

    def parse_food_details(self, response):
        sweet_name = response.meta['sweet_name']
        label = response.meta['label']
        
        # Extract factTitle and factValue
        facts = {}
        for row in response.css('td.fact'):
            title = row.css('div.factTitle::text').get()
            value = row.css('div.factValue::text').get()
            facts[title] = value
        
        # Yield the structured data
        yield {
            'name': sweet_name,
            label: facts
        }

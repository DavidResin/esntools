import datetime, scrapy, tequila

start_time = datetime.date(1996, 1, 1)
end_time = datetime.date(2020, 12, 31)

class WASpider(scrapy.Spider):
    name = "WASpider"
    start_urls = ["http://wiki.epfl.ch/esn/sitemap"]
    conn = tequila.create_tequila_session("resin", "Minecraft1138")
    
    #DOWNLOADER_MIDDLEWARES = {
    #    'scrapy_wayback_machine.WaybackMachineMiddleware': 5,
    #}

    #WAYBACK_MACHINE_TIME_RANGE = (start_time, end_time)
    
    def parse(self, response):
        title = response.css('title::text').extract()
        yield {'titletext': response.text}
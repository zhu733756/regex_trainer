from scrapy.cmdline import execute
import os

os.chdir(os.path.dirname(__file__))

if __name__ == "__main__":
    cmd = r'''scrapy crawl regex_trainer -a web_name=解放网 -a start_urls=https://www.jfdaily.com/home'''
    execute(cmd.split(' '))

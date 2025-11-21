# 需先安装：pip install selenium webdriver-manager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def crawl_dynamic_page(url):
    """用浏览器模拟抓取动态加载页面"""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)
    time.sleep(3)  # 等待JS渲染
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    return soup

# 示例：抓取工信部专精特新栏目
soup = crawl_dynamic_page("https://www.miit.gov.cn/ztzl/zhuanjingtexin/")
for item in soup.find_all("li")[:10]:
    print(item.text.strip())  # 成功获取动态内容
#!/usr/bin/env python

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
import os

options = Options()
driver.get('https://example.org')
sleep(2)
try:
    os.makedirs('./screenshots')
except OSError:
    pass
driver.get_screenshot_as_file('screenshots/check.png')
driver.quit()
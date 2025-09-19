#!/usr/bin/env python3
import os
import traceback
from time import sleep

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import time

from selenium.webdriver.remote.webdriver import WebDriver


def run(driver: WebDriver):
    driver.get("http://0.0.0.0:8080/")
    sleep(3)
    driver.save_screenshot('a.png')
    html = driver.find_element(By.TAG_NAME, "html")
    print("Page loaded in Selenium-controlled browser on virtual display :99")
    # Keep browser open so FFmpeg can capture the screen
    time.sleep(600)  # seconds; adjust as needed

def run_selenium_on_xvfb():
    os.environ['DISPLAY'] = ':99'
    print(os.getenv('DISPLAY'))
    options = Options()
    # options.add_argument("--headless")  # Enable headless mode
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")

    driver = webdriver.Firefox(service=Service("geckodriver"), options=options)
    try:
        driver.set_window_position(-5, -5, windowHandle ='current')  # correcting weird window offsets
        driver.fullscreen_window()  # pixel-perfect 1920x1080
        run(driver)
    except Exception:
        print(traceback.format_exc())
    finally:
        driver.quit()


if __name__ == "__main__":
    os.system('Xvfb :99 -screen 0 1920x1080x24 -ac &')
    run_selenium_on_xvfb()

#!/usr/bin/env python3

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS,cross_origin
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

LIVE = True

app = Flask(__name__)
CORS(app)

player_names = {'reub': 'Mighty Spearheads', 'renj': 'Paavam XI', 'suva': 'kaala Venghai',
                'gopi': 'GOPI5', 'dani': 'Aj team817KT', 'akm': 'SaidapetSuperkings'}

player_dict = {}
chrome_options = Options()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(executable_path=os.environ.get(
    "CHROMEDRIVER_PATH"), chrome_options=chrome_options)
driver.maximize_window()
wait = WebDriverWait(driver, 10)
driver.get("https://www.dream11.com/leagues")
time.sleep(3)
driver.find_elements_by_class_name("whiteBorderedButton_6b901")[0].click()
time.sleep(3)

@app.route("/phoneNumber", methods=['POST'])
@cross_origin(origin='https://team11-app.netlify.app/')
def phoneNumber():
    print("Phone No verification..")
    jsonData = request.get_json()
    print(jsonData)
    # format(jsonData['phone'])
    print("Logging in..")
    text_field = driver.find_element_by_xpath(
        "/html/body/div/div/div[3]/div/div/div[2]/div/div[1]/div[2]/div[1]/input")
    text_field.send_keys(jsonData['phone'])
    driver.find_element_by_xpath(
        "/html/body/div/div/div[3]/div/div/div[2]/div/div[2]/button").click()
    response_object = {"status": "success", "message": "otp verification"}
    return jsonify(response_object)


@app.route("/otp", methods=['POST'])
@cross_origin(origin='https://team11-app.netlify.app/')
def otp():
    global LIVE
    print("OTP verification..")
    otp_no = request.get_json()
    print(otp_no)
    otp = driver.find_element_by_xpath(
        "/html/body/div/div/div[3]/div/div/div[2]/div[1]/div[1]/div[2]/div[1]/input")
    otp.send_keys(otp_no['otp'])
    driver.find_element_by_xpath(
        "/html/body/div/div/div[3]/div/div/div[2]/div[1]/div[2]/button").click()
    time.sleep(5)

    print("Getting info..")
    my_matches = wait.until(ec.visibility_of_element_located((By.XPATH, "/html/body/div/div/div[3]/div/div/div[3]/div/div/a[2]/div[1]/i")))
    my_matches.click()
    time.sleep(3)

    # Live matches
    driver.find_element_by_xpath(
        "/html/body/div/div/div[3]/div/div/div[1]/div[2]/div/div/div[2]").click()
    time.sleep(3)
    try:
        driver.find_element_by_xpath(
            "/html/body/div/div/div[3]/div/div/div[2]/div/div/div/a/div/div/div[2]").click()
    except Exception:
        LIVE = False
        print("No Live matches currently!")
    print("Live",LIVE)
    # Completed Matches
    if not LIVE:
        driver.find_element_by_xpath(
            "/html/body/div/div/div[3]/div/div/div[1]/div[2]/div/div/div[3]").click()
        time.sleep(3)
        driver.find_element_by_xpath(
            "/html/body/div/div/div[3]/div/div/div[2]/div/div/div/a/div/div/div[2]").click()

    time.sleep(3)
    driver.find_element_by_xpath(
        "/html/body/div/div/div[3]/div/div/div[2]/div/div[2]/a/div[2]/div/div").click()
    time.sleep(5)
    containers = driver.find_elements_by_xpath(
        "/html/body/div/div/div[3]/div/div/div[5]/div[2]/div[1]/div[3]/div")
    info = str(containers[0].text).split('\n')
    if "WINNER!" in info:
        info.remove("WINNER!")
    for i in range(0, len(info), 4):
        player_dict[info[i]] = info[i+2]
    print("Player dict", player_dict)
    response_object = {"status": "success",
                       "message": player_dict, "live": LIVE}
    return jsonify(response_object)


@app.route("/refresh", methods=['GET'])
@cross_origin(origin='https://team11-app.netlify.app/')
def update_points():
    print("Updating latest points")
    driver.refresh()
    time.sleep(4)
    containers = driver.find_elements_by_xpath(
        "/html/body/div/div/div[3]/div/div/div[5]/div[2]/div[1]/div[3]/div")
    info = str(containers[0].text).split('\n')
    if "WINNER!" in info:
        info.remove("WINNER!")
    for i in range(0, len(info), 4):
        player_dict[info[i]] = info[i+2]
    print("INFO", info)
    response_object = {"status": "success",
                       "message": player_dict, "live": LIVE}
    return jsonify(response_object)

if __name__ == "__main__":
    app.run()

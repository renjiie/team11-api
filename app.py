#!/usr/bin/env python3

import os
import json
import pymongo
import time
from schedule import Matches
from datetime import date
from flask import Flask, request, jsonify
from flask_cors import CORS,cross_origin
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
# Selenium attributes
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

# DB attributes
myclient = pymongo.MongoClient("mongodb+srv://team11dev:team11dev@cluster0.dqoyp.mongodb.net/test?retryWrites=true&w=majority")

class Team11(object):

  def _get_data(self):
    contest = wait.until(ec.visibility_of_element_located((By.XPATH,"/html/body/div/div/div[3]/div/div/div[2]/div/div[2]/a/div[2]/div/div")))
    contest.click()
    time.sleep(2)
    containers = driver.find_elements_by_xpath("/html/body/div/div/div[3]/div/div/div[5]/div[2]/div[1]/div[3]/div")
    info = str(containers[0].text).split('\n')
    if "WINNER!" in info:
      info.remove("WINNER!")

    for i in range(0,len(info),4):
      player_dict[info[i]] = info[i+2]
    return player_dict
  

  def get_phone_no(self):
      driver.get("https://www.dream11.com/leagues")
      time.sleep(3)
      driver.find_elements_by_class_name("whiteBorderedButton_6b901")[0].click()
      time.sleep(3)
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


  def get_otp(self):
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

  def insert_teams(self):
      print("Insert teams to DB")
      today = date.today().strftime("%d/%m")
      match_name = Matches[today]
      mydb = myclient["team11"]
      mycol = mydb["teams"]
      team_json = request.get_json()
      team_json['team']['_id'] = match_name
      mycol.insert_one(team_json['team'])
      response_object = {"status": "success",
              "message": "Data inserted successfully"}
      return jsonify(response_object)
    #   for data in mycol.find():
    #     if data['_id'] == match_name:

    #       print ("Insertion Not required: Team already present for today's match!");

    #     else:
    #       mycol.insert_one(team_json['team'])

  def do_refresh(self):
      print("Updating latest points")
      today = date.today().strftime("%d/%m")
      match_name = Matches[today]
      mydb = myclient["team11"]
      mycol = mydb["teams"]
      team_from_db = ""
      for data in mycol.find():
        if data['_id'] == match_name:
           team_from_db = data
           print("DB team", data)
      if not team_from_db :
          print("Team names not present in DB. Please insert first: /insertteams")
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
              "message": player_dict, "live": LIVE, 'Dbteam': team_from_db}
      return jsonify(response_object)

  def update_db(self):
    print("Updating Historical data to DB")
    driver.execute_script("window.history.go(-2)")
    games = driver.find_elements_by_partial_link_text("VIVO")
    for i in range(len(games)):
      # Get all completed matches
      games = driver.find_elements_by_partial_link_text("VIVO")
      game = games[i]
      game.click()
      leaderboard = self._get_data() 
      # --> Add code here to insert leaderboard of each game to DB <--
      driver.execute_script("window.history.go(-2)")
      time.sleep(2)
      driver.find_element_by_xpath(
          "/html/body/div/div/div[3]/div/div/div[1]/div[2]/div/div/div[3]").click()
      time.sleep(1)
  
team_obj = Team11() 

@app.route("/phoneNumber", methods=['POST'])
@cross_origin(origin='https://team11-app.netlify.app/')
def phoneNumber():
  return team_obj.get_phone_no()

@app.route("/otp", methods=['POST'])
@cross_origin(origin='https://team11-app.netlify.app/')
def otp():
  return team_obj.get_otp()

@app.route("/refresh", methods=['GET'])
@cross_origin(origin='https://team11-app.netlify.app/')
def update_points():
  return team_obj.do_refresh()

@app.route("/database", methods=['GET'])
@cross_origin(origin='https://team11-app.netlify.app/')
def get_leaderboard():
  return team_obj.update_db()

@app.route("/insertteams", methods=['POST'])
@cross_origin(origin='https://team11-app.netlify.app/')
def team_insert():
      return team_obj.insert_teams()

if __name__ == "__main__":
    app.run()

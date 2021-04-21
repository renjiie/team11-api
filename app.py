#!/usr/bin/env python3

import os
import json
import pymongo
import time
from schedule import Matches
from datetime import date
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS,cross_origin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

LIVE = True
CUT_OFF_TIME = 11

app = Flask(__name__)
CORS(app)

# Not used
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
    wait.until(ec.visibility_of_element_located((By.XPATH, "/html/body/div/div/div[3]/div/div/div[5]/div[2]/div[1]/div[3]/div")))    
    containers = driver.find_elements_by_xpath("/html/body/div/div/div[3]/div/div/div[5]/div[2]/div[1]/div[3]/div")
    info = str(containers[0].text).split('\n')
    if "WINNER!" in info:
      info.remove("WINNER!")

    for i in range(0,len(info),4):
      player_dict[info[i]] = info[i+2]
    return player_dict
  

  def get_phone_no(self):
      driver.get("https://www.dream11.com/leagues")
      login = wait.until(ec.visibility_of_element_located((By.XPATH, "/html/body/div/div/div[3]/div/div/div[1]/div[1]/div/div/div[2]/div/a")))
      login.click()
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

      print("Getting info..")
      my_matches = wait.until(ec.visibility_of_element_located((By.XPATH, "/html/body/div/div/div[3]/div/div/div[3]/div/div/a[2]/div[1]/i")))
      my_matches.click()

      # Live matches
      temp = wait.until(ec.visibility_of_element_located((By.XPATH, "/html/body/div/div/div[3]/div/div/div[1]/div[2]/div/div/div[2]")))
      temp.click()
      try:
        live_match =  wait.until(ec.visibility_of_element_located((By.XPATH, "/html/body/div/div/div[3]/div/div/div[2]/div/div/div/a/div/div/div[2]")))
        live_match.click()
      except Exception:
        LIVE = False
        print("No Live matches currently!")
        # response_object = {"status": "success",
        #                   "message": "No LIVE matches in-progress.Please come back during match time!", "live": LIVE}
        # return jsonify(response_object)

      # Completed Matches
      if not LIVE:
        driver.find_element_by_xpath(
            "/html/body/div/div/div[3]/div/div/div[1]/div[2]/div/div/div[3]").click()
          
          
        completed_match = wait.until(ec.visibility_of_element_located((By.XPATH, "/html/body/div/div/div[3]/div/div/div[2]/div/div/div/a/div/div/div[2]")))
        completed_match.click()
  
      
      temp1 = wait.until(ec.visibility_of_element_located((By.XPATH, "/html/body/div/div/div[3]/div/div/div[2]/div/div[2]/a/div[2]/div/div")))
      temp1.click()      
      wait.until(ec.visibility_of_element_located((By.XPATH, "/html/body/div/div/div[3]/div/div/div[5]/div[2]/div[1]/div[3]/div")))      
      containers = driver.find_elements_by_xpath("/html/body/div/div/div[3]/div/div/div[5]/div[2]/div[1]/div[3]/div")
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
      # DB init
      mydb = myclient["team11"]
      mycol = mydb["teams"]
      complete_matches = mydb["completed matches"]
      team_json = request.get_json()
      match_name = Matches[today]
      completeDict = {}
      print("complete Dict:", completeDict)
      # Insertion logic for Double headers
      if '-' in match_name:
          match_list = match_name.split('-')
          match_list = [item.strip() for item in match_list]
          print("Match list:", match_list)
          time_now = datetime.now()
          print("--Time in int: %d" % (int(time_now.strftime("%H"))))
          # 11 is UTC Heroku server time +6:30 IST
          if int(time_now.strftime("%H")) < CUT_OFF_TIME:
              print("--inside if--")
              team_json['team']['_id'] = match_list[0]
              completeDict['_id'] = match_list[0]
          else:
              print("--inside else--")
              team_json['team']['_id'] = match_list[1]
              completeDict['_id'] = match_list[1]
      else:
          team_json['team']['_id'] = match_name
          completeDict['_id'] = match_name
      print("--match name:", team_json['team']['_id'])
      entry_exists = None
      for data in mycol.find():
        if data['_id'] == team_json['team']['_id']:     
          entry_exists = True
          print ("Insertion Not required: Team already present for today's match!");
          response_object = {"status": "failed","message": "Data already inserted "}
          break

      if not entry_exists:
        print ("Insertion required: Team not present for today's match!");
        mycol.insert_one(team_json['team'])
        complete_matches.insert_one(completeDict)
        response_object = {"status": "success","message": "Data inserted successfully"}

      return jsonify(response_object)

  def do_refresh(self):
      print("Updating latest points")
      today = date.today().strftime("%d/%m")
      match_name = Matches[today]
      mydb = myclient["team11"]
      mycol = mydb["teams"]
      team_from_db = ""
      if '-' in match_name:
          match_list = match_name.split('-')
          match_list = [item.strip() for item in match_list]
          time_now = datetime.now()
          # Cut off time for First match to complete - 7:45pm
          # 1410 is UTC Heroku server time
          if int(time_now.strftime("%H%M")) < 1410:
              match_name = match_list[0]
          else:
              match_name = match_list[1]
      
      for data in mycol.find():
        if data['_id'] == match_name:
           team_from_db = data
           print("DB team", data)
           break
      if not team_from_db :
          print("Team names not present in DB. Please insert first: /insertteams")
      driver.refresh()
      wait.until(ec.visibility_of_element_located((By.XPATH, "/html/body/div/div/div[3]/div/div/div[5]/div[2]/div[1]/div[3]/div")))
      containers = driver.find_elements_by_xpath("/html/body/div/div/div[3]/div/div/div[5]/div[2]/div[1]/div[3]/div")
      print("CONTAINER:", containers)

      info = str(containers[0].text).split('\n')
      print("INFO", info)

      if "WINNER!" in info:
          info.remove("WINNER!")
      for i in range(0, len(info), 4):
          player_dict[info[i]] = info[i+2]
      
      #code to get the db values and update the current values in db
      temp_winner = ""
      temp_win_points = 0
      for players in player_dict:
          print("players", players)
          if temp_win_points < int(player_dict[players]):
             temp_win_points = int(player_dict[players])
             temp_winner = players

      complete_matches = mydb["completed matches"]
      matchList = []
      tempDict = {"status": "success","message": player_dict, "live": LIVE, 'Dbteam': team_from_db}
      matchList.append(tempDict)
      for eachMatch in complete_matches.find():
          #tempDict = {"status": "success","message": player_dict, "live": LIVE, 'Dbteam': team_from_db}
          if eachMatch['_id'] != match_name:
              tempDict["message"] = eachMatch['points']
              tempDict["live"] = False
              tempDict['Dbteam'] = eachMatch['team']
          matchList.append(tempDict)
      
      newDict = {}
      newDict['_id'] = match_name
      newDict['team'] = team_from_db
      newDict['points'] = player_dict
      newDict['winner']= temp_winner
      complete_matches.insert_one(newDict)
              
      response_object = matchList
      return response_object

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
      contest_page = wait.until(ec.visibility_of_element_located((By.XPATH, "/html/body/div/div/div[3]/div/div/div[1]/div[2]/div/div/div[3]")))
      contest_page.click()
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

import pymongo
import json
import os

print(os.environ["mongodb_dbname"])

client = pymongo.MongoClient("mongodb+srv://draftDataUser:amateurtopro20@draftdatacluster.w18yo.mongodb.net/nba_draft_database?retryWrites=true&w=majority")
db = client.nba_draft_database
nba_draft_data = db.nba_draft_data 

# with open('draftData.json', 'r', newline='') as draftDataJson:
#     draftData = json.load(draftDataJson)

#     for year in range(1989, 2019):
#         draft = draftData[str(year)]

#         for player in draft:
#             player['pick_number'] = int(player['pick_number'])
#             player['draft_year'] = year
#             nba_draft_data.insert_one(player)



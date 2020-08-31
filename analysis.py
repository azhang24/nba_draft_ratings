import json
import pymongo
import keyring
import math

password = keyring.get_password('nba_draft_stats', 'draftDataUser')
dbUrl = "".join(["mongodb+srv://draftDataUser:", password, "@draftdatacluster.w18yo.mongodb.net/nba_draft_database?retryWrites=true&w=majority"])

client = pymongo.MongoClient(dbUrl)
db = client.nba_draft_database
nba_draft_data = db.nba_draft_data

def getDraftScores(buckets):

    bestDraftScore = float("-inf")
    bestDraftPlayer = None

    playerDraftScores = []
    teamDraftScores = []

    picksPerTeam = {}
    totalDraftScorePerTeam = {}
    averageDraftScorePerTeam = {}
    for year in range(1989, 2019):
        print(year)
        draftedPlayers = nba_draft_data.find({"draft_year": year})
        draftedPlayersSorted = nba_draft_data.find({"draft_year": year}).sort("total_ws_career", pymongo.DESCENDING) 
        numFirstRoundPicks = nba_draft_data.count_documents({"$and": [{"draft_year": year}, {"round": 1}]})
        if year == 2001 or year == 2002:
            numFirstRoundPicks += 1
        numSecondRoundPicks = nba_draft_data.count_documents({"$and": [{"draft_year": year}, {"round": 2}]})
        numDraftPicks = numFirstRoundPicks + numSecondRoundPicks
        
        bucketAssignments = {}
        numBuckets = 0
        lastBucketPick = buckets[-1][1]
        for bucket in buckets:
            startPick = bucket[0]
            endPick = bucket[1]
            if startPick <= numDraftPicks:
                if endPick > numDraftPicks:
                    endPick = numDraftPicks
                for pick in range(startPick, endPick+1):
                    bucketAssignments[pick] = numBuckets+1
            else:
                break
            
            numBuckets += 1
        
        if lastBucketPick < numDraftPicks:
            for pick in range(lastBucketPick+1, numDraftPicks+1):
                bucketAssignments[pick] = numBuckets+1
            
            numBuckets += 1


        mostTotalWSCareer = None
        player_rankings = {}
        bucketToPlayers = {}
        ranking = 1
        for player in draftedPlayersSorted:
            playerName = player["player_name"]
            playerTeam = player["first_team"]
            playerRound = player["round"]
            player_rankings[(playerName, playerTeam)] = ranking
            bucket = bucketAssignments[ranking]
            if(bucketToPlayers.get(bucket, None) == None):
                bucketToPlayers[bucket] = []

            bucketToPlayers[bucket].append(player)
            
            if ranking == 1:
                mostTotalWSCareer = player['total_ws_career']

            if (year == 2001 or year == 2002) and ranking == numFirstRoundPicks: #MIN forfeited 29th pick both years
                ranking += 2
            else:
                ranking += 1
        
        bucketMedianWS = {}
        for bucket in range(1, numBuckets+1):
            bucketPlayers = bucketToPlayers[bucket]
            bucketSize = len(bucketToPlayers[bucket])
            medianWS = None
            if bucketSize % 2 == 0: 
                medianWS = (bucketPlayers[math.floor(bucketSize/2)]['total_ws_career'] + bucketPlayers[math.floor(bucketSize/2)-1]['total_ws_career']) / 2
            else:
                medianWS = bucketPlayers[math.floor(bucketSize/2)]['total_ws_career']
            bucketMedianWS[bucket] = medianWS

            
        for player in draftedPlayers:
            playerName = player["player_name"]
            playerTeam = player["first_team"]
            pickNumber = player["pick_number"]
            bucket = bucketAssignments[pickNumber]
            medianWS = bucketMedianWS[bucket]
            playerTotalWSFirstTeam = player["total_ws_with_first_team"]
            percentile = medianWS / mostTotalWSCareer
            weight = 1 - percentile
            draftScore = weight * playerTotalWSFirstTeam
            player["draft_score"] = draftScore
            playerDraftScores.append(player)

            if picksPerTeam.get(playerTeam, None) == None:
                picksPerTeam[playerTeam] = 1
            else:
                picksPerTeam[playerTeam] += 1

            if totalDraftScorePerTeam.get(playerTeam, None) == None:
                totalDraftScorePerTeam[playerTeam] = draftScore
            else:
                totalDraftScorePerTeam[playerTeam] += draftScore

            if draftScore > bestDraftScore:
                bestDraftScore = draftScore
                bestDraftPlayer = playerName

            # playerFilter = {"$and": [{"draft_year": year}, {"player_name": playerName}, {"player_team": playerTeam}]}
            # draftScoreField = {"$set": {"draftScore": draftScore}}
            # nba_draft_data.update_one(playerFilter, draftScoreField)
    
    print("Best Draft Score: {}, {}".format(bestDraftPlayer, bestDraftScore))

    averageDraftScorePerTeam = {team:(totalScore/picksPerTeam[team]) for team, totalScore in totalDraftScorePerTeam.items()}

    teamDraftScores = [{'team_name': team, 'total_draft_score': totalDraftScorePerTeam[team], 'average_draft_score': averageDraftScorePerTeam[team]} for team in picksPerTeam.keys()]

    response = {'player_draft_scores': playerDraftScores, 'team_draft_scores': teamDraftScores}

    return response


data = getDraftScores([[1,3],[4,14],[15,30],[31,60]])
print(sorted(data['team_draft_scores'], key=lambda x: x['total_draft_score'], reverse=True))
print(sorted(data['team_draft_scores'], key=lambda x: x['average_draft_score'], reverse=True))




        


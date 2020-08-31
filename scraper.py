import requests
from bs4 import BeautifulSoup
import re
import csv
import json

comm = re.compile('<!--|-->')

alternativeAbbrevs = {}

alternativeAbbrevs['NOP'] = ['NOK', 'NOH']
alternativeAbbrevs['NOK'] = ['NOP', 'NOH']
alternativeAbbrevs['NOH'] = ['NOP', 'NOK']

alternativeAbbrevs['WAS'] = ['WSB']
alternativeAbbrevs['WSB'] = ['WAS']

alternativeAbbrevs['VAN'] = ['MEM']
alternativeAbbrevs['MEM'] = ['VAN']

alternativeAbbrevs['NJN'] = ['BKN']
alternativeAbbrevs['BKN'] = ['NJN']

alternativeAbbrevs['CHH'] = ['CHA', 'CHO']
alternativeAbbrevs['CHA'] = ['CHH', 'CHO']
alternativeAbbrevs['CHO'] = ['CHH', 'CHA']

alternativeAbbrevs['SEA'] = ['OKC']
alternativeAbbrevs['OKC'] = ['SEA']


def hasAlternativeAbbrev(teamOne, teamTwo):
    inAlternativeAbbrev = (alternativeAbbrevs.get(teamOne, None) != None) and (alternativeAbbrevs.get(teamTwo, None) != None)
    if inAlternativeAbbrev:
        return (teamOne in alternativeAbbrevs[teamTwo]) or (teamTwo in alternativeAbbrevs[teamOne])
    return False 

def getRegSeasonWinShares(advStatsTable, totalWinSharesWithFirstTeam, winSharesEachYearPerTeam):
    firstTeamAbrev = ""
    advStatsHeaders = [header.string for header in list(advStatsTable.thead.tr.children)]
    winSharesColumnNum = advStatsHeaders.index('WS')
    advStatsRegSeasons = list(advStatsTable.tbody.children)
    isFirstSeason = True
    teams = {}
    switchedFromFirstTeam = ""
    (prevSeason, prevTeam) = (None, None)
    for season in advStatsRegSeasons:
        stats = list(season.children)
        seasonYears = stats[0].a.string
        if(teams.get(seasonYears, None) == None):
            teams[seasonYears] = []
        if stats[2].a != None:
            currentTeamAbrev = stats[2].a.string
            teams[seasonYears].append(currentTeamAbrev)
            if prevTeam != None and (currentTeamAbrev != prevTeam and not hasAlternativeAbbrev(prevTeam, currentTeamAbrev)) and switchedFromFirstTeam == "":
                switchedFromFirstTeam = seasonYears

            if isFirstSeason:
                firstTeamAbrev = stats[2].a.string
                isFirstSeason = False

            regSeasonWinShares = float(stats[winSharesColumnNum].string)
            if(winSharesEachYearPerTeam.get((seasonYears, currentTeamAbrev), None) == None):
                winSharesEachYearPerTeam[(seasonYears, currentTeamAbrev)] = regSeasonWinShares
            else:
                winSharesEachYearPerTeam[(seasonYears, currentTeamAbrev)] += regSeasonWinShares

            if currentTeamAbrev == firstTeamAbrev or hasAlternativeAbbrev(firstTeamAbrev, currentTeamAbrev):
                if switchedFromFirstTeam != "":
                    if int(switchedFromFirstTeam.split("-")[0]) > int(seasonYears.split("-")[0]):
                        totalWinSharesWithFirstTeam += regSeasonWinShares
                else:
                    totalWinSharesWithFirstTeam += regSeasonWinShares
            
            (prevSeason, prevTeam) = (seasonYears, currentTeamAbrev)

    
    return firstTeamAbrev, totalWinSharesWithFirstTeam, winSharesEachYearPerTeam, teams, switchedFromFirstTeam

def getPlayoffsWinShares(firstTeamAbrev, advStatsTable, totalWinSharesWithFirstTeam, winSharesEachYearPerTeam, teams, switchedFromFirstTeam):
    advStatsHeaders = [header.string for header in list(advStatsTable.thead.tr.children)]
    winSharesColumnNum = advStatsHeaders.index('WS')
    advStatsPlayoffs = list(advStatsTable.tbody.children)

    for season in advStatsPlayoffs:
        stats = list(season.children)
        seasonYears = stats[0].a.string
        if stats[2].a != None:
            currentTeamAbrev = stats[2].a.string

            playoffsWinShares = float(stats[winSharesColumnNum].string)
            if winSharesEachYearPerTeam.get((seasonYears, currentTeamAbrev), None) == None:
                winSharesEachYearPerTeam[(seasonYears, currentTeamAbrev)] = playoffsWinShares
            else:
                winSharesEachYearPerTeam[(seasonYears, currentTeamAbrev)] += playoffsWinShares

            if currentTeamAbrev == firstTeamAbrev or hasAlternativeAbbrev(firstTeamAbrev, currentTeamAbrev):
                # currentSeasonFirstCalendarYear = seasonYears.split("-")[0]
                # prevSeasonYears = "-".join([str(int(currentSeasonFirstCalendarYear)-1), currentSeasonFirstCalendarYear[2:]])
                # prevSeasonTeams = teams.get(prevSeasonYears, None)
                # currSeasonTeams = teams.get(seasonYears, None)
                
                # prevTeam = None
                # if len(currSeasonTeams) > 1:
                #     prevTeam = currSeasonTeams[-2]
                # else:
                #     if(prevSeasonTeams != None):
                #         prevTeam = prevSeasonTeams[-1]

                # if(prevSeasonTeams != None):
                #     prevSeasonTeam = prevSeasonTeams[-1]
                #if((currentTeamAbrev == prevTeam) or hasAlternativeAbbrev(prevTeam, currentTeamAbrev)):
                if switchedFromFirstTeam != "":
                    if int(switchedFromFirstTeam.split("-")[0]) > int(seasonYears.split("-")[0]):
                        totalWinSharesWithFirstTeam += playoffsWinShares
                else:
                    totalWinSharesWithFirstTeam += playoffsWinShares
                # else:
                #     totalWinSharesWithFirstTeam += playoffsWinShares
    
    return totalWinSharesWithFirstTeam, winSharesEachYearPerTeam

def getDraftData(yearStart, yearEnd):

    if yearStart > yearEnd:
        print("start year cannot be after end year")
        return None

    draftData = {}
    for year in range(yearStart, yearEnd+1):
        print(year)
        page = requests.get(url='https://www.basketball-reference.com/draft/NBA_' + str(year) + '.html')
        soup = BeautifulSoup(comm.sub("", str(page.content)), 'html5lib')

        draftList = soup.find('table', id='stats').tbody
        players = list(draftList.children)

        currRound = 1

        draftData[year] = []

        for player in players:
            clss = player.get('class', None)
            #Row on draft list represents a player
            if clss == None:
                attributes = list(player.children)
                pickNum = attributes[1].a.string if attributes[1].a != None else None
                if pickNum != None:
                    peakWinSharesCareer = float('-inf')
                    peakWinSharesWithFirstTeam = float('-inf')
                    totalWinSharesWithFirstTeam = 0.0
                    totalWinSharesCareer = 0.0
                    playerName = attributes[3].a.string if attributes[3].a != None else attributes[3].string
                    print(playerName)
                    playerLink = attributes[3].a.get('href') if attributes[3].a != None else ""
                    playerRound = currRound
                    print("Round " + str(playerRound))
                    #BasketballReference link to the player exists
                    if playerLink != "":
                        playerPage = requests.get(url='https://www.basketball-reference.com' + playerLink)
                        soupPlayer = BeautifulSoup(comm.sub("", str(playerPage.content)), 'html5lib')

                        winSharesEachYearPerTeam = {}
                        
                        switchedFromFirstTeam = ""
                        #Get Regular Season Win Shares
                        playerRegSeasonAdvStats = soupPlayer.find('table', id='advanced')
                        if playerRegSeasonAdvStats != None:
                            firstTeamAbrev, totalWinSharesWithFirstTeam, winSharesEachYearPerTeam, teams, switchedFromFirstTeam = getRegSeasonWinShares(playerRegSeasonAdvStats, totalWinSharesWithFirstTeam, winSharesEachYearPerTeam)
                        
                        #Get Playoffs Win Shares
                        playerPlayoffsAdvStats = soupPlayer.find('table', id='playoffs_advanced')
                        if playerPlayoffsAdvStats != None:
                            totalWinSharesWithFirstTeam, winSharesEachYearPerTeam = getPlayoffsWinShares(firstTeamAbrev, playerPlayoffsAdvStats, totalWinSharesWithFirstTeam, winSharesEachYearPerTeam, teams, switchedFromFirstTeam)
                        
                        winSharesEachYear = {}

                        #Get peak win shares with first team
                        peakWinSharesWithFirstTeamSeason = ""
                        prevTeam = None
                        for (season, team), winShares in winSharesEachYearPerTeam.items():
                            
                            if winSharesEachYear.get(season, None) == None:
                                winSharesEachYear[season] = winShares
                            else:
                                winSharesEachYear[season] += winShares

                            if team == firstTeamAbrev or hasAlternativeAbbrev(firstTeamAbrev, team):
                                if switchedFromFirstTeam == "" or (int(switchedFromFirstTeam.split("-")[0]) > int(season.split("-")[0])) or (((int(switchedFromFirstTeam.split("-")[0]) == int(season.split("-")[0])) and team == teams[season][0])):
                                        if winShares > peakWinSharesWithFirstTeam:
                                            peakWinSharesWithFirstTeam = winShares
                                            peakWinSharesWithFirstTeamSeason = season
                                
                            prevTeam = team
                        
                        peakWinSharesCareerSeason = ""
                        for season, winShares in winSharesEachYear.items():
                            totalWinSharesCareer += winShares
                            if winShares > peakWinSharesCareer:
                                peakWinSharesCareer = winShares
                                peakWinSharesCareerSeason = season


                    if peakWinSharesCareer == float('-inf'):
                        peakWinSharesCareer = 0.0

                    if peakWinSharesWithFirstTeam == float('-inf'):
                        peakWinSharesWithFirstTeam = 0.0


                    if firstTeamAbrev == "CHH" or firstTeamAbrev == "CHA" or firstTeamAbrev == "CHO":
                        firstTeamAbrev = "CHH/CHA/CHO"
                    
                    elif firstTeamAbrev == 'WAS' or firstTeamAbrev == 'WSB':
                        firstTeamAbrev = 'WAS/WSB'
                    
                    elif firstTeamAbrev == 'VAN' or firstTeamAbrev == 'MEM':
                        firstTeamAbrev = 'VAN/MEM'

                    elif firstTeamAbrev == 'NJN' or firstTeamAbrev == 'BRK':
                        firstTeamAbrev = 'NJN/BRK'

                    elif firstTeamAbrev == 'NOH' or firstTeamAbrev == 'NOK' or firstTeamAbrev == 'NOP':
                        firstTeamAbrev = 'NOH/NOK/NOP'

                    elif firstTeamAbrev == 'SEA' or firstTeamAbrev == 'OKC':
                        firstTeamAbrev = 'SEA/OKC'


                    playerDict = {
                        'player_name': playerName,
                        'round': currRound,
                        'pick_number': pickNum,
                        'first_team': firstTeamAbrev,
                        'peak_ws_with_first_team': peakWinSharesWithFirstTeam,
                        'peak_ws_season_with_first_team': peakWinSharesWithFirstTeamSeason,
                        'peak_ws_career': peakWinSharesCareer,
                        'peak_ws_season_career': peakWinSharesCareerSeason,
                        'total_ws_with_first_team': totalWinSharesWithFirstTeam,
                        'total_ws_career': totalWinSharesCareer
                    }

                    draftData[year].append(playerDict)
            
            elif clss == ['over_header', 'thead']:
                currRound += 1
    
    draftJSON = json.dumps(draftData, indent=4)
    
    with open("draftData.json", "w") as draftDataFile:
        draftDataFile.write(draftJSON)

getDraftData(1989, 2018)
            
            
            
                







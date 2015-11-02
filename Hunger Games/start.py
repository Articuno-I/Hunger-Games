import random,copy,sys

KILL_DIFFICULTY = 5
LETHAL_POPULATION = 3

verbose = False

def printf(text):
    if verbose:
        print(text)

class Contestant:
    def __init__(self,name,stats = None,skills = None,inventory = None, pos = (0,0)): #stats out of 4, 2 is average, skills out of 3, 0 is average.
        self.name = name
        self.stats = stats
        self.skills = skills
        self.kills = []
        self.inventory = inventory
        self.pos = pos
        self.live = True
        game.map.grid[self.pos[0]][self.pos[1]].players.append(self)

        self.stats = {"Strength":2,"Dexterity":2,"Intelligence":2}
        self.skills = {"Survival":0,"Stabbing":0,"Bow":0,"Unarmed":0,"Shooting":0}

        self.wounds = 0

        if stats:
            for stat in stats:
                self.stats[stat] = stats[stat]
        if skills:
            for skill in skills:
                self.skills[skill] = skills[skill]

        if not inventory:
            self.inventory = []

    def challenge(self,stat,skill):
        total = {False:self.stats[stat],True:0}[stat == False] + {False:self.skills[skill],True:0}[skill == False]
        wins = 0
        for i in range(total):
            wins += {False:0,True:1}[random.randint(0,1) == 1]
        return(wins)

    def compete(self,other,selfstat,selfskill,otherstat = None,otherskill = None,advantage=0):
        if not otherstat:
            otherstat = selfstat
        if not otherskill:
            otherskill = selfskill
        
        selfTotal = self.stats[selfstat] + self.skills[selfskill]
        otherTotal = other.stats[otherstat] + other.skills[otherskill]
        if advantage > 0:
            selfTotal += advantage
        else:
            otherTotal += abs(advantage)
            
        selfWins = 0

        otherWins = 0

        for i in range(selfTotal):
            selfWins += {False:0,True:1}[random.randint(0,1) == 1]

        for i in range(otherTotal):
            otherWins += {False:0,True:1}[random.randint(0,1) == 1]
            
        if selfWins > otherWins:
            victory = True
        elif selfWins < otherWins:
            victory = False
        else:
            victory = random.randint(0,1) == 1

        return((selfWins-otherWins,victory))

    def getTagged(self,tags):
        if type(tags) == type(""):
            tags = [tags]
        items = []
        for item in self.inventory:
            valid = True
            for tag in tags:
                if not tag in item.tags:
                    valid = False
            if valid:
                items.append(item)
        return(items)

    def getWeapon(self):
        fStrength = self.skills["Unarmed"] + self.stats["Strength"]
        wChoice = None
        for weapon in self.getTagged("weapon"):
            if self.skills[weapon.values["skill"]] + weapon.values["weaponStrength"] + self.stats[weapon.values["stat"]] >= fStrength:
                fStrength = self.skills[weapon.values["skill"]] + weapon.values["weaponStrength"] + self.stats[weapon.values["stat"]]
                wChoice = weapon
        return(wChoice,fStrength)

    def fight(self,other,advantage=0):
        weapon, weapBonus = self.getWeapon()
        otherWeapon, otherWeapBonus = other.getWeapon()

        if weapon:
            weaponStat = weapon.values["stat"]
            weaponSkill = weapon.values["skill"]
            weaponStrength = weapon.values["weaponStrength"]
        else:
            weaponStat = "Strength"
            weaponSkill = "Unarmed"
            weaponStrength = 0
        if otherWeapon:
            otherWeaponStat = otherWeapon.values["stat"]
            otherWeaponSkill = otherWeapon.values["skill"]
            otherWeaponStrength = otherWeapon.values["weaponStrength"]
        else:
            otherWeaponStat = "Strength"
            otherWeaponSkill = "Unarmed"
            otherWeaponStrength = 0
        
        return(self.compete(other,weaponStat,weaponSkill,otherWeaponStat,otherWeaponSkill,advantage+weaponStrength-otherWeaponStrength+other.wounds-self.wounds))

    def setpos(self,pos):
        game.map.grid[self.pos[0]][self.pos[1]].players.remove(self)
        self.pos = list(pos)
        game.map.grid[self.pos[0]][self.pos[1]].players.append(self)

    def move(self,vec):
        if game.map.is_valid((self.pos[0]+vec[0],self.pos[1]+vec[1])):
            self.setpos((self.pos[0]+vec[0],self.pos[1]+vec[1]))
            return(True)
        else:
            return(False)

    def kill(self):
        game.map.grid[self.pos[0]][self.pos[1]].players.remove(self)
        self.live = False
        game.players.remove(self)
        game.fallen.append(self)

    def loot(self,other,quantity="all"):
        if quantity == "all":   quantity = len(other.inventory)
        stolen = []
        discarded = []
        for i in range(quantity):
            if other.inventory:
                options = []
                for item in other.inventory:
                    if not (item in self.inventory and not "stackable" in item.tags):
                        options.append(item)
                if options:
                    item = random.choice(options)
                    other.inventory.remove(item)
                    self.inventory.append(item)
                    stolen.append(item)
                else:
                    item = random.choice(other.inventory)
                    other.inventory.remove(item)
                    discarded.append(item)
                
        if stolen:
            lst = [item.an() + " "+item.name for item in stolen]
            st = ""
            for i in range(len(lst)-1):
                st += lst[i]
                st += ", "
            if len(lst)>1:
                st += ("and ")
            st += lst[-1]
            printf(self.name + " loots " + st +" from "+other.name+".")

        else:
            printf(self.name + " tries to loot " + other.name + ", but cannot find anything valuable.")
        
class Item:
    def __init__(self,name,tags = None,values = None):
        self.name = name
        self.tags = tags
        self.values = values

        if not tags:
            self.tags = []

        if not values:
            self.values = {}

    def an(self):
        return({True:"an",False:"a"}[self.name[0] in "aeiouAEIOU"])
    
class Cell:
    def __init__(self,biome = "woods"):
        self.players = []
        self.biome = biome

class Map:
    def __init__(self,dims):
        self.dims = dims
        self.cells = []
        self.grid =  [[Cell() for i in range(dims[1])] for i in range(dims[0])]
        for x in self.grid:
            for y in x:
                self.cells.append(y)
                
    def is_valid(self,pos):
        if pos[0]<self.dims[0] and pos[1]<self.dims[1] and pos[0]>=0 and pos[1]>=0:
            return(True)
        return(False)

class Table:
    def __init__(self,contents,bigN=0):
        self.contents = contents
        self.weights = contents.values()
        self.items = contents.keys()
        self.total = sum(self.weights)
        self.intervals = [sum(float(item) for item in self.weights[0:n+1]) for n in range(len(self.weights))]
        if bigN == 0:
            bigN = self.total
        self.intervals.append(bigN)
    def fish(self):
        target = random.randint(1,self.intervals[-1])
        for i in range(len(self.intervals)-1):
            if self.intervals[i] > target:
                return(self.items[i])
        return(None)
        

sharpStick = Item("Sharpened Stick",["stabbing","weapon","flammable","crafted"],{"weaponStrength":1,"skill":"Stabbing","stat":"Strength"}) #weaponStrength is usually 1, 2 is good, 3 is insane.
sword = Item("Sword",["stabbing","weapon","flammable"],{"weaponStrength":2,"skill":"Stabbing","stat":"Dexterity"})
handbow = Item("Hand-made Bow",["shooting","ranged","weapon","flammable","crafted"],{"weaponStrength":1,"skill":"Shooting","stat":"Dexterity"})
lightsaber = Item("Lightsaber",["stabbing","weapon"],{"weaponStrength":4,"skill":"Stabbing","stat":"Dexterity"})

testTable = Table({
sharpStick : 100,
sword : 50,
handbow : 75
    },2000)

cornucopiaTable = Table({
sharpStick : 1000,
sword : 500,
handbow : 750,
lightsaber : 1
    })



class Game(object):
    def main(self,pause = False):
        if self.turn == 0 and len(self.players)>1:
            printf("Cornucopia results:")
            playerList = copy.copy(self.players)
            while len(playerList)>1:
                    P1 = random.choice(playerList)
                    playerList.remove(P1)
                    P2 = random.choice(playerList)
                    playerList.remove(P2)
                    
                    result = P1.fight(P2)
                    victory = result[1]
                    extent = abs(result[0])
                    if victory:
                        victor = P1
                        loser = P2
                    else:
                        victor = P2
                        loser = P1

                    item = None
                    while not item:
                        item = cornucopiaTable.fish()

                    printf(P1.name+" and "+P2.name+" both spot "+item.an()+" "+item.name+" and make a grab for it. There is a brief grapple, but "+victor.name+" emerges victorious! "+loser.name+" slinks away, defeated.")
                    victor.inventory.append(item)
            if playerList:
                printf(playerList[0].name+" "+random.choice(["lives to fight another day.","decides that discretion is the better part of valour and runs away.","turns 540 degrees and nopes the fuck out of there.","is too young to die!"]))
                
            
        while len(self.players)>1:
            self.turn += 1
            printf("Turn: "+str(self.turn))
            self.printf_pos()
            printf(" ")
            self.tick()
            printf(" ")
            self.printf_pos()
            printf("~~~~~~~~")
            if pause:   raw_input()
        return(self.players[0])

    def tick(self):
        self.move_tick()
        self.action_tick()
        self.combat_tick()

    def move_tick(self):
        valid = []
        for player in self.players:
            for vec in ((0,0),(1,0),(-1,0),(0,1),(0,-1)):
                if game.map.is_valid((player.pos[0]+vec[0],player.pos[1]+vec[1])):
                    valid.append(vec)
            player.move(random.choice(valid))

        playerlist = copy.copy(self.players)
        if self.turnSinceFight >= 2 and len(self.players)>=2:
            P1 = random.choice(playerlist)
            playerlist.remove(P1)
            P2 = random.choice(playerlist)
            P1.setpos(P2.pos)
            printf("The gamemakers force "+P1.name+" to "+P2.name+"'"+{True:"",False:"s"}[P2.name[-1] == "s"] + " position!")

    def action_tick(self):
        for player in random.sample(self.players,len(self.players)):
            if not random.randint(0,99):
                #bear trap!
                if player.challenge("Dexterity","Survival") < 2:
                    printf(player.name + " gets their leg caught in a bear trap! They manage to force their leg out, but sustain a very nasty wound.")
                    player.wounds += 2
                else:
                    printf(player.name + " narrowly evades catching their leg in a bear trap, "+{True:"jerking it out of the way at the last moment.",False:"spotting the trap just before they would have stepped on it."}[player.stats["Dexterity"]>player.skills["Survival"]])

            else:
                loot = testTable.fish()
                if loot and not (loot in player.inventory and not "stackable" in loot.tags):
                    printf(player.name+" "+{True:"made",False:"found"}["crafted" in loot.tags]+" "+loot.an()+" "+loot.name+"!")
                    player.inventory.append(loot)

    def combat_tick(self):
        fight = False
        for cell in self.map.cells:
            if cell.players:
                playerList = copy.copy(cell.players)
                while len(playerList)>1:
                    P1 = random.choice(playerList)
                    playerList.remove(P1)
                    P2 = random.choice(playerList)
                    playerList.remove(P2)

                    result = P1.fight(P2)
                    victory = result[1]
                    extent = abs(result[0])
                    if victory:
                        victor = P1
                        loser = P2
                    else:
                        victor = P2
                        loser = P1
                    printf(victor.name + " defeats "+ loser.name + ".")
                    fight = True
                    self.turnSinceFight = 0
                    if extent + loser.wounds >= KILL_DIFFICULTY or len(game.players) <= LETHAL_POPULATION:
                        outcome = "kill"
                        if victor.getWeapon()[0]:
                            weapText = victor.getWeapon()[0].an() + " " + victor.getWeapon()[0].name
                        else:
                            weapText = "their bare hands"
                        printf(victor.name+" kills "+loser.name+" with "+weapText+"!")
                        victor.kills.append(loser)
                        loser.kill()
                        victor.loot(loser)
                    elif extent >= 2:
                        outcome = "nastywound"
                        loser.wounds += 2
                        if victor.getWeapon()[0]:
                            weapText = victor.getWeapon()[0].name
                        else:
                            weapText = random.choice(["battery","bludgeoning","assault"])
                        printf(loser.name+" manages to escape, but sustains a nasty wound from "+victor.name+"'s "+weapText)
                        
                    elif extent >= 1 and loser.inventory and random.randint(0,2):
                        outcome = "loot"
                        victor.loot(loser,1)
                    elif extent >= 1:
                        outcome = "wound"
                        loser.wounds += 1
                        if victor.getWeapon()[0]:
                            weapText = victor.getWeapon()[0].name
                        else:
                            weapText = random.choice(["battery","bludgeoning","assault"])
                        printf(loser.name+" manages to escape, but sustains a wound from "+victor.name+"'s "+weapText)
                    else:
                        outcome = "escape"
                        printf(loser.name+" escapes unharmed.")
        if not fight:
            self.turnSinceFight += 1
                        

    def printf_pos(self):
        for player in self.players:
            printf(player.name+": "+str(player.pos[0])+","+str(player.pos[1]))

def reset():
    global game,A,B,C
    game = Game()
    game.items = []
    game.players = []
    game.fallen = []
    game.turn = 0
    game.turnSinceFight = 0
    game.map = Map((5,5))


    Patrick = Contestant("Patrick",skills = {"Stabbing":1})
    Sofia = Contestant("Sofia",skills = {"Stabbing":3},stats = {"Dexterity":3})
    Oliver = Contestant("Oliver",skills = {"Stabbing":1},stats = {"Strength":1},inventory = [lightsaber])
    Luke = Contestant("Luke",skills = {"Shooting":2,"Unarmed":2})
    Kimbal = Contestant("Kimbal",stats={"Strength":4})

    game.players = [Patrick,Sofia,Oliver,Luke,Kimbal]

reset()

verbose = True

game.main()

printf("/////////////////////////")
printf("Victor:     "+game.players[0].name)
printf("Inventory:  "+", ".join([i.name for i in game.players[0].inventory]))
printf("Kills:      "+str(len(game.players[0].kills)) + " (" + ", ".join([i.name for i in game.players[0].kills]) + ")")

def test(n):
    reset()
    wins = dict([(player.name,0) for player in game.players])
    for i in range(n):
        reset()
        game.main()
        wins[game.players[0].name] += 1
    return(wins)

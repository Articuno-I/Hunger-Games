import random,copy,sys,math

try:
    import pygame
    import time
    pygame_installed = True
except:
    pygame_installed = False

mode = "normal"

KILL_DIFFICULTY = 5
LETHAL_POPULATION = 3

CELL_SIZE = 50
FONT_SIZE = 50

MUT_CHANCE = 30 #out of 100

verbose = True
logging = True
waiting = True
pygame_installed = True and pygame_installed
log = ""

def printf(text):
    if logging:
        global log
        log += text
        log += "\n"
        
        logfile = open("log.txt","w")
        logfile.write(log)
        logfile.close()

    if verbose:
        print(text)

def displayItemList(items):
    lst = [item.an() + " "+item.name for item in items]
    lst2 = {}
    for i in lst:
        if not i in lst2:
            lst2[i]=1
        else:
            lst2[i] += 1
    st = ""
    for i in lst2:
        st += i + {True:" (x"+str(lst2[i])+")",False:""}[lst2[i]>1]
        st += ", "
    return(st)

class Contestant:
    def __init__(self,name,stats = None,skills = None,inventory = None, pos = "c"): #stats out of 4, 2 is average, skills out of 5, 0 is average.
        self.name = name
        self.stats = stats
        self.skills = skills
        self.kills = []
        self.inventory = inventory
        self.pos = pos
        self.live = True

        self.stats = {"Strength":2,"Dexterity":2,"Intelligence":2}
        self.skills = {"Survival":0,"Melee":0,"Unarmed":0,"Shooting":0,"First Aid":0,"Throwing":0,"Explosives":0}

        self.wounds = 0
        self.wound_ticks = []

        self.hunger = 100

        if stats:
            for stat in stats:
                self.stats[stat] = stats[stat]
        if skills:
            for skill in skills:
                self.skills[skill] = skills[skill]

        if not inventory:
            self.inventory = []

        if pos == "c":
            self.pos = (game.map.dims[0]/2,game.map.dims[1]/2)

    def challenge(self,stat,skill):
        total = {False:self.stats[stat],True:0}[stat == False] + {False:self.skills[skill],True:0}[skill == False]
        wins = 0
        for i in range(total):
            wins += {False:0,True:1}[random.randint(0,1) == 1]
        return(wins)

    def compete(self,other,selfstat,selfskill,otherstat = None,otherskill = None,advantage=0,otheradvantage=0):
        if not otherstat:
            otherstat = selfstat
        if not otherskill:
            otherskill = selfskill
        
        selfTotal = self.stats[selfstat] + self.skills[selfskill]
        otherTotal = other.stats[otherstat] + other.skills[otherskill]

        selfTotal += advantage
        otherTotal += otheradvantage

        selfTotal = max(0,selfTotal)
        otherTotal = max(0,otherTotal)
        
        selfWins = 0

        otherWins = 0

        for i in range(selfTotal):
            selfWins += {False:0,True:1}[random.randint(0,1) == 1]

        for i in range(otherTotal):
            otherWins += {False:0,True:1}[random.randint(0,1) == 1]

        #printf((self.name,selfTotal,selfWins))
        #printf((other.name,otherTotal,otherWins))
            
        if selfWins > otherWins:
            victory = True
        elif selfWins < otherWins:
            victory = False
        else:
            victory = random.randint(0,1) == 1

        return((selfWins-otherWins,victory))

    def getCell(self):
        return(game.map.grid[self.pos[0]][self.pos[1]])

    def getDistance(self,other):
        return(((self.pos[0]-other.pos[0])**2+(self.pos[1]-other.pos[1])**2)**0.5)

    def getNearest(self):
        distance = 99
        target = False
        for player in game.players:
            if player != self:
                tdistance = player.getDistance(self)
                if tdistance<distance:
                    target = player
                    distance = tdistance
        return(target)

    def getDir(self,pos):
        if abs(self.pos[0] - pos[0]) >= abs(self.pos[1] - pos[1]):
            if self.pos[0] - pos[0] > 0:
                return((-1,0))
            elif self.pos[0] - pos[0] < 0:
                return((1,0))
        else:
            if self.pos[1] - pos[1] > 0:
                return((0,-1))
            elif self.pos[1] - pos[1] < 0:
                return((0,1))
        return((0,0))

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
            if self.skills[weapon.getSkill(self)] + weapon.values["weaponStrength"] + self.stats[weapon.getStat(self)] + self.getCell().biome.get_bonus(weapon) >= fStrength:
                fStrength = self.skills[weapon.getSkill(self)] + weapon.values["weaponStrength"] + self.stats[weapon.getStat(self)] + self.getCell().biome.get_bonus(weapon)
                wChoice = weapon
        return(wChoice,fStrength)

    def fight(self,other):
        weapon, weapBonus = self.getWeapon()
        otherWeapon, otherWeapBonus = other.getWeapon()

        hungerBonus, otherHungerBonus = 0,0

        if self.hunger <=20:
            otherHungerBonus += 2
        elif self.hunger <= 40:
            otherHungerBonus += 1

        if other.hunger <= 20:
            hungerBonus += 2
        elif other.hunger <= 40:
            hungerBonus += 1

        if weapon:
            weaponStat = weapon.getStat(self)
            weaponSkill = weapon.getSkill(self)
            weaponStrength = weapon.values["weaponStrength"]
            biomeBonus = self.getCell().biome.get_bonus(weapon)
            if "durability" in weapon.values:
                if random.randint(0,100)>weapon.values["durability"]:
                    self.inventory.remove(weapon)
                    printf(self.name+"'s "+weapon.name+" breaks!")
            elif "consumable" in weapon.tags:
                self.inventory.remove(weapon)
                printf(self.name + " uses their "+weapon.name+".")
        else:
            weaponStat = "Strength"
            weaponSkill = "Unarmed"
            weaponStrength = 0
            biomeBonus = 0
        if otherWeapon:
            otherWeaponStat = otherWeapon.getStat(other)
            otherWeaponSkill = otherWeapon.getSkill(other)
            otherWeaponStrength = otherWeapon.values["weaponStrength"]
            otherBiomeBonus = other.getCell().biome.get_bonus(otherWeapon)
        else:
            otherWeaponStat = "Strength"
            otherWeaponSkill = "Unarmed"
            otherWeaponStrength = 0
            otherBiomeBonus = 0
        
        return(self.compete(other,weaponStat,weaponSkill,otherWeaponStat,otherWeaponSkill,weaponStrength+other.wounds+biomeBonus-otherHungerBonus,otherWeaponStrength+self.wounds+otherBiomeBonus-hungerBonus))

    def wound(self,number):
        for i in range(number):
            self.wounds += 1
            self.wound_ticks.append(random.randint(6,9))

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
            printf(self.name + " loots " + displayItemList(stolen) +" from "+other.name+".")

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

    def getSkill(self,player):
        if type(self.values["skill"]) == type("String!"):
            return(self.values["skill"])
        else:
            maxvalue = 0
            target = None
            for i in range(len(self.values["skill"])):
                if player.skills[self.values["skill"][i]] + player.stats[self.values["stat"][i]] > maxvalue:
                    target = self.values["skill"][i]
                    maxvalue = player.skills[self.values["skill"][i]] + player.stats[self.values["stat"][i]]
            return(target)

    def getStat(self,player):
        if type(self.values["stat"]) == type("String!"):
            return(self.values["stat"])
        else:
            maxvalue = 0
            target = None
            for i in range(len(self.values["stat"])):
                if player.skills[self.values["skill"][i]] + player.stats[self.values["stat"][i]] > maxvalue:
                    target = self.values["stat"][i]
                    maxvalue = player.skills[self.values["skill"][i]] + player.stats[self.values["stat"][i]]
            return(target)


class Cell:
    def __init__(self,pos,biome = None):
        self.players = []
        self.biome = biome
        self.pos = pos
        
        if biome:
            self.lootTable = biome.table
            
    def list_names(self):
        return([player.name for player in self.players])

    def generate(self):
        
        if self.biome:
            pass
        else:
            surrounding = []
            for d in ((-1,0),(1,0),(0,1),(0,-1)):
                try:
                    if game.map.grid[self.pos[0]+d[0]][self.pos[1]+d[1]].biome:
                        surrounding.append(game.map.grid[self.pos[0]+d[0]][self.pos[1]+d[1]].biome)
                except:
                    pass
            if (not surrounding) or random.randint(0,100)<MUT_CHANCE:
                self.biome = random.choice(biomes)
                self.lootTable = self.biome.table
            else:
                self.biome = random.choice(surrounding)
                self.lootTable = self.biome.table

        for d in ((-1,0),(1,0),(0,1),(0,-1)):
            try:
                if not game.map.grid[self.pos[0]+d[0]][self.pos[1]+d[1]].biome:
                    game.map.grid[self.pos[0]+d[0]][self.pos[1]+d[1]].generate()
            except:
                pass
            

class Map:
    def __init__(self,dims):
        self.dims = dims
        self.cells = []
        #self.grid =  [[Cell(random.choice(biomes)) for i in range(dims[1])] for i in range(dims[0])]
        self.grid =  [[Cell((x,y)) for y in range(dims[1])] for x in range(dims[0])]
        self.grid[dims[0]/2][dims[1]/2].biome = woods
        self.grid[dims[0]/2][dims[1]/2].lootTable = woods.table
        

        # Uncomment below for 'Desert Hell Mode'
        #for x in range(4,11):
        #    for y in range(4,11):
        #        self.grid[x][y] = Cell(desert)

        for x in self.grid:
            for y in x:
                self.cells.append(y)
                
    def is_valid(self,pos):
        if pos[0]<self.dims[0] and pos[1]<self.dims[1] and pos[0]>=0 and pos[1]>=0:
            return(True)
        return(False)

    def generate(self):
        self.grid[self.dims[0]/2][self.dims[1]/2].generate()

class Table:
    def __init__(self,contents,bigN=0):
        self.contents = contents
        self.weights = contents.values()
        self.items = contents.keys()
        self.total = sum(self.weights)
        self.intervals = [sum(float(item) for item in self.weights[0:n+1]) for n in range(len(self.weights))]
        if bigN == 0:
            bigN = self.total
        self.bigN = bigN
        self.intervals.append(bigN)
        
    def fish(self):
        target = random.randint(1,self.intervals[-1])
        for i in range(len(self.intervals)-1):
            if self.intervals[i] >= target:
                return(self.items[i])
        return(None)

    def update(self,item,odds):
        ncontents = copy.copy(self.contents)
        ncontents[item] = odds
        return(Table(ncontents,self.bigN))
        
class Biome:
    def __init__(self,name,table,colour,weapon_boost={},dangers = None):
        self.name = name
        self.table = table
        self.colour = colour
        self.weapon_boost = weapon_boost
        self.dangers = dangers

    def get_bonus(self,weapon):
        bonus = 0
        for tag in weapon.tags:
            if tag in self.weapon_boost:
                bonus += self.weapon_boost[tag]
        if "ranged" in weapon.tags and not "melee" in weapon.tags:
            if game.phase == "Night":
                bonus -= 1
        return(int(bonus+{True:0.5,False:-0.5}[bonus>0])) #rounds to nearest whole number; Python always rounds down, so int(0.9) = 0. Adding/subtracting 0.5 changes this to how we would like it to work.

sharpStick = Item("Sharpened Stick",["melee","stabbing","weapon","flammable","crafted"],{"weaponStrength":0,"skill":("Throwing","Melee"),"stat":("Dexterity","Strength"),"durability":80}) #weaponStrength is usually 1, 2 is good, 3 is insane.
sword = Item("Sword",["melee","stabbing","weapon","flammable","slashing"],{"weaponStrength":2,"skill":"Melee","stat":"Dexterity"})
handbow = Item("Hand-made Bow",["shooting","ranged","weapon","flammable","crafted"],{"weaponStrength":1,"skill":"Shooting","stat":"Dexterity","durability":80})
photon = Item("Photon Blaster",["shooting","ranged","weapon"],{"weaponStrength":4,"skill":"Shooting","stat":"Dexterity"})
lightsaber = Item("Lightsaber",["melee","stabbing","weapon","slashing"],{"weaponStrength":4,"skill":"Melee","stat":"Dexterity"})
berries = Item("Handful of Berries",["food","stackable"],{"nutrition":25})
bird_meat = Item("Small Bird (Cooked)",["food","stackable","ranged_find_bonus"],{"nutrition":50})
wellbow = Item("Well Made Bow",["shooting","ranged","weapon","flammable"],{"weaponStrength":2,"skill":"Shooting","stat":"Dexterity"})
energybar = Item("Energy Bar",["food","stackable"],{"nutrition":40})
mace = Item("Mace",["melee","weapon","bashing"],{"weaponStrength":2,"skill":"Melee","stat":"Strength"})
bandage = Item("Bandage",["stackable","medical","crafted"],{"healstrength":1})
firstaid = Item("First Aid Kit",["stackable","medical"],{"healstrength":2})
throwknives = Item("Throwing Knives",["melee","ranged","weapon","throwing"],{"weaponStrength":1,"skill":"Throwing","stat":"Dexterity"})
spear = Item("Spear",["melee","ranged","weapon","throwing"],{"weaponStrength":2,"skill":("Throwing","Melee"),"stat":("Dexterity","Strength")})
dynamite = Item("Dynamite",["explosive","weapon","consumable"],{"weaponStrength":6,"skill":"Explosives","stat":"Intelligence"})

cornucopiaTable = Table({
sword : 500,
mace : 500,
spear : 500,
bandage : 500,
dynamite : 250,
throwknives : 500,
wellbow : 500,
firstaid : 750,
energybar : 750,
lightsaber : {True:999999,False:1}[mode == "spacewar"],
photon : {True:999999,False:1}[mode == "spacewar"]
    })

#BIOME LOOT TABLES

woodsTable = Table({
sharpStick : 100,
sword : 30,
mace : 30,
energybar : 30,
bandage : 50,
handbow : 75,
berries : 150,
spear : 40,
throwknives : 30,
bird_meat : 150
    },1500)

plainsTable = Table({
    sharpStick : 50,
    sword : 20,
    mace : 20,
    spear : 25,
    throwknives : 20,
    energybar : 20,
    handbow : 40,
    berries : 10,
    bandage : 10,
    bird_meat : 200
    },1500)

desertTable = Table({
    bird_meat : 10,
    sharpStick : 10,
    dynamite : 100
    },1500)

spaceTable = Table({
    lightsaber : 10,
    photon : 10
    },1500)

#BIOME DANGER TABLES

woodsDangers = Table({
    "beartrap" : 10
    },2000)

desertDangers = Table ({
    "mirage" : 20
    },2000)

#BIOMES                

woods = Biome("woods",woodsTable,(36,119,0),weapon_boost = {"shooting":-0.5},dangers = woodsDangers)
plains = Biome("plains",plainsTable,(187,255,157),weapon_boost = {"shooting":1})
desert = Biome("desert",desertTable,(239,228,176),dangers = desertDangers)
space = Biome("space",spaceTable,(0,0,50))

biomes = [woods,plains,desert]
if mode == "spacewar":
    biomes = [space]

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
            self.phase = {"Start":"Dawn","Dawn":"Afternoon","Afternoon":"Dusk","Dusk":"Night","Night":"Dawn"}[self.phase]
            if self.phase == "Dawn":
                self.day += 1
            printf("Day: "+str(self.day) + " ("+self.phase+")")
            self.tick()
            printf("~~~~~~~~")
            if pause:   raw_input()
        return(self.players[0])

    def tick(self):
        if pygame_installed:
            self.draw_tick()
        self.move_tick()
        self.printf_pos()
        self.action_tick()
        self.combat_tick()

    def move_tick(self):
        for player in self.players:
            valid = []
            for vec in ((1,0),(-1,0),(0,1),(0,-1)):
                if game.map.is_valid((player.pos[0]+vec[0],player.pos[1]+vec[1])):
                    valid.append(vec)
                    
                nDir = player.getDir(player.getNearest().pos)
                #printf((player.name,player.pos,player.getNearest().name,player.getNearest().pos,(-player.pos[0]--player.getNearest().pos[0],-player.pos[1]--player.getNearest().pos[1]),nDir))
                for i in range(int(self.turnSinceFight) + len(player.kills)):
                    if nDir in valid:
                        valid.append(nDir)
            #printf(valid)
            selected = random.choice(valid)
            #printf(selected)
            player.move(selected)

        playerlist = copy.copy(self.players)
        if self.turnSinceFight >= 12 and len(self.players)>=2:
            distance = 999
            pair = ()
            for player in playerlist:
                for other in playerlist:
                    if other != player:
                        if player.getDistance(other) < distance:
                            pair = (player,other)
                            distance = ((player.pos[0]-other.pos[0])**2 + (player.pos[1]-other.pos[1])**2)**0.5
            P1 = pair[0]
            P2 = pair[1]
            P1.setpos(P2.pos)
            printf("The gamemakers force "+P1.name+" to "+P2.name+"'"+{True:"",False:"s"}[P2.name[-1] == "s"] + " position!")

    def action_tick(self):
        for player in random.sample(self.players,len(self.players)):
            for i in range(len(player.wound_ticks)):
                player.wound_ticks[i] -= 1
                if player.wound_ticks[i] == 0:
                    player.wounds -= 1
                    printf(player.name + " managed to recover from "+{True:"one of their injuries!",False:"their injury!"}[player.wounds>0])
            while 0 in player.wound_ticks:
                player.wound_ticks.remove(0)
            if player.wounds:
                meds = player.getTagged("medical")
                if meds:
                    best = None
                    besth = 0
                    for med in meds:
                        if abs(med.values["healstrength"]-player.wounds)<abs(besth-player.wounds):
                            best = med
                            besth = med.values["healstrength"]
                    if best:
                        player.inventory.remove(best)
                        heals = min(best.values["healstrength"],player.wounds)
                        printf(player.name + " attempts to use "+best.name+" to treat their wound"+{True:"s",False:""}[heals>=2]+".")
                        if player.challenge("Intelligence","First Aid")>=2:
                            printf(player.name+" is successful and treats "+str(heals) + " wound"+{True:"s",False:""}[heals>=2]+"!")
                            for i in range(heals):
                                player.wounds -= 1
                                player.wound_ticks.remove(max(player.wound_ticks))
                        else:
                            printf(player.name + " is unsuccessful and wastes the "+best.name+".")
                    
            if player.getCell().biome.dangers:
                danger = player.getCell().biome.dangers.fish()
                if danger == "beartrap":
                    #bear trap!
                    if player.challenge("Dexterity","Survival") < 2:
                        printf(player.name + " gets their leg caught in a bear trap! They manage to force their leg out, but sustain a very nasty wound.")
                        player.wound(2)
                    else:
                        printf(player.name + " narrowly evades catching their leg in a bear trap, "+{True:"jerking it out of the way at the last moment.",False:"spotting the trap just before they would have stepped on it."}[player.stats["Dexterity"]>player.skills["Survival"]])
                elif danger == "mirage":
                    difficulty = 1
                    if player.hunger <= 20:
                        difficulty += 2
                    elif player.hunger <= 40:
                        difficulty += 1
                    if player.challenge("Intelligence","Survival") < difficulty:
                        printf(player.name + " thinks that they can see something in the distance! They spend hours chasing after it before the mirage fades.")
                        player.hunger -= random.randint(0,5+player.hunger/6)
                    else:
                        printf(player.name + " thinks that they can make out something in the distance, but after a moment blinks, shakes their head and can see nothing.")


            tries = 0
            loot = None
            lootTable = player.getCell().lootTable
            if player.getTagged("ranged"):
                for item in lootTable.items:
                    if "ranged_find_bonus" in item.tags:
                        lootTable = lootTable.update(item,lootTable.contents[item]*2)
                        #printf(player.name + "'s ranged weapon gives them a bonus to hunting!")
            
            while tries <= player.skills["Survival"] and not loot:
                loot = lootTable.fish()
                tries += 1
            if loot and not (loot in player.inventory and not "stackable" in loot.tags):
                printf(player.name+" "+{True:"made",False:"found"}["crafted" in loot.tags]+" "+loot.an()+" "+loot.name+"!")
                player.inventory.append(loot)

            if mode != "spacewar":
                player.hunger -= random.randint(0,5+player.hunger/6)
            if player.hunger<=40 and player.getTagged("food"):
                while player.getTagged("food") and player.hunger<=60:
                    printf(player.name + " eats " + player.getTagged("food")[0].name + ".")
                    player.hunger += player.getTagged("food")[0].values["nutrition"]
                    player.inventory.remove(player.getTagged("food")[0])
            elif player.hunger <= 0 and len(game.players)>2:
                printf(player.name + " starved to death!")
                player.kill()
            elif player.hunger <= 20:
                printf(player.name + " is starving!")
            elif player.hunger <= 40:
                printf(player.name + " is hungry, but has nothing to eat!")
                

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

                    weapon1 = P1.getWeapon()[0]
                    weapon2 = P2.getWeapon()[0]
                    result = P1.fight(P2)
                    victory = result[1]
                    extent = abs(result[0])
                    if victory:
                        victor = P1
                        weapon = weapon1
                        loser = P2
                    else:
                        victor = P2
                        weapon = weapon2
                        loser = P1
                    printf(victor.name + " defeats "+ loser.name + ".")
                    fight = True
                    self.turnSinceFight = 0
                        
                    if extent + loser.wounds >= KILL_DIFFICULTY or len(game.players) <= LETHAL_POPULATION:
                        outcome = "kill"
                        if weapon:
                            weapText = weapon.an() + " " + weapon.name
                        else:
                            weapText = "their bare hands"
                            
                        if extent >= KILL_DIFFICULTY-1 and weapon:
                            if "slashing" in weapon.tags:
                                printf(victor.name + " DECAPITATES " + loser.name + " with a fell swoop of their "+weapon.name + "!")
                            elif "stabbing" in weapon.tags:
                                printf(victor.name + " IMPALES " + loser.name + " with a powerful thrust of their " + weapon.name + "!")
                            elif "explosive" in weapon.tags:
                                printf(victor.name + " VAPORIZES " + loser.name + " with their "+weapon.name +"!")
                            else:
                                printf(victor.name+" kills "+loser.name+" with "+weapText+"!")
                                
                        else:
                            printf(victor.name+" kills "+loser.name+" with "+weapText+"!")
                        victor.kills.append(loser)
                        loser.kill()
                        victor.loot(loser)
                    elif extent >= 2:
                        outcome = "nastywound"
                        loser.wound(2)
                        if weapon:
                            weapText = weapon.name
                        else:
                            weapText = random.choice(["bludgeoning","assault"])
                        printf(loser.name+" manages to escape, but sustains a nasty wound from "+victor.name+"'s "+weapText + "!")
                        
                    elif extent >= 1 and loser.inventory and random.randint(0,2):
                        outcome = "loot"
                        victor.loot(loser,1)
                    elif extent >= 1:
                        outcome = "wound"
                        loser.wound(1)
                        if weapon:
                            weapText = weapon.name
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
            printf(player.name+": ["+str(player.pos[0])+","+str(player.pos[1])+"] ("+player.getCell().biome.name+") HNG: "+str(player.hunger))

    def draw_map(self):
        biomeSurf = pygame.surface.Surface((CELL_SIZE,CELL_SIZE))
        mapSurf = pygame.surface.Surface((biomeSurf.get_width() * self.map.dims[0],biomeSurf.get_height() * self.map.dims[1]))
        for x in range(self.map.dims[0]):
            for y in range(self.map.dims[1]):
                biomeSurf.fill(self.map.grid[x][y].biome.colour)

                names = self.map.grid[x][y].list_names()
                if names:
                    for i in range(len(names)):
                        name = names[i]
                        textcol = (0,0,0)
                        if pygame.Color(self.map.grid[x][y].biome.colour[0],self.map.grid[x][y].biome.colour[1],self.map.grid[x][y].biome.colour[2]).hsla[2]<40:
                            textcol = (255,255,255)
                        firstPass = Calibri.render(name,1,textcol)
                        secondPass = pygame.transform.scale(firstPass,(CELL_SIZE,CELL_SIZE/len(names)))
                        biomeSurf.blit(secondPass,(0,i*CELL_SIZE/len(names)))
                
                mapSurf.blit(biomeSurf,(x*biomeSurf.get_width(),y*biomeSurf.get_height()))
        return(mapSurf)

    def draw_tick(self):
        screen.fill((0,0,0))
        drawn_map = self.draw_map()
        if self.phase == "Night":
            drawn_map.blit(night_veil,(0,0))
        elif self.phase in ("Dawn","Dusk"):
            drawn_map.blit(dawn_veil,(0,0))
        screen.blit(drawn_map,(0,0))

        pygame.display.flip()

        while waiting:
            event = pygame.event.poll()
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    break

            time.sleep(0.05)

def reset():
    global game,A,B,C
    game = Game()
    game.items = []
    game.players = []
    game.fallen = []
    game.turn = 0
    game.day = 0
    game.phase = "Start"
    game.turnSinceFight = 0
    game.map = Map((15,15))
    game.map.generate()


    Patrick = Contestant("Patrick",stats = {"Intelligence":3},skills = {"Melee":1})
    Sofia = Contestant("Sofia",skills = {"Melee":5},stats = {"Dexterity":3})
    Oliver = Contestant("Oliver",skills = {"Melee":1},stats = {"Strength":1,"Intelligence":3},inventory = [])
    Luke = Contestant("Luke",skills = {"Shooting":3,"Unarmed":2,"Intelligence":3})
    Kimbal = Contestant("Kimbal",stats={"Strength":4,"Intelligence":3})
    Phyllie = Contestant("Phyllie",stats = {"Intelligence":3})
    Deborah = Contestant("Deborah")
    Chloe = Contestant("Chloe")
    Josh = Contestant("Josh")
    Uhoh = Contestant("Katniss",skills = {"Shooting":5,"Survival":2,"Unarmed":1,"Melee":1},stats = {"Dexterity":3})

    game.players = [Patrick,Sofia,Oliver,Luke,Kimbal,Phyllie,Deborah,Chloe,Josh,Uhoh]

    for player in game.players:
        game.map.grid[player.pos[0]][player.pos[1]].players.append(player)

reset()

if pygame_installed:
    pygame.init()
    Calibri = pygame.font.SysFont("Calibri",FONT_SIZE)
    drawnmap = game.draw_map()
    screen = pygame.display.set_mode(drawnmap.get_size()) #welcome2

    night_veil = pygame.surface.Surface(drawnmap.get_size())
    night_veil.fill((0,0,120))
    night_veil.set_alpha(100)

    dawn_veil = pygame.surface.Surface(drawnmap.get_size())
    dawn_veil.fill((120,95,0))
    dawn_veil.set_alpha(50)
        
    pygame.image.save(drawnmap,"map.png")

game.main()

printf("/////////////////////////")
printf("Victor:     "+game.players[0].name)
printf("Inventory:  "+displayItemList(game.players[0].inventory))
printf("Kills:      "+str(len(game.players[0].kills)) + " (" + ", ".join([i.name for i in game.players[0].kills]) + ")")

if pygame_installed:
    game.draw_tick()

def test(n):
    reset()
    wins = dict([(player.name,0) for player in game.players])
    turns = []
    for i in range(n):
        if not i%200:
            print(i)
        reset()
        game.main()
        wins[game.players[0].name] += 1
        turns.append(game.turn)
    return(wins,sum(turns)/float(n))

while not "Dynamite" in log:
    reset()
    game.main()

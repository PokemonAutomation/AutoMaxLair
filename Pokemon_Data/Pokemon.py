# Pokemon
#   Eric Donders
#   2020-11-27
import math

class Pokemon():
    def __init__(self, Name, Ability, Types, Base_stats, Moves, Level=100, IVs=(15,15,15,15,15,15), EVs=(0,0,0,0,0,0,), Nature=(None,1,1,1,1,1)):
        self.name = Name
        self.ability = Ability
        self.types = Types
        self.base_stats = Base_stats
        self.moves = Moves
        self.level = Level
        self.ivs = IVs
        self.evs = EVs
        self.nature = Nature
        
        PP = []
        for move in Moves:
            PP.append(move.PP)
        self.PP = tuple(PP)

        self.status = None
        self.stat_modifiers = (None,0,0,0,0,0)
        self.recalculate_stats()

    def __str__(self):
        output = self.name+'\n'
        output += self.ability+'\n'
        output += self.types[0]
        if self.types[1] != '':
            output += '/'+self.types[1]
        output += '\nLevel %i' % self.level
        output += '\nMoves:\n'
        for move in self.moves:
            output += '\t'+str(move)+'\n'
        return output

    def adjust_stats(self, modification):
        for i in range(1,6):
            self.stat_modifiers[i] += modification[i]
        self.recalculate_stats()

    def recalculate_stats(self):
        self.stats = [math.floor((2*self.base_stats[0]+self.ivs[0]+math.floor(self.evs[0]/4))*self.level/100)+self.level+10]
        for i in range(1,6):
            self.stats.append(math.floor((math.floor((2*self.base_stats[i]+self.ivs[i]+math.floor(self.evs[i]/4))*self.level/100)+5)*self.nature[i]))
            if self.stat_modifiers[i] >= 0:
                if self.stat_modifiers[i] > 6:
                    self.stat_modifiers[i] = 6
                self.stats[i] *= (2+self.stat_modifiers[i])/2
            elif self.stat_modifiers[i] < 0:
                if self.stat_modifiers[i] < -6:
                    self.stat_modifiers[i] = -6
                self.stats[i] *= 2/(2+self.stat_modifiers[i])

# Pokemon
#   Eric Donders
#   2020-11-27
import math, copy

class Pokemon():
    def __init__(self, Name, Ability, Types, Base_stats, Moves, Max_moves, Level=100, IVs=(15,15,15,15,15,15), EVs=(0,0,0,0,0,0,), Nature=(None,1,1,1,1,1)):
        self.name = Name
        self.ability = Ability
        self.types = Types
        self.base_stats = Base_stats
        self.moves = Moves
        self.max_moves = Max_moves
        self.level = Level
        self.ivs = IVs
        self.evs = EVs
        self.nature = Nature
        
        self.PP = []
        for move in Moves:
            self.PP.append(move.PP)

        self.restore()
        self.reset_stats()

    def __str__(self):
        return self.name
##        output = self.name+'\n'
##        output += self.ability+'\n'
##        output += self.types[0]
##        if self.types[1] != '':
##            output += '/'+self.types[1]
##        output += '\nLevel %i' % self.level
##        output += '\nMoves:\n'
##        for move in self.moves:
##            output += '\t'+str(move)+'\n'
##        return output

    def __copy__(self):
        copied_pokemon = type(self)(self.name, self.ability, self.types, self.base_stats, self.moves, self.max_moves, self.level, self.ivs, self.evs, self.nature)
        copied_pokemon.PP = copy.deepcopy(self.PP)
        copied_pokemon.HP = copy.deepcopy(self.HP)
        copied_pokemon.status = self.status
        copied_pokemon.stat_modifiers = self.stat_modifiers
        copied_pokemon.dynamax = self.dynamax
        return copied_pokemon

    def restore(self):
        """Restore HP, PP, and status effects."""
        self.HP = 1
        for i in range(len(self.PP)):
            self.PP[i] = self.moves[i].PP
        self.status = None

    def reset_stats(self):
        """Reset stat changes."""
        self.stat_modifiers = (None,0,0,0,0,0)
        self.recalculate_stats()
        self.dynamax = False

    def adjust_stats(self, modification):
        for i in range(1,6):
            self.stat_modifiers[i] += modification[i]
        self.recalculate_stats()

    def recalculate_stats(self):
        self.stats = [(math.floor((2*self.base_stats[0]+self.ivs[0]+math.floor(self.evs[0]/4))*self.level/100)+self.level+10) * self.HP]
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

    def toggle_dynamax(self):
        self.dynamax = not self.dynamax

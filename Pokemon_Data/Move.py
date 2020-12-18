# Move
#   Eric Donders
#   2020-11-27
import copy

class Move():
    def __init__(self, Name, Type, Category, Power, Accuracy, PP, TM, Effect, Probability, is_spread=False, correction_factor=1):
        self.name = Name
        self.type = Type
        self.category = Category
        self.base_power = Power
        self.accuracy = Accuracy
        self.PP = PP
        self.TM = TM
        self.effect = Effect
        self.probability = Probability
        self.is_spread = is_spread
        self.correction_factor = correction_factor

        self.power = Power*correction_factor

    def __str__(self):
        return self.name

    def __copy__(self):
        return type(self)(self.name, self.type, self.category, self.power, self.accuracy, copy.deepcopy(self.PP), self.TM, self.effect, self.probability, self.is_spread, self.correction_factor)

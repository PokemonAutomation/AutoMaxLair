# Move
#   Eric Donders
#   2020-11-27

class Move():
    def __init__(self, Name, Type, Category, Power, Accuracy, PP, TM, Effect, Probability):
        self.name = Name
        self.type = Type
        self.category = Category
        self.power = Power
        self.accuracy = Accuracy
        self.PP = PP
        self.TM = TM
        self.effect = Effect
        self.probability = Probability

    def __str__(self):
        return self.name

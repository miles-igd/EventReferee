import json
import data

def bounds(min_, max_, n):
    '''Helper function to return min, or max or inbetween if in bounds'''
    return min(max_, max(min_, n))

class ConfigError(Exception):
    pass

class Instance():
    @classmethod
    def make(cls, id, config):
        try: 
            return cls(id, json.loads(config))
        except ValueError:
            return cls(id)

class BoggleInstance(Instance):
    '''
    Class explicit variables:
        score: scores for word length, should not be configurable, 
                otherwise scores database can be unreliable
        die16: original 4x4 dice, die25: original* 5x5 dice configuration
        explicit: dictionary containing board sizes that give explicit dice, 
                otherwise use a letter generator.

    Config dictionary arguments:
        {
        "rounds": 5, (minimum: 1, maximum: 16)
        "timer": 180, (minimum: 10, maximum: 600)
        "size": 5 (minimum: 3, maximum: 9)
        }
    '''
    name = 'boggle'
    score = { 3: 1, 4: 1,
               5: 2,
               6: 3,
               7: 5,
               8: 11}
    die16 = ('AACIOT','AHMORS','EGKLUY','ABILTY','ACDEMP',
                'EGINTV','GILRUW','ELPSTU','DENOSW','ACELRS',
                'ABJMOQ','EEFHIY','EHINPS','DKNOTU','ADENVZ',
                'BIFORX')
    die25 = ('AAAFRS','AAEEEE','AAFIRS','ADENNN','AEEEEM',
             'AEEGMU','AEGMNN','AFIRSY','BJKQXZ','CCNSTW',
             'CEIILT','CEIPST','DDLNOR','DHHLOR','IKLMQU',
             'DHLNOR','EIIITT','CEILPT','EMOTTT','ENSSSU',
             'FIPRSY','GORRVW','HIPRRY','NOOTUW','OOOTTU')
    explicit = {4: die16, 5: die25}

    defaults = {"rounds": 5,
                "timer": 180,
                "size": 5}

    def __init__(self, id, config = {}):
        self.id = id
        
        self.rounds = bounds(1, 16, config.get(rounds, self.defaults['rounds']))
        self.timer =  bounds(10, 600, config.get(timer, self.defaults['timer']))
        self.size =  bounds(3, 9, config.get(size, self.defaults['size']))

    def __repr__(self):
        return f'{self.id}: rounds({self.rounds}), timer({self.timer}), size({self.size})'



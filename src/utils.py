from colorsys import hsv_to_rgb
import random 

def createCombos(groups: list[list[any]]):
    if len(groups) == 0: 
        return [[]]
    else:
        rest = createCombos(groups[1:])
        return [[item] + r for r in rest for item in groups[0]]
    
def getRandomColor() -> tuple[int,int,int]:
    rgbDecimal = hsv_to_rgb(random.random(),0.7,0.65)
    return map(lambda x: int(x*255),rgbDecimal)

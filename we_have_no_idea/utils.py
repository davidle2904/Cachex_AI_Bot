def hexDistance(hex1, hex2):
    return (abs(hex1[0] - hex2[0]) + abs(hex1[1] - hex2[1]) + abs(hex1[0] + hex1[1] - hex2[0] - hex2[1])) / 2

def hexChainDistance(hex, hexList):
    return min(map(lambda x: hexDistance(hex, x), hexList))

def changeSide(token):
    if token == "red":
        return "blue"
    else:
        return "red"
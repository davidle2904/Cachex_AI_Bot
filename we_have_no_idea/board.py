"""
Acknowledgement:
This file is the modified version of the board.py file from the referee module
that is provided with the skeleton-code-B repository for following:
    COMP30024_2022_SM1 Project Part B
"""


"""
Provide a class to maintain the state of a Cachex game board, including
some helper methods to assist in updating and searching the board.

NOTE:
This board representation is designed to be used internally by the referee
for the purposes of validating actions and displaying the result of the game.
Each player is expected to store its own internal representation of the board
for use in informing decisions about which action to choose each turn. Please
don't assume this class is an "ideal" board representation for your own agent; 
you should think carefully about how to design your own data structures for 
representing the state of a game, with respect to your chosen strategy. 
"""

from collections import defaultdict
from queue import Queue
from numpy import zeros, array, roll, vectorize, count_nonzero, reshape
from we_have_no_idea.utils import hexChainDistance
import heapq

# Utility function to add two coord tuples
_ADD = lambda a, b: (a[0] + b[0], a[1] + b[1])

# Neighbour hex steps in clockwise order
_HEX_STEPS = array([(1, -1), (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1)], 
    dtype="i,i")

# Pre-compute diamond capture patterns - each capture pattern is a 
# list of offset steps:
# [opposite offset, neighbour 1 offset, neighbour 2 offset]
#
# Note that the "opposite cell" offset is actually the sum of
# the two neighbouring cell offsets (for a given diamond formation)
#
# Formed diamond patterns are either "longways", in which case the
# neighbours are adjacent to each other (roll 1), OR "sideways", in
# which case the neighbours are spaced apart (roll 2). This means
# for a given cell, it is part of 6 + 6 possible diamonds.
_CAPTURE_PATTERNS = [[_ADD(n1, n2), n1, n2] 
    for n1, n2 in 
        list(zip(_HEX_STEPS, roll(_HEX_STEPS, 1))) + 
        list(zip(_HEX_STEPS, roll(_HEX_STEPS, 2)))]

# Maps between player string and internal token type
_TOKEN_MAP_OUT = { 0: None, 1: "red", 2: "blue" }
_TOKEN_MAP_IN = {v: k for k, v in _TOKEN_MAP_OUT.items()}

# Map between player token types
_SWAP_PLAYER = { 0: 0, 1: 2, 2: 1 }

_PLAYER_AXIS = {
    "red": 0, # Red aims to form path in r/0 axis
    "blue": 1 # Blue aims to form path in q/1 axis
}

class Board:
    def __init__(self, data, n):
        """
        Initialise board of given size n.
        """
        self.n = n
        self._data = data
        self.redPath = None
        self.bluePath = None
        self.redLength = None
        self.blueLength = None
        self.isupdated = False

    def __getitem__(self, coord):
        """
        Get the token at given board coord (r, q).
        """
        return _TOKEN_MAP_OUT[self._data[coord]]

    def __setitem__(self, coord, token):
        """
        Set the token at given board coord (r, q).
        """
        self._data[coord] = _TOKEN_MAP_IN[token]

    def digest(self):
        """
        Digest of the board state (to help with counting repeated states).
        Could use a hash function, but not really necessary for our purposes.
        """
        return self._data.tobytes()

    def swap(self):
        """
        Swap player positions by mirroring the state along the major 
        board axis. This is really just a "matrix transpose" op combined
        with a swap between player token types.
        """
        swap_player_tokens = vectorize(lambda t: _SWAP_PLAYER[t])
        self._data = swap_player_tokens(self._data.transpose())

    def place(self, token, coord):
        """
        Place a token on the board and apply captures if they exist.
        Return coordinates of captured tokens.
        """
        self[coord] = token
        # self.placed = coord
        # self.placedToken = token
        return self._apply_captures(coord)

    def connected_coords(self, start_coord):
        """
        Find connected coordinates from start_coord. This uses the token 
        value of the start_coord cell to determine which other cells are
        connected (e.g., all will be the same value).
        """
        # Get search token type
        token_type = self._data[start_coord]

        # Use bfs from start coordinate
        reachable = set()
        queue = Queue(0)
        queue.put(start_coord)

        while not queue.empty():
            curr_coord = queue.get()
            reachable.add(curr_coord)
            for coord in self._coord_neighbours(curr_coord):
                if coord not in reachable and self._data[coord] == token_type:
                    queue.put(coord)

        return list(reachable)

    def inside_bounds(self, coord):
        """
        True iff coord inside board bounds.
        """
        r, q = coord
        return r >= 0 and r < self.n and q >= 0 and q < self.n

    def is_occupied(self, coord):
        """
        True iff coord is occupied by a token (e.g., not None).
        """
        return self[coord] != None

    def _apply_captures(self, coord):
        """
        Check coord for diamond captures, and apply these to the board
        if they exist. Returns a list of captured token coordinates.
        """
        opp_type = self._data[coord]
        mid_type = _SWAP_PLAYER[opp_type]
        captured = set()

        # Check each capture pattern intersecting with coord
        for pattern in _CAPTURE_PATTERNS:
            coords = [_ADD(coord, s) for s in pattern]
            # No point checking if any coord is outside the board!
            if all(map(self.inside_bounds, coords)):
                tokens = [self._data[coord] for coord in coords]
                if tokens == [opp_type, mid_type, mid_type]:
                    # Capturing has to be deferred in case of overlaps
                    # Both mid cell tokens should be captured
                    captured.update(coords[1:])

        capture = False
        # Remove any captured tokens
        for coord in captured:
            capture = True
            self[coord] = None
        self.captured = capture
        if self.captured:
            self.capset = captured
        return list(captured)

    def undo_place(self):
        """
        Undo the last placed token.
        """
        self[self.placed] = None
        if self.captured:
            for coord in self.capset:
                self[coord] = _TOKEN_MAP_OUT[_SWAP_PLAYER[_TOKEN_MAP_IN[self.placedToken]]]
            self.captured = False

    def _coord_neighbours(self, coord):
        """
        Returns (within-bounds) neighbouring coordinates for given coord.
        """
        return [_ADD(coord, step) for step in _HEX_STEPS \
            if self.inside_bounds(_ADD(coord, step))]

    def heuristic(self, token, coord):
        """
        Heuristic value for given token.
        """
        occupied = 0
        if token == "red":
            for i in range(coord[0]+1, self.n):
                for j in range(self.n):
                    if self[i, j] == "red":
                        occupied += 1
                        break
            return self.n - coord[0] - occupied -1
        else:
            for j in range(coord[1]+1, self.n):
                for i in range(self.n):
                    if self[i, j] == "blue":
                        occupied += 1
                        break
            return self.n - coord[1] - occupied -1

    def pathSearch(self, token):
        """
        Search for a path from this side to the other side for a token.
        """
        minQueue = []
        gCost = dict()
        parent = dict()
        cloesed_list = defaultdict(bool)

        # if token is red, add first row to the queue with gCost
        if token == "red":
            for i in range(self.n):
                if self[(0, i)] in [token, None]:
                    if self[(0, i)] == token:
                        gCost[(0, i)] = 0
                    else:
                        gCost[(0, i)] = 1
                    heapq.heappush(minQueue, (gCost[(0, i)] + self.heuristic(token, (0, i)), (0, i)))
        else:
            for j in range(self.n):
                if self[(j, 0)] in [token, None]:
                    if self[(j, 0)] == token:
                        gCost[(j, 0)] = 0
                    else:
                        gCost[(j, 0)] = 1
                    heapq.heappush(minQueue, (gCost[(j, 0)] + self.heuristic(token, (j, 0)), (j, 0)))
        while not len(minQueue) == 0:
            curr = heapq.heappop(minQueue)[1]
            if token == "red":
                if curr[0] == self.n-1:
                    temp = curr
                    path = []
                    while temp in parent.keys():
                        path.append(temp)
                        temp = parent[temp]
                    path.append(temp)
                    return path, gCost[curr]
            else:
                if curr[1] == self.n-1:
                    temp = curr
                    path = []
                    while temp in parent.keys():
                        path.append(temp)
                        temp = parent[temp]
                    path.append(temp)
                    return path, gCost[curr]

            if cloesed_list[curr]:
                continue
            else:
                cloesed_list[curr] = True
            for neighbour in self._coord_neighbours(curr):
                if self[neighbour] == token and self[neighbour] not in cloesed_list:
                    if neighbour not in gCost.keys():
                        gCost[neighbour] = gCost[curr]
                        heapq.heappush(minQueue, (gCost[neighbour] + self.heuristic(token, neighbour), neighbour))
                        parent[neighbour] = curr
                    elif gCost[neighbour] > gCost[curr]:
                        gCost[neighbour] = gCost[curr]
                        heapq.heappush(minQueue, (gCost[neighbour] + self.heuristic(token, neighbour), neighbour))
                        parent[neighbour] = curr
                elif self[neighbour] == None:
                    if neighbour not in gCost.keys():
                        gCost[neighbour] = gCost[curr] + 1
                        heapq.heappush(minQueue, (gCost[neighbour] + self.heuristic(token, neighbour), neighbour))
                        parent[neighbour] = curr
                    elif gCost[neighbour] > gCost[curr] + 1:
                        gCost[neighbour] = gCost[curr] + 1
                        heapq.heappush(minQueue, (gCost[neighbour] + self.heuristic(token, neighbour), neighbour))
                        parent[neighbour] = curr
        return [], self.n


    def generateMove(self, token):
        """
        Generate a move for the current player.
        """
        moves = []
        reds = []
        blues = []
        for i in range(self.n):
            for j in range(self.n):
                if self[i, j] == None:
                    moves.append((i, j))
                elif self[i, j] == "red":
                    reds.append((i, j))
                elif self[i, j] == "blue":
                    blues.append((i, j))
        if token == "red":
            if count_nonzero(self._data == 1) > 0 and count_nonzero(self._data == 2) > 0:
                filtered = filter(lambda x: hexChainDistance(x, reds) <= 1 or hexChainDistance(x, blues) <= 1, moves)
            elif count_nonzero(self._data == 1) > 0:
                filtered = filter(lambda x: hexChainDistance(x, reds) <= 1, moves)
            elif count_nonzero(self._data == 2) > 0:
                filtered = filter(lambda x: hexChainDistance(x, blues) <= 1, moves)
            else:
                if self.redLength == None:
                    self.updateEval()
                filtered = filter(lambda x: hexChainDistance(x, self.redPath) <= 1, moves)
            filtered = list(filtered)
            filtered.sort(key=lambda x: hexChainDistance(x, self.redPath))
        else:
            if count_nonzero(self._data == 1) > 0 and count_nonzero(self._data == 2) > 0:
                filtered = filter(lambda x: hexChainDistance(x, reds) <= 1 or hexChainDistance(x, blues) <= 1, moves)
            elif count_nonzero(self._data == 2) > 0:
                filtered = filter(lambda x: hexChainDistance(x, blues) <= 1, moves)
            elif count_nonzero(self._data == 1) > 0:
                filtered = filter(lambda x: hexChainDistance(x, reds) <= 1, moves)
            else:
                if self.blueLength == None:
                    self.updateEval()
                filtered = filter(lambda x: hexChainDistance(x, self.bluePath) <= 1, moves)
            filtered = list(filtered)
            filtered.sort(key=lambda x: hexChainDistance(x, self.bluePath))
        return list(filtered)

    def evaluate(self, token):
        if token == 'red':
            if self.redLength == 0:
                return self.n ** 3
            elif self.blueLength == 0:
                return -self.n ** 3
            else:
                return ((self.n - self.redLength) - (self.n - self.blueLength))  + count_nonzero(self._data == 1) - count_nonzero(self._data == 2) + self.diamond_eval()
        else :
            if self.redLength == 0:
                return -self.n ** 2
            elif self.blueLength == 0:
                return self.n ** 2
            else:
                return ((self.n - self.blueLength) - (self.n - self.redLength)) - count_nonzero(self._data == 1) + count_nonzero(self._data == 2) -  + self.diamond_eval()
    
    def updateEval(self):
        """
        Returns True if the game is over.
        """
        self.redPath, self.redLength = self.pathSearch('red')
        self.bluePath, self.blueLength = self.pathSearch('blue')

    def filled(self):
        """
        Returns the percentage of the board that is filled.
        """
        return count_nonzero(self._data)

    def isTerminal(self):
        if self.redLength == 0 or self.blueLength == 0:
            return True
        return False

    def diamond_eval(self):
        # cal for red
        opp_type = 'red'
        mid_type = 'blue'
        eval = 0
        
        for i in range(self.n):
            for j in range(self.n):
                if self[(i,j)] == opp_type:
                    eval += 1
                    for pattern in _CAPTURE_PATTERNS:
                        coords = [_ADD((i,j), s) for s in pattern]
                        if all(map(self.inside_bounds, coords)):
                            tokens = [self[coord] for coord in coords]
                            if tokens == [None, mid_type, mid_type]:
                                eval += 0.5
                            elif tokens == [opp_type, None, mid_type]:
                                eval -= 0.5
                            elif tokens == [opp_type, mid_type, None]:
                                eval -= 0.5
                elif self[(i,j)] == mid_type:
                    eval -= 1
                    for pattern in _CAPTURE_PATTERNS:
                        coords = [_ADD((i,j), s) for s in pattern]
                        if all(map(self.inside_bounds, coords)):
                            tokens = [self[coord] for coord in coords]
                            if tokens == [None, opp_type, opp_type]:
                                eval -= 0.5
                            elif tokens == [mid_type, None, opp_type]:
                                eval += 0.5
                            elif tokens == [mid_type, opp_type, None]:
                                eval += 0.5
        return eval

    

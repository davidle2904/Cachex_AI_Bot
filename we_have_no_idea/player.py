from numpy import zeros
from we_have_no_idea.board import Board
from we_have_no_idea.alphaBeta import get_best_move

DEPTH_ORIGINAL = {3:12, 4:4, 5:3, 6:2, 7:2, 8:2, 9:2, 10:1, 11:1, 12:1, 13:1, 14:1, 15:1}
START_PIECE = {3:(2,1), 4:(2,2), 5:(3,1), 6:(3,2), 7:(4,2), 8:(5,3), 9:(6,2), 10:(6,3), 11:(7,4), 12:(8,4), 13:(9,4), 14:(10,4), 15:(11,4)}
class Player:
    def __init__(self, player, n):
        """
        Called once at the beginning of a game to initialise this player.
        Set up an internal representation of the game state.

        The parameter player is the string "red" if your player will
        play as Red, or the string "blue" if your player will play
        as Blue.
        """
        # put your code here
        self.n = n
        self.player = player
        self.board = Board(zeros((n, n), dtype=int), n)
        self.firstMove = True
        self.redMove = None

    def action(self):
        """
        Called at the beginning of your turn. Based on the current state
        of the game, select an action to play.
        """
        # put your code here
        if self.firstMove and self.player == 'red':
            self.firstMove = False
            temp = START_PIECE[self.n]
            return ("PLACE", temp[0], temp[1])
        elif self.firstMove and self.player == 'blue' and self.takeMove():
            self.firstMove = False
            return ("STEAL", )
        else:
            if self.firstMove:
                self.firstMove = False
            if self.n > 10 and (self.board.filled() < 6 or self.board.filled() > (self.n**2 - 6)):
                depth = DEPTH_ORIGINAL[self.n] + 1
            elif self.n == 9 and (self.board.filled() > 9**2*0.3 and self.board.filled() < 9**2*0.7):
                depth = DEPTH_ORIGINAL[self.n] - 1
            else:
                depth = DEPTH_ORIGINAL[self.n]
            move = get_best_move(self.board, depth, self.player)
            return ("PLACE", move[0], move[1])
    
    def turn(self, player, action):
        """
        Called at the end of each player's turn to inform this player of 
        their chosen action. Update your internal representation of the 
        game state based on this. The parameter action is the chosen 
        action itself. 
        
        Note: At the end of your player's turn, the action parameter is
        the same as what your player returned from the action method
        above. However, the referee has validated it at this point.
        """
        # put your code here
        if self.player ==  'blue' and self.firstMove:
            self.redMove = (action[1], action[2])
        if action == ("STEAL", ):
            self.board.swap()
            self.board.updateEval()
        else:
            self.board.place(player, (action[1], action[2]))
            self.board.updateEval()

    def takeMove(self):
        if self.n == 3:
            if self.redMove not in [(1,0), (1,2)]:
                return True
            else:
                return False
        if self.redMove is not None:
            if self.redMove in [(0, self.n - 1), (self.n - 1, 0)]:
                return True
            elif self.redMove[0] in [0, self.n - 1] or self.redMove[1] in [0, self.n - 1]:
                return False
            else:
                return True
        else:
            return False

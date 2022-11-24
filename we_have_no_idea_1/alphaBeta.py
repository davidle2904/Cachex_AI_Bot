from we_have_no_idea_1.board import Board
from we_have_no_idea_1.utils import *
import numpy as np


def get_best_move(board, depth, token):
    best_move = None
    alpha = -10000
    beta = 10000
    for move in board.generateMove(token):
        temp_board = Board(np.array(board._data), board.n)
        temp_board.place(token, move)
        temp_board.updateEval()
        value = minValue(temp_board, depth - 1, alpha, beta, changeSide(token))
        if value > alpha:
            alpha = value
            best_move = move
    return best_move
    
def maxValue(board, depth, alpha, beta, token):
    if depth == 0 or board.isTerminal():
        return board.evaluate(token)
    for move in board.generateMove(token):
        temp_board = Board(np.array(board._data), board.n)
        temp_board.place(token, move)
        temp_board.updateEval()
        alpha = max(alpha, minValue(temp_board, depth - 1, alpha, beta, changeSide(token)))
        if alpha >= beta:
            return beta
    return alpha

def minValue(board, depth, alpha, beta, token):
    if depth == 0 or board.isTerminal():
        return board.evaluate(changeSide(token))
    for move in board.generateMove(token):
        temp_board = Board(np.array(board._data), board.n)
        temp_board.place(token, move)
        temp_board.updateEval()
        beta = min(beta, maxValue(temp_board, depth - 1, alpha, beta, changeSide(token)))
        if beta <= alpha:
            return alpha
    return beta
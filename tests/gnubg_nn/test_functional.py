# test_module.py
import unittest
import pytest
import faulthandler
import gnubg.nn as nn

faulthandler.enable()



def test_module():

    functions = [
        '__doc__',
        '__name__',
        '__package__',
        'bearoffid2pos',
        'bearoffprobs',
        'bestmove',
        'board',
        'boardfromkey',
        'c_bearoff',
        'c_contact',
        'c_crashed',
        'c_over',
        'c_race',
        #'classify',
        'crollout',
        'doubleroll',
        'equities',
        # 'id',
        'keyofboard',
        'moves',
        'net',
        'onecrace',
        'p_0plus1',
        'p_1sbear',
        'p_1srace',
        'p_bearoff',
        'p_osr',
        'p_prune',
        'p_race',
        'probs',
        #'pubbestmove',
        # 'pubevalscore',
        'ro_auto',
        'ro_bearoff',
        'ro_over',
        'ro_race',
        'roll',
        'rollout',
        'set',
        'trainer'
    ]


    print("=== exported names ===")
    print(dir(nn))
    print()

    # build a simple “race” board:
    board = [[0]*25, [0]*25]
    board[0][0] = 15   # X on the bar
    board[1][24] = 15  # O on the bar

    # load it through the module
    board = nn.board_from_position_id("4HPwATDgc/ABMA")
    print("BoardFromID:", board)
    print("Key of that board:", nn.position_id(board))
    d1, d2 = nn.roll()
    print(f"Rolled: {d1}, {d2}")
    print("Key-roundtrip -> board:", nn.board_from_position_key(nn.key_of_board(board)))
    print("Class:", nn.classify(board))
    print("PUB eval bestmove:", nn.pub_best_move(board, d1, d2))
    print("PUB eval score:", nn.pub_eval_score(board))

    print()
    print("=== full evaluator bestmove ===")
    best = nn.best_move(board, d1, d2)
    print("  simple:", best)
    best_all = nn.best_move(board, d1, d2, b=1, r=1, list=1)
    print("  with extras:", best_all)

    print()
    print("=== other core bindings ===")
    print("bearoffid2pos(1000)    ->", nn.bearoff_id_2_pos(1000))
    print("bearoffprobs(1000)[:5] ->", nn.bearoff_probabilities(1000)[:5])
    print("moves(board,2,3)       ->", nn.moves(board, 2, 3)[:3], "...")  # first 3 moves
    print("probs(board,0)         ->", nn.probabilities(board, 0))
    print("roll()                 ->", nn.roll())
    print("rollout(board,1)       ->", nn.rollout("4HPwATDgc/ABMA", 1))
    # print("crollout(board,1)      ->", gnubg.crollout("4HPwATDgc/ABMA"), "...")

    print()
    print("=== constants ===")
    for name in ("c_over","c_bearoff","c_race","c_crashed","c_contact"):
        print(f" {name} =", getattr(nn, name))
    for name in ("p_osr","p_bearoff","p_prune","p_race","p_1srace","p_0plus1"):
        print(f" {name} =", getattr(nn, name))
    for name in ("ro_auto","ro_over","ro_bearoff","ro_race"):
        print(f" {name} =", getattr(nn, name))

    print()
    print("=== equities submodule ===")
    print(" available tables:", dir(nn.equities))
    print(" equities.value(2,3) =", nn.equities.value(2,3))

    print()
    print("=== set submodule ===")
    # seed, shortcuts, osdb, ps, score, cube
    nn.set.seed(42)
    nn.set.shortcuts(1)
    nn.set.osdb(0)
    nn.set.ps(1, 4, 0, 0.1)
    nn.set.score(1, 2, 0)
    nn.set.cube(2, b'X')
    print(" set.* calls completed without error")

    print()
    print("=== trainer and onecrace ===")
    print(" onecrace(10)        ->", nn.one_checker_race(10))
    # t = nn.trainer({"pos": board, "n": 0})  # a Trainer object
    # print(" trainer object      ->", t)

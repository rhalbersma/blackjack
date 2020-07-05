#          Copyright Rein Halbersma 2020.
# Distributed under the Boost Software License, Version 1.0.
#    (See accompanying file LICENSE_1_0.txt or copy at
#          http://www.boost.org/LICENSE_1_0.txt)

from aenum import IntEnum, extend_enum
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np

class Hand(IntEnum):
    DEAL =  0
    H2   =  1
    H3   =  2
    H4   =  3
    H5   =  4
    H6   =  5
    H7   =  6
    H8   =  7
    H9   =  8
    H10  =  9
    H11  = 10
    H12  = 11
    H13  = 12
    H14  = 13
    H15  = 14
    H16  = 15
    H17  = 16
    H18  = 17
    H19  = 18
    H20  = 19
    H21  = 20
    T    = 21
    A    = 22
    S12  = 23
    S13  = 24
    S14  = 25
    S15  = 26
    S16  = 27
    S17  = 28
    S18  = 29
    S19  = 30
    S20  = 31
    S21  = 32
    BJ   = 33

hand_labels = [ h.name for h in Hand ]

class Count(IntEnum):
    _BUST =  0 # all counts above 21
    _16   =  1 # all counts below 17
    _17   =  2
    _18   =  3
    _19   =  4
    _20   =  5
    _21   =  6
    _BJ   =  7 # 21 with the first 2 cards

count_labels = [
    c.name[c.name.startswith('_'):]
    for c in Count
]

_offset = Hand.BJ + 1
for key, value in Count.__members__.items():
    extend_enum(Hand, key, value + _offset)

hand_labels += count_labels

class Card(IntEnum):
    _2 =  0
    _3 =  1
    _4 =  2
    _5 =  3
    _6 =  4
    _7 =  5
    _8 =  6
    _9 =  7
    _T =  8 # 10, J, Q, K are all denoted as T
    _A =  9

card_labels = [ c.name[1:] for c in Card ]

class Action(IntEnum):
    s = 0
    h = 1

action_labels = [ a.name[0] for a in Action ]

# Finite-state machine for going from one hand to the next after 'hitting' another card.
fsm_hit = np.zeros((len(Hand), len(Card)), dtype=int)

for _j, _c in enumerate(range(Card._2, Card._T)):
    fsm_hit[Hand.DEAL, _c] = Hand.H2 + _j
fsm_hit[Hand.DEAL, Card._T] = Hand.T
fsm_hit[Hand.DEAL, Card._A] = Hand.A

for _i, _h in enumerate(range(Hand.H2, Hand.H11)):
    for _j, _c in enumerate(range(Card._2, Card._A)):
        fsm_hit[_h, _c] = _h + 2 + _j
    fsm_hit[_h, Card._A] = Hand.S13 + _i

for _j, _c in enumerate(range(Card._2, Card._A)):
    fsm_hit[Hand.H11, _c] = Hand.H13 + _j
fsm_hit[Hand.H11, Card._A] = Hand.H12

for _i, _h in enumerate(range(Hand.H12, Hand.H21)):
    for _j, _c in enumerate(range(Card._2, Card._T - _i)):
        fsm_hit[_h, _c] = _h + 2 + _j
    fsm_hit[_h, (Card._T - _i):Card._A] = Hand._BUST
    fsm_hit[_h, Card._A] = _h + 1

fsm_hit[Hand.H21, :] = Hand._BUST

for _j, _c in enumerate(range(Card._2, Card._A)):
    fsm_hit[Hand.T, _c] = Hand.H12 + _j
fsm_hit[Hand.T, Card._A] = Hand.BJ

for _j, _c in enumerate(range(Card._2, Card._T)):
    fsm_hit[Hand.A, _c] = Hand.S13 + _j
fsm_hit[Hand.A, Card._T] = Hand.BJ
fsm_hit[Hand.A, Card._A] = Hand.S12

for _i, _s in enumerate(range(Hand.S12, Hand.S21)):
    for _j, _c in enumerate(range(Card._2, Card._T - _i)):
        fsm_hit[_s, _c] = _s + 2 + _j
    for _j, _c in enumerate(range(Card._T - _i, Card._A)):
        fsm_hit[_s, _c] = Hand.H12 + _j
    fsm_hit[_s, Card._A] = _s + 1

for _c, _j in enumerate(range(Card._2, Card._A)):
    fsm_hit[Hand.S21, _c] = Hand.H13 + _j
fsm_hit[Hand.S21, Card._A] = Hand.H12

fsm_hit[Hand.BJ, :] = fsm_hit[Hand.S21, :]

for _c in range(Hand._BUST, Hand._BJ + 1):
    fsm_hit[_c, :] = _c

# Finite-state machine for going from one hand to the next after 'standing'.
fsm_stand = np.zeros(len(Hand), dtype=int)
fsm_stand[Hand.DEAL:Hand.H17] = Hand._16
for _i, _h in enumerate(range(Hand.H17, Hand.H21 + 1)):
    fsm_stand[_h] = Hand._17 + _i
fsm_stand[Hand.T:Hand.S17] = Hand._16
for _i, _s in enumerate(range(Hand.S17, Hand.S21 + 1)):
    fsm_stand[_s] = Hand._17 + _i
fsm_stand[Hand.BJ] = Hand._BJ
for _c in range(Hand._BUST, Hand._BJ + 1):
    fsm_stand[_c: ] = _c

# Map a Hand to a Count
count = fsm_stand - _offset

# Policy for a dealer who stands on 17.
stand_on_17 = np.full(len(Hand), Action.h)

for _h in range(Hand.H17, Hand.H21 + 1):
    stand_on_17[_h] = Action.s

for _s in range(Hand.S17, Hand._BJ + 1):
    stand_on_17[_s] = Action.s

# Policy for a dealer who hits on soft 17.
hit_on_soft_17 = stand_on_17.copy()
hit_on_soft_17[Hand.S17] = Action.h

# The payout structure as specified in Sutton and Barto.
_sutton_barto = np.zeros((len(Count), len(Count)))      # The player and dealer have equal scores.
_sutton_barto[Count._BUST, :         ]           = -1.  # The player busts regardless of whether the dealer busts.
_sutton_barto[Count._16:, Count._BUST]           = +1.  # The dealer busts and the player doesn't.
_sutton_barto[np.tril_indices(len(Count), k=-1)] = +1.  # The player scores higher than the dealer.
_sutton_barto[np.triu_indices(len(Count), k=+1)] = -1.  # The dealer scores higher than the player.

# The payout structure as specified in the default Blackjack-v0 environment with natural=False.
# Note: in contrast to Sutton and Barto, blackjack is considered equivalent to 21.
_blackjack_v0 = _sutton_barto.copy()
_blackjack_v0[Count._BJ, Count._21]              =  0.  # A player's blackjack and a dealer's 21 are treated equally.
_blackjack_v0[Count._21, Count._BJ]              =  0.  # A player's 21 and a dealer's blackjack are treated equally.

# The payout structure as specified in the alternative Blackjack-v0 environment with natural=True.
# Note: in contrast to Sutton and Barto, blackjack is considered equivalent to 21.
_blackjack_v0_natural = _blackjack_v0.copy()
_blackjack_v0_natural[Count._BJ, :Count._21]     = +1.5 # A player's winning blackjack pays 1.5 times the original bet.

# The typical casino payout structure as specified in E.O. Thorp, "Beat the Dealer" (1966).
# https://www.amazon.com/gp/product/B004G5ZTZQ/
_thorp = _sutton_barto.copy()
_thorp[Count._BJ, :Count._BJ]                    = +1.5 # A player's winning blackjack pays 1.5 times the original bet.

class InfiniteDeck:
    """
    An infinite deck of cards (i.e. drawing from a single suit with replacement).
    """
    def __init__(self, np_random):
        self.cards = np.array([ c for c in range(Card._2, Card._T) ] + [ Card._T ] * 4 + [ Card._A ])
        self.np_random = np_random

    def draw(self):
        """
        Draw a single card.
        """
        return self.np_random.choice(self.cards, replace=True)

    def deal(self):
        """
        Draw two player cards and one dealer card.
        """
        return self.draw(), self.draw(), self.draw()

class BlackjackEnv(gym.Env):
    """
    Blackjack environment corresponding to Examples 5.1, 5.3 and 5.4 in
    Reinforcement Learning: An Introduction (2nd ed.) by Sutton and Barto.
    http://incompleteideas.net/book/the-book-2nd.html

    Description:
        The object of the popular casino card game of blackjack is to obtain cards,
        the sum of whose values is as great as possible without exceeding 21 ('bust').
        Face cards count as 10, and an ace can count as either 1 ('hard') or 11 ('soft').

    Observations:
        There are 34 * 10 = 340 discrete states:
            34 player counts (DEAL, H2-H21, T, A, S12-S21, BJ)
            10 dealer cards showing (2-9, T, A)

    Actions:
        There are 2 actions for the player:
            0: stop the game ('stand' or 'stick') and play out the dealer's hand.
            1: request an additional card to be dealt ('hit').
        Note: additional actions allowed in casino play, such as taking insurance,
        doubling down, splitting or surrendering, are not supported.

    Rewards:
        There are 3 rewards for the player:
            -1. : the player busted, regardless of the dealer,
                or the player's total is lower than the dealer's,
                or the dealer has a blackjack and the player doesn't.
             0. : the player's total is equal to the dealer's.
            +1. : the player's total is higher than the dealer's,
                or the dealer busted and the player didn't,
                or the player has a blackjack and the dealer doesn't
                (in casino play, this pays out +1.5 to the player).
    """

    metadata = {'render.modes': ['human']}

    def __init__(self, payout=None, dealer_hits_on_soft_17=False, deck=InfiniteDeck):
        """
        Initialize the state of the environment.

        Args:
            payout (None, str or an 8x8 NumPy matrix): the game's payout structure.
                If payout is None or 'sutton-barto', blackjack beats 21 and a player's winning blackjack pays out +1.0.
                If payout is 'blackjack-v0', same as above, but a blackjack ties with 21.
                If payout is 'blackjack-v0-natural', same as above, but a player's winning blackjack pays out +1.5.
                If payout is 'thorp', same as 'sutton-barto', but a player's winning blackjack pays out +1.5.
            dealer_hits_on_soft (bool): whether the dealer stands or hits on soft 17.
            debug (bool): whether the environment keeps track of the cards received by the player and the dealer.

        Notes:
            'suttton-barto' is described in Sutton and Barto's "Reinforcement Learning" (2018).
            'blackjack-v0' is implemented in the OpenAI Gym environment 'Blackjack-v0'.
            'blackjack-v0-natural' is obtained from 'Blackjack-v0' initialized with natural=True.
            'thorp' is described in E.O. Thorp's "Beat the Dealer" (1966).
        """
        if payout is None:
            self.payout = _sutton_barto
        elif isinstance(payout, np.ndarray) and payout.shape == (len(Count), len(Count)) and payout.dtype.name.startswith('float'):
            self.payout = payout
        elif isinstance(payout, str):
            try:
                self.payout = {
                    'sutton-barto'          : _sutton_barto,
                    'blackjack-v0'          : _blackjack_v0,
                    'blackjack-v0-natural'  : _blackjack_v0_natural,
                    'thorp'                 : _thorp
                }[payout.lower()]   # Handle mixed-case spelling.
            except KeyError:
                raise ValueError(f"Unknown payout name '{payout}'")
        else:
            raise ValueError(f"Unknown payout type '{type(payout)}'")
        self.dealer_policy = hit_on_soft_17 if dealer_hits_on_soft_17 else stand_on_17
        self.observation_space = spaces.Tuple((
            spaces.Discrete(len(Hand) - len(Count)),
            spaces.Discrete(len(Card))
        ))
        self.action_space = spaces.Discrete(len(Action))
        self.reward_range = (np.min(self.payout), np.max(self.payout))
        self.seed()
        self.deck = deck(self.np_random)
        self.reset()

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def render(self, mode='human'):
        p = hand_labels[self.player]
        upcard_only = self.dealer in range(Card._2, Card._A + 1)
        if self.player != Hand._BUST and upcard_only:
            d = card_labels[self.dealer]
            return f'player: {p:>4}; dealer: {d:>4};'
        else:
            d = hand_labels[fsm_hit[Hand.DEAL, self.dealer] if upcard_only else self.dealer]
            R = self.payout[count[self.player], count[self.dealer]]
            return f'player: {p:>4}; dealer: {d:>4}; reward: {R:>+4}'

    def _get_obs(self):
        return self.player, self.dealer

    def reset(self):
        """
        Reset the state of the environment by drawing two player cards and one dealer card.

        Returns:
            observation (object): the player's hand and the dealer's upcard.

        Notes:
            Cards are drawn from a single deck with replacement (i.e. from an infinite deck).
        """
        p1, p2, up = self.deck.deal()
        self.info = { 'player': [ card_labels[p1], card_labels[p2] ], 'dealer': [ card_labels[up] ] }
        self.player, self.dealer = fsm_hit[fsm_hit[Hand.DEAL, p1], p2], up
        return self._get_obs()

    def explore(self, start):
        """
        Explore a specific starting state of the environment.

        Args:
            start (tuple of ints): the player's count and the dealer's upcard.

        Returns:
            observation (object): the player's count and the dealer's upcard.

        Notes:
            Monte Carlo Exploring Starts should use this method instead of reset().
        """
        self.player, self.dealer = start
        self.info = { 'player': [], 'dealer': [] }
        return self._get_obs()

    def step(self, action):
        if action:
            next = self.deck.draw()
            self.info['player'].append(card_labels[next])
            self.player = fsm_hit[self.player, next]
            done = self.player == Hand._BUST
        else:
            self.dealer = fsm_hit[Hand.DEAL, self.dealer]
            while True:
                next = self.deck.draw()
                self.info['dealer'].append(card_labels[next])
                self.dealer = fsm_hit[self.dealer, next]
                if not self.dealer_policy[self.dealer]:
                    break
            done = True
        reward = self.payout[count[self.player], count[self.dealer]] if done else 0.
        return self._get_obs(), reward, done, self.info

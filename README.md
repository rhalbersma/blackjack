# OpenAI Gym blackjack environment (v1)

[![Language](https://img.shields.io/badge/language-Python-blue.svg)](https://www.python.org/)
[![Standard](https://img.shields.io/badge/Python-3.6-blue.svg)](https://en.wikipedia.org/wiki/History_of_Python)
[![License](https://img.shields.io/badge/license-Boost-blue.svg)](https://opensource.org/licenses/BSL-1.0)
[![Lines of Code](https://tokei.rs/b1/github/rhalbersma/blackjack?category=code)](https://github.com/rhalbersma/blackjack)

## Requirements

- Python version 3.6 or higher

## Installation

```bash
git clone https://github.com/rhalbersma/blackjack.git
cd blackjack
python3 -m venv .env
source .env/bin/activate
pip install -e .
```

## Hello World

Let's simulate one millions blackjack hands using Sutton and Barto's blackjack rules and Thorp's basic strategy:

```python
import gym
import blackjack as bj
env = gym.make('Blackjack-v1')
agent = bj.BasicStrategyAgent(env)
stats = bj.simulate(agent, env, episodes=10**6)
dict(zip(stats.data, stats.weights)), stats.mean, stats.tconfint_mean(.05)
```

The above code will output the distribution of outcomes (win, loss, tie), the mean score per hand and its 95% confidence interval:

<pre>
>>> import gym
>>> import blackjack as bj
>>> env = gym.make('Blackjack-v1')
>>> agent = bj.BasicStrategyAgent(env)
>>> stats = bj.simulate(agent, env, episodes=10**6)
100%|██████████████████████████████| 1000000/1000000 [00:28<00:00, 35182.52it/s]
>>> dict(zip(stats.data, stats.weights)), stats.mean, stats.tconfint_mean(.05)
({-1.0: 480046.0, 1.0: 432712.0, 0.0: 87242.0}, -0.047334, (-0.049204221221545476, -0.045463778778454526))
</pre>

A player using the basic strategy will approximately lose 48.0%, win 43.3% and tie 8.7% of all hands, for a mean score per hand of -4.73%, give or take 0.19%.

## Acknowledgement

Special thanks to [Craig Lee Zirbel](https://sites.google.com/view/clzirbel/home) for his illumunating [blackjack paper](https://www.google.com/url?q=https%3A%2F%2Fwww.dropbox.com%2Fs%2Fxrntclqyx36jhis%2FBlackjack_talk_2001.pdf%3Fdl%3D0&sa=D&sntz=1&usg=AFQjCNE-4z5OXoUaqlLra9HD8rfaN-kVkQ).

## License

Copyright Rein Halbersma 2020.
Distributed under the [Boost Software License, Version 1.0](http://www.boost.org/users/license.html).
(See accompanying file LICENSE_1_0.txt or copy at [http://www.boost.org/LICENSE_1_0.txt](http://www.boost.org/LICENSE_1_0.txt))

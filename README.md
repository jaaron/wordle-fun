# Wordle Investigation

This repository is an investigation of the trending word puzzle game
wordle (https://www.powerlanguage.co.uk/wordle/).

This project is completely unaffiliated with the actual wordle game
and does not interact with the wordle server in anyway. It is just
intended as an investigation of the statistics and strategies for
successful play. It makes many assumptions, is only minimally tested,
and is completely unoptimized.

The file `wordle.py` implements the mechanics of the wordle puzzle
game and can be run from the commandline in either fully automatic
mode or with interactive assessment.

The file `Wordle Investigation.ipynb` is a Jupyter notebook that
generates histograms for a number of different guessing
strategies/parameters.

## Usage:
```
$ python wordle.py --help
usage: wordle.py [-h] [--repeat REPEAT] [--words WORDS]
       		 [--pop-size POP_SIZE] [--guess GUESS]
		 [--random-choice] [--prompt-assess]
		 [--secret SECRET] [--quiet]

optional arguments:
  -h, --help           show this help message and exit
  --repeat REPEAT
  --words WORDS
  --pop-size POP_SIZE
  --guess GUESS
  --random-choice
  --prompt-assess
  --secret SECRET
  --quiet
```

## Arguments:
* `--repeat` run a given number of trials
* `--words` read the word list from the given file (defaults to
  `sgb-words.txt`)
* `--pop-size` defines sample population size for strategic guessing
* `--guess` define an initial guess, may be specified multiple times
  to specify guesses in sequence
* `--random-choice` choose guesses randomly from valid words
* `--prompt-assess` instead of generating a random secret word, prompt
  the user for assessment of each guess (useful for playing the real
  wordle game)
* `--secret` specify a secret word
* `--quiet` only output the number of turns for each trial to stdout

## Guessing Algorithms

`wordle.py` can either randomly guess valid words at each step, or the
`smart_choice()` routine that attempts to maximize the expected
information gain from the guess.

In either case, the guessing algorihm will only guess a word that is
consistent with knowledge gained from all previous guesses. For
example, if an initial guess of "STARE" is assessed as "YGBBB" all
subsequent guesses will contain an "S" at a position other than 0, a
"T" at position 1, and not contain any "A"s, "R"s, or "E"s. This
greatly reduces the search space for the `smart_choice()` algorithm,
and is an attractive strategy (although not necessarily optimal).

`smart_choice` works by drawing a sample population (defined by the
`pop-size` argument) from the set of remaining valid words, then for
each word in the population it computes the average number of valid
remaining words for all possible secrets.

## Word List

By default `wordle.py` uses the included copy of Donald Knuth's
5-letter word list `sgb-words.txt`
(https://www-cs-faculty.stanford.edu/~knuth/sgb-words.txt). This file
is part of the Stanford Graphics Base and is published in the public
domain.

Any word list can be used, words should be provided one-per-line with
no additional punctuation.

## Generalization

In theory, the code is written to support the wordle mechanics for
words of any fixed length. In practice it's only been tested on words
of length 5.
#!/usr/bin/env python

# Copyright 2022 J. Aaron Pendergrass 

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:

# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import random
import argparse
from time import perf_counter

"""Global quiet flag controling output"""
quiet = False

def charidx(c):
    """Return the array index of the given letter.  

    Assumes 'A' <= c <= 'Z'

    """
    return ord(c) - ord('A')

def calc_letter_freqs(words):
    """Calculate how many words contain each letter.

    Returns a list of (letter * count) in descending order.

    """
    cnts = [0]*26
    for w in words:
        for i in range(len(w)):
            if w[i] in w[0:i]:
                continue
            cnts[charidx(i)] += 1
            pass
        pass
    cnts = [('A' + chr(i),cnts[i]) for i in range(len(cnts))]
    return sorted(cnts, lambda x: x[1])

class MaskCell:
    """Knowledge state for a specific letter. 

    Tracks which positions in the secret may contain this letter, and
    its minimum and maximum number of occurences.

    """
    
    def __init__(self, n):
        self.n       = n
        self.allowed = [True]*n
        self.min     = 0
        self.max     = n
        pass

    def reset_bounds(self):
        self.min = 0
        self.max = self.n
        pass
    
    def valid_at(self, pos, count):
        return self.max > count and self.allowed[pos]

    def clone(self):
        other         = MaskCell(self.n)
        other.allowed = [x for x in self.allowed]
        other.min     = self.min
        other.max     = self.max
        return other
    pass

class Mask:
    """Complete knowledge state. 

    Tracks a `MaskCell` for each letter of the alphabet
    (`self.cells`), as well as a list of positions with known letters
    (`self.reqd`).

    """

    def __init__(self, n):
        self.n     = n
        self.cells = [MaskCell(n) for _ in range(26)]
        self.reqd  = [None]*n
        pass

    def clone(self):
        other = Mask(self.n)
        other.cells = [c.clone() for c in self.cells]
        other.reqd  = [x for x in self.reqd]
        return other
    
    def valid_at(self, w, pos, counts):
        c    = w[pos]
        idx  = charidx(c)
        if self.reqd[pos] and not c == self.reqd[pos]:
            return False
        if self.cells[idx].valid_at(pos, counts[idx]):
            counts[idx]+= 1
            return True
        return False

    def valid(self, w):        
        counts = [0]*26
        return (len(w) == self.n and
                all(self.valid_at(w, i, counts) for i in range(self.n)) and
                all(counts[i] >= self.cells[i].min for i in range(26)))

    def update(self, w, a):
        assert(len(w) == self.n)
        assert(len(a) == self.n)

        for cell in self.cells:
            cell.reset_bounds()
            
        for i in range(self.n):
            cell = self.cells[charidx(w[i])]
            if a[i] == 'G':
                self.reqd[i] = w[i]
                cell.min += 1
            elif a[i] == 'Y':
                cell.min += 1
                cell.allowed[i] = False
            else:
                cell.max = cell.min
                pass
            if cell.min > cell.max:
                cell.max = cell.min
                pass
            pass
        pass
    pass

def filter(words, mask):
    """Return list of elements from the `words` list that satisfy `mask`"""
    return [w for w in words if mask.valid(w)]

def prompt_assessment(word):
    """Prompt the use for assessment of the given word."""
    print("   < ", end="")
    return input().strip().upper()

def assess(secret, guess, print_assess = True):
    """Assess the given `guess` against the `secret.

    Returns a five character string of "G"|"Y"|"B" (green, yellow, or
    black) indicating whether each character is exactly right (G),
    present in the string at a different location (Y), or not present
    (B).

    If `print_assess` is true and `quiet` is false, prints the
    assessment to stdout.

    """
    
    assert(len(secret) == len(guess))
    counts = [0]*26
    for c in secret:
        counts[charidx(c)] += 1
        
    res = ["B"]*len(secret)
    for i in range(len(secret)):
        if secret[i] == guess[i]:
            res[i] = "G"
            counts[charidx(secret[i])] -= 1
            pass
        pass
    for i in range(len(guess)):
        if res[i] == "G":
            continue
        if counts[charidx(guess[i])] > 0:
            res[i] = "Y"
            counts[charidx(guess[i])] -= 1
            pass
        pass
    res = ''.join(res)
    if(print_assess and not quiet):
        print("   < %s" % (res))
    return res

def smart_choice(mask, words, pop_size = 65535):
    """Smart choice guessing algorithm.

    Given a knowledge state and a word list, generate a new guess by
    attempting to maximize the information gain. Selects a random
    population from the word list then for each word in the sample,
    computes the average the number of remaining valid words for all
    possible secret words, and returns the guess with the smallest
    value.

    """

    best = None
    if len(words) > pop_size:
        population = random.choices(words, k=pop_size)
    else:
        population = words
        pass
    for choice in population:
        total = 0
        for possible_secret in population:
            m = mask.clone()
            a = assess(possible_secret, choice, print_assess = False)
            m.update(choice, a)
            ws = filter(population, m)
            total += len(ws)            
            pass
        avg = total / len(population)
        if avg > 0 and not best or best[0] > avg:
            best = (avg, choice)
            pass
        pass
    if not quiet:
        print("Choosing %s average score: %f" % (best[1], best[0]))
        pass
    return best[1]    

def play(words, secret, get_choice):
    """Play wordle with the given wordlist, secret, and choice algorithm. 

    If `secret == None`, prompts the user for assessment of each guess.
    
    `get_choice` must be a function that given a `Mask` and a list of
    valid words, returns a word to guess (e.g., `smart_choice` above).

    """
    assert(len(words) > 0)
    wordlen = len(words[0])
    mask  = Mask(wordlen)
    a     = ""
    turn = 0
    while a != "G"*wordlen:        
        w = get_choice(mask, words)
        if not quiet:
            print("%03d> %s" % (turn, w))
            pass

        if secret:
            a = assess(secret, w)
        else:
            a = prompt_assessment(w)
            pass

        if a != "G"*wordlen:
            mask.update(w, a)
            words = filter(words, mask)
            if not quiet:
                print("\t%d words remain" % (len(words)))
            pass
        turn += 1
        pass
    if not quiet:
        print("Success in %d guesses" % (turn))
        pass
    return turn

def load_dictionary(fname):
    """Read a list of words from the given file."""
    with open(fname) as f:
        words = [l.strip().upper() for l in f]
        pass
    return words

def main():
    """Main routine to parse arguments and play wordle."""
    global quiet
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeat", default=1, type=int, metavar="N",
                    help=("Run N independent trials with the same parameters. "
                          "(default = 1)"))
    ap.add_argument("--words", default="sgb-words.txt", metavare="words.txt"
                    help=("Load word list from the given file. "
                          "(default = sgb-words.txt)"))
    ap.add_argument("--pop-size", metavar="P", type=int, default=20,
                    help=("For smart_choice, select P remaining words as the "
                          "population to evaluate/draw guesses from"))
    ap.add_argument("--guess", metavar="WORD", default=[], action="append",
                    help=("Specify initial guess(es). May be used multiple "
                          "times to specify guesses in the order provided."))
    ap.add_argument("--random-choice", action="store_true",
                    help="Use random choice guess strategy instead of smart_choice")
    ap.add_argument("--prompt-assess", action="store_true",
                    help="Prompt interactively for assessment of each guess")
    ap.add_argument("--secret", metavar="SECRET", help="Specify the secret word")
    ap.add_argument("--quiet", action="store_true",
                    help="Only output the number of turns for each trial")
    args = ap.parse_args()
    quiet = args.quiet
    
    words = load_dictionary(args.words)
    guesses = args.guess
    def chooser(mask,words):
        if guesses:
            return guesses.pop(0)
        if args.random_choice:
            return random.choice(words)
        return smart_choice(mask, words, args.pop_size)

    for i in range(args.repeat):
        start = perf_counter()
        if args.secret:
            secret = args.secret.upper()
        elif not args.prompt_assess:
            secret = random.choice(words)
        else:
            secret = None
            pass
        turns = play(words, secret, chooser)
        if quiet:
            print("%d" % (turns))
            pass

        end = perf_counter()
        if args.quiet:
            if i > 0 and i % 20 == 0:
                print("Trial: %d" % (i), file=sys.stderr)
                pass
        else:
            print("Trial: %d (%0.4f)" % (i, end - start))
    pass

if __name__ == "__main__":
    main()
    pass

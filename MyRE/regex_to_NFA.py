from subprocess import getoutput
import os
import sys
import re
import json
import graphviz
from collections import defaultdict


def ValidateRegex(RegexInput):
    try:
        re.compile(RegexInput)
        return True
    except re.error:
        return False


def ExtractAtomicExpressions(regex):
    stack = list()
    atomic = str()
    atomics = list()
    lasts = list()

    for c in regex:
        if c != ")":
            stack.append(c)
        else:
            # Extract the atomic expression that corresponds to the closing paranthesis found
            while stack[-1] != "(" and len(stack) > 0:
                atomic = stack[-1] + atomic
                stack.pop(-1)
            stack.pop(-1)  # remove the opening bracket from the stack
            if atomic[0] == ".":
                lasts.append(atomic[1:])
            else: 
                atomics.append(atomic)
            
            atomic = ""

    print("Atomics: ", atomics)
    print("Lasts: ", lasts)
    return atomics , lasts


class State:
    stateID = None
    edges = []
    transitions = []

    def __init__(self, stateID=None, edges=None, transitions=None):
        self.stateID = stateID
        self.edges = edges or []

    def __str__(self):
        return f"state_id:{self.stateID}\n edges:{self.edges}\n"

    def __repr__(self):
        return self.__str__()


class NFA:
    initial = None
    accept = None

    def __init__(self, initial, accept):
        self.initial = initial
        self.accept = accept or []

    def __str__(self):
        return f"intial:{self.initial}  final:{self.accept}"

    def __repr__(self):
        return self.__str__()


def InsertConcatenationDot(regex):
    regex = re.sub(r'(\w|\))(\(|\w)', r'\1.\2', regex)
    regex = re.sub(r'\)(\()', r').\1', regex)
    return regex


def MoveSymbolToEndOfAtomicExpression(expression):
    for i in range(len(expression)):
        if expression[i] == "|":
            return expression[0:i] + expression[i+1:] + "|"
        if expression[i] == ".":
            return expression[0:i] + expression[i+1:] + "."
    return expression


def RegexToNFA(regex):
    if ValidateRegex(regex):
        regex = InsertConcatenationDot(regex)
        regex = regex.replace(" ", "")
        atomics , lasts = ExtractAtomicExpressions(regex)
        states = list()
        for i in range(len(atomics)):
            atomics[i] = MoveSymbolToEndOfAtomicExpression(atomics[i])
        counter = -1
        stack = []
        for atomic in atomics:
            match = re.search(r'\[.*?\]', atomic)
            if match:
                character_class = match.group()
                counter = counter+1
                initial = State()
                initial.stateID = counter
                accept = State()
                accept.stateID = counter+1
                initial.edges.append((character_class, accept))
                accept.edges = []
                stack.append(NFA(initial, [accept]))
                counter = counter+1
                continue

            print("Atomic Expression: ", atomic)
            for i in range(len(atomic)):

                if atomic[i] == '.':
                    NFA1 = stack.pop()
                    NFA2 = stack.pop()
                    NFA1.accept[0].edges.append(("epsilon", NFA2.initial))
                    NFA1.accept = NFA2.accept
                    stack.append(NFA1)

                elif atomic[i] == '|':
                    NFA2 = stack.pop()
                    NFA1 = stack.pop()
                    counter = counter+1
                    initial = State()
                    initial.stateID = counter
                    accept = State()
                    counter = counter+1
                    accept.stateID = counter
                    initial.edges.append(("epsilon", NFA1.initial))
                    initial.edges.append(("epsilon", NFA2.initial))
                    NFA1.accept[0].edges.append(("epsilon", accept))
                    NFA2.accept[0].edges.append(("epsilon", accept))
                    stack.append(NFA(initial, [accept]))

                elif atomic[i] == '*':
                    counter = counter+1
                    NFA0 = stack.pop()
                    initial = State()
                    initial.stateID = counter
                    accept = State()
                    counter = counter+1
                    accept.stateID = counter
                    initial.edges.append(("epsilon", NFA0.initial))
                    initial.edges.append(("epsilon", accept))
                    NFA0.accept[0].edges.append(("epsilon", initial))
                    NFA0.accept[0].edges.append(("epsilon", accept))
                    stack.append(NFA(initial, [accept]))

                elif atomic[i] == '?':
                    counter = counter+1
                    NFA0 = stack.pop()
                    NFA0.initial.edges.append(("epsilon", NFA0.accept[0]))
                    stack.append(NFA0)

                elif atomic[i] == '+':
                    counter = counter+1
                    NFA0 = stack.pop()
                    initial = State()
                    initial.stateID = counter
                    accept = State()
                    counter = counter+1
                    accept.stateID = counter
                    initial.edges.append(("epsilon", NFA0.initial))
                    NFA0.accept[0].edges.append(("epsilon", accept))
                    NFA0.accept[0].edges.append(("epsilon", NFA0.initial))
                    stack.append(NFA(initial, [accept]))

                else:
                    counter = counter+1
                    initial = State()
                    initial.stateID = counter
                    accept = State()
                    accept.stateID = counter+1
                    initial.edges.append((atomic[i], accept))
                    stack.append(NFA(initial, [accept]))
                    counter = counter+1

        #make the elements of lasts the final states
        for last in lasts:
            counter = counter+1
            NFA0 = stack.pop()
            initial = State()
            initial.stateID = counter
            accept = State()
            counter = counter+1
            accept.stateID = counter
            initial.edges.append((last, accept))
            NFA1 = NFA(initial, [accept])
            NFA0.accept[0].edges.append(("epsilon", NFA1.initial))
            NFA0.accept = NFA1.accept
            stack.append(NFA0)
        



        if len(stack) >= 1:
            return stack.pop()
    else:
        print("Invalid Regex")
        sys.exit(1)


def WriteJsonFile(NFA, filename):
    data = dict()
    visited = set()
    data["StartingState"] = "S"+str(NFA.initial.stateID)
    queue = [NFA.initial]
    while queue:
        state = queue.pop(0)
        if state in visited:
            continue
        visited.add(state)

        if state in NFA.accept:

            if data.get("S"+str(state.stateID)) is not None:
                pass
            else:
                data["S"+str(state.stateID)] = dict()
                data["S"+str(state.stateID)]["IsTerminating"] = True
            for char, dest_state in state.edges:
                if data.get("S"+str(state.stateID), {}).get(str(char)) is not None:

                    data["S"+str(state.stateID)][str(char)
                                                 ].append("S"+str(dest_state.stateID))

                else:
                    data["S"+str(state.stateID)][str(char)] = list()
                    data["S"+str(state.stateID)][str(char)
                                                 ].append("S"+str(dest_state.stateID))

                queue.append(dest_state)

        for char, dest_state in state.edges:

            if data.get("S"+str(state.stateID)) is not None:
                pass
            else:
                data["S"+str(state.stateID)] = dict()
                data["S"+str(state.stateID)]["IsTerminating"] = False

            if data.get("S"+str(state.stateID)) is not None:
                if data.get("S"+str(state.stateID), {}).get(str(char)) is not None:
                    data["S"+str(state.stateID)][str(char)
                                                 ].append("S"+str(dest_state.stateID))

                else:
                    data["S"+str(state.stateID)][str(char)] = list()
                    data["S"+str(state.stateID)][str(char)
                                                 ].append("S"+str(dest_state.stateID))

            queue.append(dest_state)

    f = open(filename, 'w')
    json.dump(data, f)
    f.close()
    return data

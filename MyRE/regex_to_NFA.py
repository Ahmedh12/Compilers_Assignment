from subprocess import getoutput
import os
import re 
import json
import graphviz
from collections import defaultdict


def ValidateRegex (RegexInput):
  try:
    re.compile(RegexInput)
    return True

  except re.error:
    print("Non valid regex pattern")
    exit()


def ExtractAtomicExpressions(regex):
    stack = list() 
    atomic = str()
    atomics = list()
    for c in regex:
        if c != ")":
            stack.append(c)
        else:
            while stack[-1] != "(" and len(stack) > 0 : #Extract the atomic expression that corresponds to the closing paranthesis found
                atomic = stack[-1] + atomic
                stack.pop(-1)
            
            stack.pop(-1) #remove the opening bracket from the stack
            atomics.append(atomic)
            atomic = ""
    #atomics.reverse()
    return atomics


class State:
    stateID=None
    edges=[]
    transitions=[]    
    def __init__(self, stateID=None, edges=None,transitions=None):
        self.stateID = stateID
        self.edges = edges or []


class NFA:
    initial = None
    accept = None

    def __init__(self, initial, accept):
        self.initial = initial
        self.accept = accept or []


def InsertConcatenationDot(regex):
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
        regex = re.sub(r"\.", "dot", regex)
        regex = InsertConcatenationDot(regex)
        regex = regex.replace(" ", "")
        atomics = ExtractAtomicExpressions(regex)
        states = list()
        for i in range(len(atomics)):
            atomics[i] = MoveSymbolToEndOfAtomicExpression(atomics[i])
        counter = -1
        stack = []
        for atomic in atomics:
                pattern = r'^[a-zA-Z0-9]+$'
                if re.match(pattern, atomic):
                        atomic = re.sub(r"dot", ".", atomic)
                        counter=counter+1
                        initial = State()
                        initial.stateID=counter
                        accept = State()
                        accept.stateID=counter+1
                        initial.edges.append((atomic, accept))
                        stack.append(NFA(initial, [accept]))
                        counter=counter+1
                        continue
                match = re.search(r'\[.*?\]', atomic)
                if match:
                    
                    character_class = match.group()
                    character_class = re.sub(r"\.", "", character_class)
                    counter=counter+1
                    initial = State()
                    initial.stateID=counter
                    accept = State()
                    accept.stateID=counter+1
                    initial.edges.append((character_class, accept))
                    accept.edges=[]
                    stack.append(NFA(initial, [accept]))
                    counter=counter+1
                    continue
                
            #else:                
                for i in range(len(atomic)):
                    if atomic[i] == '.':
                        if len(stack) >1:

                            NFA2 = stack.pop()
                            NFA1 = stack.pop()
                            NFA1.accept[0].edges.append(("epsilon", NFA2.initial))
                            NFA1.accept = NFA2.accept
                            stack.append(NFA1)
                    elif atomic[i] == '|':
                        NFA2 = stack.pop()
                        NFA1 = stack.pop()
                        counter=counter+1
                        initial = State()
                        initial.stateID=counter
                        accept=State()
                        counter=counter+1
                        accept.stateID=counter
                        initial.edges.append(("epsilon", NFA1.initial))
                        initial.edges.append(("epsilon", NFA2.initial))
                        #accept = NFA1.accept + NFA2.accept
                        NFA1.accept[0].edges.append(("epsilon",accept))
                        NFA2.accept[0].edges.append(("epsilon",accept))
                        stack.append(NFA(initial, [accept]))
                    elif atomic[i] == '*':
                        counter=counter+1
                        NFA0 = stack.pop()
                        initial = State()
                        initial.stateID=counter
                        accept = State()
                        counter=counter+1
                        accept.stateID=counter
                        initial.edges.append(("epsilon", NFA0.initial))
                        initial.edges.append(("epsilon", accept))
                        NFA0.accept[0].edges.append(("epsilon", initial))
                        NFA0.accept[0].edges.append(("epsilon", accept))
                        stack.append(NFA(initial, [accept]))

                    
                    elif atomic[i] == '?':
                        counter=counter+1
                        NFA0 = stack.pop()
                        NFA0.initial.edges.append(("epsilon", NFA0.accept[0]))
                        stack.append(NFA0)

                    elif atomic[i] == '+':
                        counter=counter+1
                        NFA0 = stack.pop()
                        initial = State()
                        initial.stateID=counter
                        accept = State()
                        counter=counter+1
                        accept.stateID=counter
                        initial.edges.append(("epsilon", NFA0.initial))
                        NFA0.accept[0].edges.append(("epsilon", accept))
                        NFA0.accept[0].edges.append(("epsilon", NFA0.initial))
                        stack.append(NFA(initial, [accept]))

                
                    else:
                        counter=counter+1
                        initial = State()
                        initial.stateID=counter
                        accept = State()
                        accept.stateID=counter+1
                        initial.edges.append((atomic[i], accept))
                        stack.append(NFA(initial, [accept]))
                        counter=counter+1
    if len(stack) >= 1:
        return stack.pop()


def WriteJsonFile(NFA , filename):
 
    data = dict()
    visited = set()
    data["StartingState"]="S"+str(NFA.initial.stateID)
    queue = [NFA.initial]
    while queue:
        state = queue.pop(0)
        if state in visited:
            continue
        visited.add(state)
        
        if state in NFA.accept:
                    
                    if data.get("S"+str(state.stateID)) is not None:
                        print("")
                    else:
                       data["S"+str(state.stateID)]=  dict()
                       data["S"+str(state.stateID)]["IsTerminating"] = True
                    for char, dest_state in state.edges:
                        if data.get("S"+str(state.stateID),{}).get(str(char)) is not None:
                            
                            data["S"+str(state.stateID)][str(char)].append("S"+str(dest_state.stateID))
                            
                        else:
                            data["S"+str(state.stateID)][str(char)]=list()
                            data["S"+str(state.stateID)][str(char)].append("S"+str(dest_state.stateID))

  
                        queue.append(dest_state)

                            
        for char, dest_state in state.edges:

            if data.get("S"+str(state.stateID)) is not None:
                print("")
            else:
                       data["S"+str(state.stateID)]= dict()
                       data["S"+str(state.stateID)]["IsTerminating"] = False
                       
            if data.get("S"+str(state.stateID))  is not None:
                if data.get("S"+str(state.stateID),{}).get(str(char))is not None:
                    data["S"+str(state.stateID)][str(char)].append("S"+str(dest_state.stateID))
                            
                else:
                    data["S"+str(state.stateID)][str(char)]=list()
                    data["S"+str(state.stateID)][str(char)].append("S"+str(dest_state.stateID))

            queue.append(dest_state)

    f = open(filename,'w')
    json.dump(data,f)
    f.close()
    return data

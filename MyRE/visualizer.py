# draw graphs of automata from json files using graphviz
import json
import graphviz

def draw_DFA(DFA,file_name="DFA"):
    G = graphviz.Digraph()
    nodes = list(DFA.keys())[1:]
    for node in nodes:
        G.node(DFA.get("StartingState"),color='green')
        if DFA.get(node).get('IsTerminating'):
            G.node(node, shape='doublecircle' , color='red')
        else:
            G.node(node)
    for state in DFA:
        if state != "StartingState":
            for transition in DFA.get(state):
                if transition != 'states' and transition != 'IsTerminating':
                    G.edge(state, DFA.get(state).get(transition), label=transition)
    
    G.render(file_name , format='png' ,cleanup=True , quiet=True)
    return G


def draw_NFA(NFA , filename="NFA"):
    G = graphviz.Digraph()
    nodes = list(NFA.keys())[1:]
    for node in nodes:
        G.node(NFA.get("StartingState"),color='green')
        if NFA.get(node).get('IsTerminating') == 'true':
            G.node(node, shape='doublecircle' , color='red')
        else:
            G.node(node)
    for state in NFA:
        if state != "StartingState":
            for transition in NFA.get(state):
                if transition != 'states' and transition != 'IsTerminating':
                    for next_state in [NFA.get(state).get(transition)]:
                        for next_states in next_state:
                            if transition == "epsilon":
                                G.edge(state, next_states, label='epsilon')
                            else:
                                G.edge(state, next_states, label=transition)
                                print("next state",next_states)
                                print("state",state)
    G.render(filename , format='png' ,cleanup=True , quiet=True)
    return G


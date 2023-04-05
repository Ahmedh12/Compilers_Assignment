import json

def epsilon_closure_state_rec(NFA,state,visited):
    reachable = [state]
    visited.append(state)
    for transition in NFA.get(state):
        if transition == 'epsilon':
            reachable.extend((NFA.get(state).get(transition)))
            for state in reachable:
                if state not in visited:
                    visited.append(state)
                    reachable.extend(epsilon_closure_state_rec(NFA,state,visited))
    return list(set(reachable))


def epsilon_closure_state(NFA,state):
    visited = []
    return epsilon_closure_state_rec(NFA,state,visited)

def epsilon_closure_states(NFA,states):
    reachable = []
    visited = []
    for state in states:
        reachable.extend(epsilon_closure_state(NFA,state))
    return list(set(reachable))

def move(NFA,states,symbol):
    reachable = []
    for state in states:
        if symbol in NFA.get(state):
            reachable.extend(NFA.get(state).get(symbol))
    return list(set(reachable))

def DFA_state(states , IsTerminating):
    return {'states':states , 'IsTerminating':IsTerminating , 'marked' : False}

def Extract_NFA_transitions(NFA):
    transitions = []
    for state in NFA:
        if state != "StartingState":
            for transition in NFA.get(state):
                if transition != 'epsilon' and transition != 'IsTerminating' and transition not in transitions:
                    transitions.append(transition)
    return transitions

def unique_state_set(DFA , U):
    for state in DFA.keys():
        if state != "StartingState" and DFA.get(state).get("states") == U:
            return state
    return None

def get_NFA_Terminating_states(NFA):
    terminating_states = set()
    for state in NFA:
        if state != "StartingState" and NFA.get(state).get("IsTerminating") == True:
            terminating_states.add(state)
    return terminating_states

def get_first_unmarked_state(DFA):
    for state in DFA:
        if state != "StartingState" and DFA.get(state).get("marked") == False:
            return state
    return None


def NFA_to_DFA(NFA):
    last_DFA_State_symbol = 65
    terminating_states = get_NFA_Terminating_states(NFA)
    DFA = dict()
    DFA["StartingState"] = chr(last_DFA_State_symbol)
    
    U = epsilon_closure_state(NFA, NFA.get("StartingState"))
    if len(list(set(U).intersection(terminating_states))) > 0:
        DFA.update({chr(last_DFA_State_symbol): DFA_state(U,True)})
    else:
        DFA.update({chr(last_DFA_State_symbol): DFA_state(U,False)})
    
    transitions = Extract_NFA_transitions(NFA)
    states = [chr(last_DFA_State_symbol)]
    while False in [DFA.get(state).get("marked") for state in states]:
        for transition in transitions: #for each transition in NFA
            state = get_first_unmarked_state(DFA)
            NFA_states = DFA.get(state).get('states')
            U = epsilon_closure_states(NFA,move(NFA,NFA_states,transition))
            unique_state = unique_state_set(DFA,U)
            if unique_state is None:
                last_DFA_State_symbol += 1
                if len(list(set(U).intersection(terminating_states))) > 0:
                    DFA.update({chr(last_DFA_State_symbol): DFA_state(U,True)})
                else:
                    DFA.update({chr(last_DFA_State_symbol): DFA_state(U,False)})
                states.append(chr(last_DFA_State_symbol))
                DFA.get(state).update({transition : chr(last_DFA_State_symbol)})
            else:
                DFA.get(state).update({transition : unique_state})

        DFA.get(state).update({"marked":True})

    
    #remove the marked attribute
    for state in DFA:
        if state != "StartingState":
            DFA.get(state).pop("marked")
        
    return DFA


    #########################MINIMIZATION#########################

def get_transitions(DFA):
    transitions = []
    for state in DFA.keys():
        for transition in DFA.get(state):
            if transition not in transitions and transition != 'states' and transition != 'IsTerminating' and state != 'StartingState' : 
                transitions.append(transition)
    return transitions

def get_accepting_states(DFA):
    accepting_states = []
    for state in DFA.keys():
        if state != "StartingState" and DFA.get(state).get('IsTerminating') == True:
            accepting_states.append(state)
    return accepting_states

def get_non_accepting_states(DFA):
    non_accepting_states = []
    for state in DFA.keys():
        if state != "StartingState" and DFA.get(state).get('IsTerminating') == False:
            non_accepting_states.append(state)
    return non_accepting_states


def get_partitions(DFA):
    partitions = [get_accepting_states(DFA) , get_non_accepting_states(DFA)]
    transitions = get_transitions(DFA)
    for transition in transitions: # for each transition in the DFA e.g. a , b
        new_partitions = [] # new partitions after the transition
        for partition in partitions: # for each partition in the partitions e.g. [A,B,C] , [D] 
            partition_dict = {}
            for state in partition: # for each state in the partition e.g. A , B , C
                if DFA.get(state).get(transition) in partition_dict.keys(): # if the transition of the state is already in the partition_dict ,transition is The state that the transition leads to
                    partition_dict.get(DFA.get(state).get(transition)).append(state) 
                else:
                    partition_dict[DFA.get(state).get(transition)] = [state]
            for key in partition_dict.keys(): # for each key in the partition_dict e.g. A , B , C
                new_partitions.append(partition_dict.get(key)) # add the partition to the new_partitions
        partitions = new_partitions # update the partitions
    return partitions


# merge the partitions to get the minimum DFA
def merge_partitions(DFA,partitions):
    for partition in partitions:
        if len(partition) > 1:
            for state in partition:
                if state != partition[0]:
                    DFA.get(partition[0]).update(DFA.get(state))
                    del DFA[state]
                
                for state in DFA.keys():
                    for transition in DFA.get(state):
                        if transition != 'states' and transition != 'IsTerminating' and state != 'StartingState':
                            if DFA.get(state).get(transition) in partition:
                                DFA.get(state)[transition] = partition[0]
                
    return DFA



def minimize_DFA(DFA , file_name = "MIN_DFA" ):
    partitions = get_partitions(DFA)
    min_DFA = merge_partitions(DFA,partitions)
    file = open(file_name, "w")
    json.dump(min_DFA , file)
    file.close()
    return min_DFA

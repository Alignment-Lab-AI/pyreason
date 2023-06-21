import numba
import numpy as np

import pyreason.scripts.numba_wrapper.numba_types.rule_type as rule
import pyreason.scripts.numba_wrapper.numba_types.label_type as label
import pyreason.scripts.numba_wrapper.numba_types.interval_type as interval


def parse_rule(rule_text: str, name: str, infer_edges: bool = False, immediate_rule: bool = False) -> rule.Rule:
    # First remove all spaces from line
    r = rule_text.replace(' ', '')

    # Separate into head and body
    head, body = r.split('<-')

    # Extract delta_t of rule if it exists else set it to 0
    t = ''
    is_digit = True
    while is_digit:
        if body[0].isdigit():
            t += body[0]
            body = body[1:]
        else:
            is_digit = False

    if t == '':
        t = 0
    else:
        t = int(t)

    # Raw parsing steps
    # 1. Remove whitespaces
    # 2. replace ) by )) and ] by ]] so that we can split without damaging the string
    # 3. Split with ), and then for each element of list, split with ], and add to new list
    # 4. Then replace ]] with ] and )) with ) in for loop
    # 5. Add :[1,1] to the end of each element if a bound is not specified
    # 6. Then split each element with :
    # 7. Transform bound strings into pr.intervals

    # 2
    body = body.replace(')', '))')
    body = body.replace(']', ']]')

    # 3
    body = body.split('),')
    split_body = []
    for b in body:
        split_body.extend(b.split('],'))

    # 4
    for i in range(len(split_body)):
        split_body[i] = split_body[i].replace('))', ')')
        split_body[i] = split_body[i].replace(']]', ']')

    # 5
    for i in range(len(split_body)):
        if split_body[i][-1] != ']':
            split_body[i] += ':[1,1]'

    # 6
    body_clauses = []
    body_bounds = []
    for b in split_body:
        clause, bound = b.split(':')
        body_clauses.append(clause)
        body_bounds.append(bound)

    # 7
    for i in range(len(body_bounds)):
        bound = body_bounds[i]
        l, u = _str_bound_to_bound(bound)
        body_bounds[i] = [l, u]

    # Find the target predicate
    if head[-1] != ']':
        head += ':[1,1]'
    head, head_bound = head.split(':')
    target_bound = list(_str_bound_to_bound(head_bound))
    idx = head.find('(')
    target = head[:idx]
    target = label.Label(target)

    # Variable(s) in the head of the rule
    end_idx = head.find(')')
    head_variables = head[idx + 1:end_idx].split(',')

    # Assign type of rule
    rule_type = 'node' if len(head_variables) == 1 else 'edge'

    # Get the variables in the body
    body_predicates = []
    body_variables = []
    for clause in body_clauses:
        idx = clause.find('(')
        body_predicates.append(clause[:idx])
        body_variables.append(clause[idx+1:-1].split(','))

    # Replace the variables in the body with source/target if they match the variables in the head
    # If infer_edges is true, then we consider all rules to be node rules, we infer the 2nd variable of the target predicate from the rule body
    # Else we consider the rule to be an edge rule and replace variables with source/target
    # Node rules with possibility of adding edges
    if infer_edges or len(head_variables) == 1:
        head_source_variable = head_variables[0]
        for i in range(len(body_variables)):
            for j in range(len(body_variables[i])):
                if body_variables[i][j] == head_source_variable:
                    body_variables[i][j] = '__target'
    # Edge rule, no edges to be added
    elif len(head_variables) == 2:
        for i in range(len(body_variables)):
            for j in range(len(body_variables[i])):
                if body_variables[i][j] == head_variables[0]:
                    body_variables[i][j] = '__source'
                elif body_variables[i][j] == head_variables[1]:
                    body_variables[i][j] = '__target'

    # Start setting up clauses
    # clauses = [c1, c2, c3, c4]
    # thresholds = [t1, t2, t3, t4]

    # Array of thresholds to keep track of for each neighbor criterion. Form [(comparison, (number/percent, total/available), thresh)]
    thresholds = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, numba.types.UniTuple(numba.types.string, 2), numba.types.float64)))

    # Array to store clauses for nodes: node/edge, [subset]/[subset1, subset2], label, interval
    clauses = numba.typed.List.empty_list(numba.types.Tuple((numba.types.string, label.label_type, numba.types.UniTuple(numba.types.string, 2), interval.interval_type)))

    # Loop though clauses
    for predicate, variables, bounds in zip(body_predicates, body_variables, body_bounds):
        # Neigh criteria
        clause_type = 'node' if len(variables) == 1 else 'edge'
        subset = (variables[0], variables[0]) if clause_type == 'node' else (variables[0], variables[1])
        l = label.Label(predicate)
        bnd = interval.closed(bounds[0], bounds[1])
        clauses.append((clause_type, l, subset, bnd))

        # Threshold.
        quantifier = 'greater_equal'
        quantifier_type = ('number', 'total')
        thresh = 1
        thresholds.append((quantifier, quantifier_type, thresh))

    # Assert that there are two variables in the head of the rule if we infer edges
    # Add edges between head variables if necessary
    if infer_edges:
        assert len(head_variables) == 2, 'Cannot infer edges with a node rule. There have to be two variables in the head'
        var = '__target' if head_variables[0] == head_variables[1] else head_variables[1]
        edges = ('__target', var, target)
    else:
        edges = ('', '', label.Label(''))

    # Bound to set atom if rule fires
    bnd = interval.closed(*target_bound)
    ann_fn = ''
    ann_label = label.Label('')

    weights = np.ones(len(body_predicates), dtype=np.float64)
    weights = np.append(weights, 0)

    r = rule.Rule(name, rule_type, target, numba.types.uint16(t), clauses, bnd, thresholds, ann_fn, ann_label, weights, edges, immediate_rule)
    return r


def _str_bound_to_bound(str_bound):
    str_bound = str_bound.replace('[', '')
    str_bound = str_bound.replace(']', '')
    l, u = str_bound.split(',')
    return float(l), float(u)

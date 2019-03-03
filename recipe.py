#!/usr/bin/python

import re
import sys

#fname = '/Users/ezra/Documents/Sunday Family Dinner/dec 2/moroccan ingredients.calca'
fname = sys.argv[1]

results = {}

def trim(s):
    s = re.sub(r'^ *', '', s)
    s = re.sub(r' *$', '', s)
    return s

# TO DO: depluralization

# To do: support ranges, parentheticals, processing adjectives, mismatched units
processing_adjective = r' *(diced|grated|chopped|sliced|dried|minced|ground|sliced|(un)?bleached|boiling|boiled|rinsed|warm|cold)'

def simplify(typ):
    typ = re.sub(r' *(\([^)]*\))', '', typ)
    typ = re.sub(r', [^,]*,', '', typ)
    typ = re.sub(r', [^,()0-9]*$', '', typ)
    typ = re.sub(processing_adjective, '', typ)
    return typ

def stem(name):
    name = re.sub(r'\.', r'', name)
    name = re.sub(r's$', r'', name)
    name = re.sub(r's$', r'', name)
    return name.lower()

canon_unit = {
    'tablespoon': 'tbsp',
    'teaspoon': 'tsp',
    'c': 'cup',
    'pound': 'lb',
    'gram': 'g',
    }

def normalize(name):
    name = stem(name)
    name = canon_unit.get(name, name)
    return name

unit_conversions = {
    ('tbsp', 'tsp'): 3,
    ('cup', 'tbsp'): 0.0625
    }

def align(uni, uni_stant, qua):
    if uni_stant == uni:
        return (qua, uni)
    if (uni_stant, uni) in unit_conversions:
        qua = qua * unit_conversions[(uni_stant, uni)]
        uni = uni_stant
        return (qua, uni)
    else:
        return None

def add(dict, key, qua, uni):
    uni = normalize(uni)
    if key not in dict:
        dict[key] = []
    for i, (qua_stant, uni_stant) in enumerate(dict[key]):
        x = align(uni, uni_stant, qua)
        if x == None:
            continue
        else:
            qua_new, uni_new = x
            print "Consolidating {} {} and {} {} {} to {} {}".format(
                qua,uni, qua_stant, uni_stant, typ, qua_new + qua_stant, uni_new)
            dict[key][i] = (qua_new + qua_stant, uni_new)
            return
    dict[key] += [(qua, uni)]

# TODO: There is a problem with "fl oz" because a previous stage
# breaks all tokens on spaces, so "fl oz" is never recognized as
# a token or a unit.
def is_unit(str):
    return re.match(r'cup|can|tbsp|tsp|large|small|medium|stalk|bunch|lb|package|clove|trace|g|gram|oz|fl oz|fluid ounce', normalize(str)) != None

def is_comment(line):
    return re.match(r'^ *#', line) or re.match(r'^[\s]*$', line)

with open(fname, 'r') as f:
    lineno = 1
    for line in f:
        if is_comment(line):
            continue

        m = re.match(r'(?:.*=> *)?([0-9.0-9]+)? *(.*)', line)
        if m == None:
            print "Ignoring {}".format(line)
            continue

        (qua, unityp) = m.groups()
        m = re.match(r'([^ ]*)(.*)', unityp)
        if m == None or not m.groups()[1] or not is_unit(m.groups()[0]):
            uni, typ = '', unityp
        else:
            uni, typ = m.groups()
        if uni == None:
            uni = ''
        if qua == None:
            qua = '1'
        typ = simplify(typ)
        typ = trim(typ)
        if not re.match(r'[a-zA-Z]', typ):
            raise Exception("Unknown ingredient '{}' on line '{}'".format(typ, line))
        add(results, typ, float(qua), uni)

    print "\n# Shopping List"
    sorted_results = sorted(results.items())
    for typ, terms in sorted_results:
        for (qua, uni) in terms:
            if abs(qua-int(qua)) < 0.0125:
                print "{:.0f} {} {}".format(qua, uni, typ)
            else:
                print "{} {} {}".format(qua, uni, typ)

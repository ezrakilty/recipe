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
processing_adjective = r' *(diced|grated|chopped|sliced|dried|minced|(freshly *)?ground|sliced|(un)?bleached|boiling|boiled|rinsed|warm|cold)'

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

# TODO: I have seen "ounces" in a recipe, referring to fl oz. How can
# I deduce that it is talking about fluid ounces, not pounds, so as to
# then do a conversion to cups?
unit_conversions = {
    ('cup', 'fl oz'): 8,
    ('tbsp', 'tsp'): 1/3,
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
        print "No conversion to align {} and {}".format(uni_stant, uni)
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
# TODO: There is a problem with strings like "14-ounce can": Do we
# want to parse that as 1 count of a can-like unit, or as 14 ounces?
# Either way, it currently doesn't parse.
def is_unit(str):
    return re.match(r'cup|can|tbsp|tsp|large|small|medium|stalk|bunch|lb|package|clove|trace|g|gram|oz|fl oz|fluid ounce', normalize(str)) != None

def is_comment(line):
    return re.match(r'^ *#', line) or re.match(r'^[\s]*$', line)

WHOLE_NUMBER_REGEX = r'[0-9]'

FRACTION_PARTS_REGEX = r'([0-9]+ +)?([0-9]+) */ *([0-9]+)'

# TODO: Would prefer to use some rational representation & arithmetic
# for rational quantities, rather than get stuff like "0.33333333 cup oil"
def normalize_fraction(frac_str):
    m = re.match(FRACTION_PARTS_REGEX, frac_str)
    if m:
        who, num, den = m.groups()
        who = who or 0
        return int(who) + float(num) / int(den)
    else:
        return float(frac_str)

NUMBER_REGEX = r'(?:[0-9]+ +)?[0-9.]+(?:/[0-9]+)?'

with open(fname, 'r') as f:
    lineno = 1
    for line in f:
        if is_comment(line):
            continue

        m = re.match(r'(?:.*=> *)?(' + NUMBER_REGEX + r')? *(.*)', line)
        if m == None:
            print "Ignoring {}".format(line)
            continue

        (qua, unityp) = m.groups()
        print qua, unityp
        m = re.match(r'([^ ]*)(.*)', unityp)
        if m == None or not m.groups()[1] or not is_unit(m.groups()[0]):
            uni, typ = '', unityp
        else:
            uni, typ = m.groups()
        if uni == None:
            uni = ''
        if qua == None:
            qua = '1'
        if qua:
            qua = normalize_fraction(qua)
        typ = simplify(typ)
        typ = trim(typ)
        if not re.match(r'[a-zA-Z]', typ):
            raise Exception("Unknown ingredient '{}' on line '{}'".format(typ, line))
        add(results, typ, qua, uni)

    print "\n# Shopping List"
    sorted_results = sorted(results.items())
    for typ, terms in sorted_results:
        for (qua, uni) in terms:
            if abs(qua-int(qua)) < 0.0125:
                print "{:.0f} {} {}".format(qua, uni, typ)
            else:
                print "{} {} {}".format(qua, uni, typ)

# TODO: Sometimes we see ranges, like "1/4 - 1/2 tbsp salt."
# Other times that notation might be used for fractions > 1, such as "1 - 1/2 cup broth."

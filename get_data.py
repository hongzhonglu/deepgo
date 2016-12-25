#!/usr/bin/env python
import sys
import numpy as np
import pandas as pd
from utils import (
    get_gene_ontology,
    get_go_set,
    get_anchestors,
    BIOLOGICAL_PROCESS,
    MOLECULAR_FUNCTION,
    CELLULAR_COMPONENT)
from aaindex import AAINDEX
from text import get_text_reps


FUNCTION = 'bp'
ORG = ''
TT = 'data'

args = sys.argv
if len(args) == 4:
    print args
    TT = args[1]
    if args[2]:
        ORG = '-' + args[2]
    else:
        ORG = ''
    FUNCTION = args[3]

FUNC_DICT = {
    'cc': CELLULAR_COMPONENT,
    'mf': MOLECULAR_FUNCTION,
    'bp': BIOLOGICAL_PROCESS}

GO_ID = FUNC_DICT[FUNCTION]

DATA_ROOT = 'data/cafa3/'
FILENAME = TT + '.txt'

go = get_gene_ontology('go.obo')

func_df = pd.read_pickle(DATA_ROOT + FUNCTION + ORG + '.pkl')
functions = func_df['functions'].values
func_set = get_go_set(go, GO_ID)
print len(functions)
go_indexes = dict()
for ind, go_id in enumerate(functions):
    go_indexes[go_id] = ind


def load_data():
    proteins = list()
    sequences = list()
    gos = list()
    labels = list()
    indexes = list()
    trigrams = list()
    with open(DATA_ROOT + FILENAME, 'r') as f:
        for line in f:
            items = line.strip().split('\t')
            go_list = items[2].split('; ')
            go_set = set()
            for go_id in go_list:
                if go_id in func_set:
                    go_set |= get_anchestors(go, go_id)
            if not go_set or GO_ID not in go_set:
                continue
            go_set.remove('root')
            go_set.remove(GO_ID)
            gos.append(go_list)
            proteins.append(items[0])
            sequences.append(items[1])
            idx = [0] * len(items[1])
            tri = [0] * (len(items[1]) - 4)
            for i in range(len(idx)):
                idx[i] = AAINDEX[items[1][i]] + 1
            for i in xrange(len(tri)):
                i1 = AAINDEX[items[1][i]]
                i2 = AAINDEX[items[1][i + 1]]
                i3 = AAINDEX[items[1][i + 2]]
                tri[i] = i1 * 400 + i2 * 20 + i3 + 1
            indexes.append(idx)
            trigrams.append(tri)
            label = [0] * len(functions)
            for go_id in go_set:
                if go_id in go_indexes:
                    label[go_indexes[go_id]] = 1
            labels.append(label)

    return proteins, sequences, indexes, gos, labels, trigrams


def load_rep():
    data = dict()
    with open('data/uni_reps.tab', 'r') as f:
        for line in f:
            it = line.strip().split('\t')
            prot_id = it[0]
            rep = np.array(map(float, it[1:]))
            data[prot_id] = rep
    return data


def filter_data():
    prots = set()
    with open('data/uni_reps.tab', 'r') as f:
        for line in f:
            items = line.strip().split('\t')
            prots.add(items[0])
    train = list()
    text_reps = get_text_reps()
    with open('data/cafa3/uniprot_sprot.tab', 'r') as f:
        for line in f:
            items = line.strip().split('\t')
            if items[0] not in prots:
                train.append(line)
    print(len(train))
    with open('data/cafa3/data.txt', 'w') as f:
        for line in train:
            f.write(line)


def load_org_df():
    proteins = list()
    orgs = list()
    with open('data/uniprot-all-org.tab') as f:
        for line in f:
            items = line.strip().split('\t')
            prot_id = items[0]
            org_id = items[2]
            proteins.append(prot_id)
            orgs.append(org_id)
    df = pd.DataFrame({'proteins': proteins, 'orgs': orgs})
    return df


def run(*args, **kwargs):
    proteins, sequences, indexes, gos, labels, trigrams = load_data()
    data = {
        'proteins': proteins,
        'sequences': sequences,
        'indexes': indexes,
        'gos': gos,
        'labels': labels,
        'trigrams': trigrams}
    rep = load_rep()
    text_reps = get_text_reps()
    rep_list = list()
    rep_n = 0
    text_n = 0
    for prot_id in proteins:
        text_rep = np.zeros((128,), dtype='float32')
        net_rep = np.zeros((256,), dtype='float32')
        if prot_id in text_reps:
            text_rep = text_reps[prot_id]
            text_n += 1
        if prot_id in rep:
            net_rep = rep[prot_id]
            rep_n += 1
        rep_list.append(net_rep)
    print(len(rep_list), rep_n, text_n)
    data['rep'] = rep_list
    df = pd.DataFrame(data)
    org_df = load_org_df()
    print(len(df))
    df = pd.merge(df, org_df, on='proteins', how='left')
    print(len(df))
    df.to_pickle(DATA_ROOT + TT + ORG + '-' + FUNCTION + '.pkl')


def main(*args):
    run()
    # filter_data()


if __name__ == '__main__':
    main(*sys.argv)


#!/usr/bin/env python3

"""
Generate measurements with data/ground truth for experiment 05
"""

import csv
import os
import sqlite3
from datetime import datetime
import math
import numpy
import json
from scipy import interpolate
import re

MODEL_MAP_EPFL_ANDROID = [
    (0, 0),
    ('1AliceGS10', 'SM-G973F'),
    ('2BobGS10', 'SM-G973F'),
    ('3CharlieGS10e', 'SM-G970F'),
    ('4DaveGS10e', 'SM-G970F'),
    ('5EmmaGA40', 'SM-A405FN'),
    ('6HansGS20', 'SM-G981B/DS'),
    ('7IvanGS10', 'SM-G973F'),
    ('8LeoGA90', 'SM-A908B'),
    ('9MegGS10', 'SM-G973F'),
    ('10NellyGA51', 'SM-A515F'),
    ('11OllyGS10', 'SM-G973F'),
    ('12PepGS10', 'SM-G973F'),
    ('13QueenGA40', 'SM-A405FN'),
    ('RobGA40', 'SM-A405FN'),
    ('15SamGA40', 'SM-A405FN'),
    ('16TomGA40', 'SM-A405FN'),
    ('17HugoGA40', 'SM-A405FN'),
    ('18VeraGA40', 'SM-A405FN'),
    ('19ZedGA40', 'SM-A405FN'),
    ('20YanGA40', 'SM-A405FN'),
    ('21WillyGA40', 'SM-A405FN'),
    ('22JaneGA40', 'SM-A405FN'),
    ('23AnnaGP4', 'GA01187-DE'),
    ('24BorisGP4', 'GA01187-DE')
]

def crt(filename, rm_old=False):
    if rm_old and os.path.exists('{}.sqlite'.format(filename)):
        os.remove('{}.sqlite'.format(filename))
        print('Removed old {}.sqlite'.format(filename))

    try:
        conn = sqlite3.connect('{}.sqlite'.format(filename))
        conn.execute('''CREATE TABLE results(
            {}    INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            {}    INT NOT NULL,
            {}    TEXT NOT NULL,
            {}    INT NOT NULL,
            {}    TEXT NOT NULL,
            {}    REAL NOT NULL,
            {}    INTEGER NOT NULL,
            {}    INTEGER NOT NULL,
            {}    REAL
        )'''.format('db_id', 'receiver_id', 'receiver_model',
            'transmitter_id', 'transmitter_model', 'timestamp',
            'rssi', 'tx_power', 'ground_truth_distance'))
    except sqlite3.OperationalError as e:
        print(e, 'if you want a new one: rm {}.sqlite'.format(filename))

    conn.close()


def put_results(filename, results):
    conn = sqlite3.connect('{}.sqlite'.format(filename))

    c = conn.cursor()
    iq = """INSERT INTO results ({}, {}, {}, {}, {}, {}, {}, {})
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);""".format(
            'timestamp', 'transmitter_id', 'transmitter_model', 'tx_power',
            'rssi', 'receiver_id', 'receiver_model', 'ground_truth_distance')
    c.executemany(iq, results)
    conn.commit()

    conn.close()


def get_raw_measurements(path, rx):
    results = []

    if len(str(rx)) == 1:
        db_path = '{}/0{}.sqlite'.format(path, rx)
    else:
        db_path = '{}/{}.sqlite'.format(path, rx)
    conn = sqlite3.connect(db_path)

    c = conn.cursor()
    c.execute('SELECT timestamp, star, tx_power_level, rssi FROM handshakes')
    temp = c.fetchall()

    for i in range(0, len(temp)):
        # NOTE: fix Rob that is missing 14
        if chr(temp[i][1][0]) == 'R':
            tx = 14
        else:
            # NOTE: if second char is not A then greater than 9
            first = int(chr(temp[i][1][0]))
            second = chr(temp[i][1][1])
            if (first == 1 and second != 'A') or (first == 2 and second != 'B'):
                tx = int(chr(temp[i][1][0]) + chr(temp[i][1][1]))
            else:
                tx = int(chr(temp[i][1][0]))
        # NOTE: gtd added later with add_gtd
        gtd = -1.0
        results.append(
             # timestamp tx  tx_model                       tx_power
            (temp[i][0], tx, MODEL_MAP_EPFL_ANDROID[tx][1], temp[i][2],
                # rssi      rx  rx_model                       gtd
                temp[i][3], rx, MODEL_MAP_EPFL_ANDROID[rx][1], gtd)
            )

    conn.close()

    return results


def comp_dist(el1, el2):
    if not el1 or not el2:
        return numpy.nan
    dx = el1[0] - el2[0]
    dy = el1[1] - el2[1]
    distance = math.sqrt( pow(dx,2) + pow(dy,2) )
    return distance

def convert_time(ts):
    if '.' in ts:
        timePattern = re.search(r'(.*?)\.([0-9]*?)$', ts)
        timestamp = datetime.strptime(timePattern.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
        timestamp = timestamp*1000 + (int(timePattern.group(2))/1000)
        return int(timestamp)
    else: 
        return int(datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").timestamp()*1000)

def convert_time_list(timestamp_list):
    return [convert_time(ts) for ts in timestamp_list]

def groundTruthFromCV(json_files):
    groundtD = { json_file : json.load(open(json_file)) for json_file in json_files }
    sortedKeys = sorted(groundtD.keys())
    timestamps = numpy.concatenate( [numpy.array(convert_time_list(groundtD[inp]['datetime'])) for inp in sortedKeys] )

    uniqueIDs = numpy.unique(numpy.concatenate([numpy.array(list(groundtD[inp].keys())) for inp in sortedKeys]) )
    uniqueIDs = [i for i in uniqueIDs if not 'datetime' in i.lower()]

    groundTruthDistance = {}
    for u1 in uniqueIDs:
        groundTruthDistance[int(u1)] = {}
        for u2 in uniqueIDs:
            distl = []
            for inp in sortedKeys:
                if u1 in groundtD[inp] and u2 in groundtD[inp]:
                    distl.append( numpy.array( [comp_dist(el1, el2) for el1, el2 in zip(groundtD[inp][u1], groundtD[inp][u2]) ] ) )
                else:
                    distl.append( numpy.full(len(groundtD[inp]['datetime']), numpy.nan) )
            groundTruthDistance[int(u1)][int(u2)] = numpy.concatenate(distl)
    return timestamps, groundTruthDistance  

def get_gtd(rx, tx, ts, gtd_ts, gtd):
    # was the person was visible any time during the experiment?
    if rx not in gtd or tx not in gtd:
        return numpy.nan
    # get closest timestamp
    tsidx = min(range(len(gtd_ts)), key = lambda i: abs(gtd_ts[i]-ts))
    # check if we're in range
    granularity = (gtd_ts[1] - gtd_ts[0])/2 + 1
    if abs(gtd_ts[tsidx] - ts) > granularity:
        return numpy.nan
    # print('{} {} {} {} {} {}'.format(rx, tx, ts, gtd_ts[tsidx], tsidx, gtd[rx][tx][tsidx]))
    return gtd[rx][tx][tsidx]

def add_gtd(results, gtd_ts, gtd):
    res = []
    for timestamp, tx, tx_model, tx_power, rssi, rx, rx_model, ogtd in results:
        cgtd = get_gtd(rx, tx, timestamp, gtd_ts, gtd)
        if cgtd == numpy.nan:
            cgtd = -1
        #if ogtd == cgtd:
        #    print('{} {}'.format(ogtd, cgtd))
        res.append((timestamp, tx, tx_model, tx_power, rssi, rx, rx_model, cgtd))
    return res

if __name__ == "__main__":

    crt('scenario01-lunch', rm_old=True)
    results_list = []
    cvfiles = [
        'ground_truth/1_lunch_part1.json',
        'ground_truth/1_lunch_part2.json',
        'ground_truth/1_lunch_part3.json'
    ]
    gtd_ts, gtd = groundTruthFromCV(cvfiles)
    for i in range(1, 18):
        results_list.append(get_raw_measurements('scenario01-lunch', i))
    results = [item for sublist in results_list for item in sublist]
    results = add_gtd(results, gtd_ts, gtd)
    put_results('scenario01-lunch', results)

    crt('scenario02-train', rm_old=True)
    results_list = []
    cvfiles = [
        'ground_truth/2_cff_part1.json',
        'ground_truth/2_cff_part2.json',
        'ground_truth/2_cff_part3.json'
    ]
    gtd_ts, gtd = groundTruthFromCV(cvfiles)
    for i in range(1, 21):
        results_list.append(get_raw_measurements('scenario02-train', i))
    results = [item for sublist in results_list for item in sublist]
    results = add_gtd(results, gtd_ts, gtd)
    put_results('scenario02-train', results)


    crt('scenario03-office', rm_old=True)
    results_list = []
    cvfiles = [
        'ground_truth/3_coworking_part1.json',
        'ground_truth/3_coworking_part2.json',
        'ground_truth/3_coworking_part3.json'
    ]
    gtd_ts, gtd = groundTruthFromCV(cvfiles)
    for i in range(10, 21):
        results_list.append(get_raw_measurements('scenario03-office', i))
    results = [item for sublist in results_list for item in sublist]
    results = add_gtd(results, gtd_ts, gtd)
    put_results('scenario03-office', results)

    crt('scenario04-queue', rm_old=True)
    results_list = []
    cvfiles = [
        'ground_truth/4_queue_part1.json',
        'ground_truth/4_queue_part2.json',
    ]
    gtd_ts, gtd = groundTruthFromCV(cvfiles)
    for i in range(1, 21):
        if i == 3:  # NOTE: 03.sqlite is empty
            continue
        results_list.append(get_raw_measurements('scenario04-queue', i))
    results = [item for sublist in results_list for item in sublist]
    results = add_gtd(results, gtd_ts, gtd)
    put_results('scenario04-queue', results)

    crt('scenario05-party', rm_old=True)
    results_list = []
    cvfiles = [
        'ground_truth/5_party_part1.json',
        'ground_truth/5_party_part2.json',
        'ground_truth/5_party_part3.json'
    ]
    gtd_ts, gtd = groundTruthFromCV(cvfiles)
    for i in range(1, 21):
        if i == 15:  # NOTE: 15.sqlite is empty
            continue
        results_list.append(get_raw_measurements('scenario05-party', i))
    results = [item for sublist in results_list for item in sublist]
    results = add_gtd(results, gtd_ts, gtd)
    put_results('scenario05-party', results)

    # TODO: ground truth data for this scenario
    crt('scenario06-walls', rm_old=True)
    for i in range(1, 11):
        results = get_raw_measurements('scenario06-walls', i)
        put_results('scenario06-walls', results)

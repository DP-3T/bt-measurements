# exp25.py

import os
import sqlite3
import json
import pyshark

from datetime import datetime

MODEL_RX_TX_COMPENSATION = { # date: 200813
# Official Google calibration of 20/08/13
    'SM-G973F': [5.0, -24.0],
    'SM-G970F': [5.0, -24.0],
    'SM-A405FN': [5.0, -24.0],
    'SM-A515F': [5.0, -24.0],
    'SM-A908B': [5.0, -24.0],
    'SM-G981B/DS': [5.0, -24.0] # SM-G981B in table
}

MODEL_MAP_EPFL_ANDROID = [
     0,
    'SM-G973F',
    'SM-G973F',
    'SM-G970F',
    'SM-G970F',
    'SM-A405FN',
    'SM-G981B/DS',
    'SM-G973F',
    'SM-A908B',
    'SM-G973F',
    'SM-A515F',
    'SM-G973F',
    'SM-G973F',
    'SM-A405FN',
    'SM-A405FN',
    'SM-A405FN',
    'SM-A405FN',
    'SM-A405FN',
    'SM-A405FN',
    'SM-A405FN',
    'SM-A405FN',
    'SM-A405FN',
    'SM-A405FN',
    'GA01187-DE',
    'GA01187-DE',
]

MODEL_MAP_EPFL_IPHONES = [0,
    'iPhone7',
    'iPhone11Pro',
    'iPhone11',
    'iPhone7',
    'iPhone11Pro',
    'iPhoneXR',
    'iPhoneXS',
    'iPhoneXS',
    'iPhoneXR',
    'iPhone11',
]

TX_POWER_IPHONES = [0,
     3, # 1, iPhone 7
     3, # 2, iPhone 11Pro
     1, # 3, iPhone 11
     3, # 4, iPhone 7
     3, # 5, iPhone 11Pro
     0, # 6, iPhone XR
     3, # 7, iPhone XS
     3, # 8, iPhone XS
     0, # 9, iPhone XR
     1, # 10, iPhone 11
]


IDs = [103, 110, 2, 3, 6, 8, 10, 18]

HCI_IDs = [103, 110, 2, 3, 6, 8]
VS_IDs  = [10, 18]

# NOTE: encoded as 100 + id to avoid clashes with Android
IPHONE_IDs = [103, 110]


def parse_hcicmds(path, rx, ti):
    """Use to parse HCI Set Ext Adv Data

    """
    ephids = []

    rx_str = str(rx)
    if len(rx_str) == 1:
        rx_str = '0'+rx_str

    with open(path+rx_str+'.json', "r") as rf:
        pkts = json.load(rf)

    for pkt in pkts:
        # NOTE: exclude packets outside the experimental range
        pkt_timestamp = pkt['_source']['layers']['frame']['frame.time_epoch']
        pkt_datetime =  datetime.fromtimestamp(round(float(pkt_timestamp)))
        if pkt_datetime < ti[0] or pkt_datetime > ti[1]:
            continue
        # print(pkt_datetime)

        pkt_source = pkt['_source']['layers']['bluetooth']['bluetooth.src_str']
        # NOTE:HCI cmd
        if pkt_source == 'host':
            pkt_ads = pkt['_source']['layers']['bthci_cmd']['btcommon.eir_ad.advertising_data']
            pkt_ephid = pkt_ads['btcommon.eir_ad.entry']['btcommon.eir_ad.entry.service_data']
            # print(pkt_ephid)
            if pkt_ephid not in ephids:
                ephids.append(pkt_ephid)
    print('')
    print('rx', rx)
    print('ephids', ephids)
    print('len(ephids)', len(ephids))
    print('')

    with open(path+rx_str+'.ephids', "w") as wf:
        for ephid in ephids:
            wf.write(ephid+'\n')


def get_ephids(path):
    """Returns a dict of ephids indexed by filename
    """

    ephids = {}

    for i in IDs:
        i_str = str(i)
        if len(i_str) == 1:
            i_str = '0'+i_str
        ephids[i_str] = []
        with open(path+i_str+'.ephids', "r") as rf:
            for line in rf:
                if line == '\n':
                    continue
                ephid = line.strip()
                assert len(ephid) == 59   # 20 bytes like aa:bb:..:ff
                ephids[i_str].append(ephid)

    return ephids


def parse_hcievents(path, rx, ti):
    """Use to parse HCI LE Meta Adv Report

    """
    results = []

    ephids = get_ephids(path)
    rx_str = str(rx)
    if len(rx_str) == 1:
        rx_str = '0'+rx_str

    with open(path+rx_str+'.json', "r") as rf:
        pkts = json.load(rf)

    for pkt in pkts:
        # NOTE: exclude packets outside the experimental range
        pkt_timestamp = pkt['_source']['layers']['frame']['frame.time_epoch']
        pkt_datetime =  datetime.fromtimestamp(round(float(pkt_timestamp)))
        if pkt_datetime < ti[0] or pkt_datetime > ti[1]:
            continue
        # print(pkt_datetime)

        pkt_source = pkt['_source']['layers']['bluetooth']['bluetooth.src_str']
        # NOTE:HCI cmd
        if pkt_source == 'controller':
            pkt_rssi = pkt['_source']['layers']['bthci_evt']['bthci_evt.rssi']
            # print('rssi', pkt_rssi)
            pkt_ads = pkt['_source']['layers']['bthci_evt']['btcommon.eir_ad.advertising_data']
            pkt_ephid = pkt_ads['btcommon.eir_ad.entry']['btcommon.eir_ad.entry.service_data']
            # print('ephid', pkt_ephid)

            for key, value in ephids.items():
                if pkt_ephid in ephids[key]:
                    # print('tx', key, pkt_ephid)
                    tx = int(key)
                    gtd = 1.0
                    if tx in IPHONE_IDs:
                        tmo = MODEL_MAP_EPFL_IPHONES[tx-100]
                        txpower = TX_POWER_IPHONES[tx-100]
                    else:
                        tmo = MODEL_MAP_EPFL_ANDROID[tx]
                        txpower = 0
                    if rx in IPHONE_IDs:
                        rmo = MODEL_MAP_EPFL_IPHONES[rx-100]
                    else:
                        rmo = MODEL_MAP_EPFL_ANDROID[rx]
                    results.append((pkt_timestamp, tx, tmo, txpower, pkt_rssi, rx, rmo, gtd))

    return results


def parse_vscmds(path, rx, ti):
    """Use to parse HCI LE Meta Adv Report

    """
    ephids = []

    rx_str = str(rx)
    if len(rx_str) == 1:
        rx_str = '0'+rx_str

    vs_rpi = 'bthci_cmd  and (frame contains 03:03:6f:fd:17:16:6f:fd)'
    pkts = pyshark.FileCapture(path+rx_str+'.btsnoop', display_filter=vs_rpi)
    raw_pkts = pyshark.FileCapture(path+rx_str+'.btsnoop', display_filter=vs_rpi,
            use_json=True, include_raw=True)

    i = 0
    for pkt in pkts:
        pkt_datetime = datetime.fromtimestamp(pkt.sniff_time.timestamp())
        if pkt_datetime < ti[0] or pkt_datetime > ti[1]:
            i += 1
            continue
        else:
            raw_ephid = raw_pkts[i].get_raw_packet().hex()[28:-8]
            # print(raw_ephid)
            assert len(raw_ephid) == 40

            ephid = ''
            for j in range(0,40,2):
                ephid += raw_ephid[j:j+2]
                if j != 38:
                    ephid += ':'

            if ephid not in ephids:
                ephids.append(ephid)
            i += 1

    print('')
    print('rx', rx)
    print('ephids', ephids)
    print('len(ephids)', len(ephids))
    print('')

    pkts.close()
    raw_pkts.close()

    with open(path+rx_str+'.ephids', "w") as wf:
        for ephid in ephids:
            wf.write(ephid+'\n')


def create_db(filename, rm_old=False):
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


if __name__ == "__main__":
    path = ''


    # NOTE: pklg export log with datetime +2 hours from our timezone
    start_datetime = datetime(2020, 6,  10,  9+2, 50, 00, 0)
    end_datetime =   datetime(2020, 6,  10, 17+2, 31, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in HCI_IDs:
        parse_hcicmds(path, i, ti)
    for i in VS_IDs:
        parse_vscmds(path, i, ti)

    create_db('scenario01-110-103', rm_old=True)
    start_datetime = datetime(2020, 6,  10,  9+2, 50, 00, 0)
    end_datetime =   datetime(2020, 6,  10, 11+2, 00, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in [110, 103]:
        results = parse_hcievents(path, i, ti)
        put_results('scenario01-110-103', results)

    create_db('scenario02-110-02', rm_old=True)
    start_datetime = datetime(2020, 6,  10, 11+2, 15, 00, 0)
    end_datetime =   datetime(2020, 6,  10, 12+2, 15, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in [110, 2]:
        results = parse_hcievents(path, i, ti)
        put_results('scenario02-110-02', results)

    create_db('scenario03-110-03', rm_old=True)
    start_datetime = datetime(2020, 6,  10, 12+2, 15, 00, 0)
    end_datetime =   datetime(2020, 6,  10, 13+2, 20, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in [110, 3]:
        results = parse_hcievents(path, i, ti)
        put_results('scenario03-110-03', results)

    create_db('scenario04-110-06', rm_old=True)
    start_datetime = datetime(2020, 6,  10, 13+2, 24, 00, 0)
    end_datetime =   datetime(2020, 6,  10, 14+2, 24, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in [110, 6]:
        results = parse_hcievents(path, i, ti)
        put_results('scenario04-110-06', results)

    create_db('scenario05-110-08', rm_old=True)
    start_datetime = datetime(2020, 6,  10, 14+2, 28, 00, 0)
    end_datetime =   datetime(2020, 6,  10, 15+2, 28, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in [110, 8]:
        results = parse_hcievents(path, i, ti)
        put_results('scenario05-110-08', results)

    create_db('scenario06-110-10', rm_old=True)
    start_datetime = datetime(2020, 6,  10, 15+2, 30, 00, 0)
    end_datetime =   datetime(2020, 6,  10, 16+2, 30, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in [110, 10]:
        results = parse_hcievents(path, i, ti)
        put_results('scenario06-110-10', results)

    create_db('scenario07-110-18', rm_old=True)
    start_datetime = datetime(2020, 6,  10, 16+2, 31, 00, 0)
    end_datetime =   datetime(2020, 6,  10, 17+2, 31, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in [110, 18]:
        results = parse_hcievents(path, i, ti)
        put_results('scenario07-110-18', results)

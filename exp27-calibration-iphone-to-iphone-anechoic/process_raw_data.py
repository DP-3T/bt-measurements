# exp27.py


import os
import sqlite3
import json
import pyshark

from datetime import datetime

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


IDs = [1,2, 6, 8, 10]
HCI_IDs = [2,8,10]
# NOTE: iPhone7 and XR
VS_IDs = [1,6]
assert len(IDs) == (len(HCI_IDs)+len(VS_IDs))


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
                    txpower = TX_POWER_IPHONES[tx]
                    tmo = MODEL_MAP_EPFL_IPHONES[tx]
                    rmo = MODEL_MAP_EPFL_IPHONES[rx]

                    results.append((pkt_timestamp, tx, tmo, txpower, pkt_rssi,
                        rx, rmo, gtd))

    return results


def parse_vscmds(path, rx, ti):
    """Use to parse HCI LE Meta Adv Report

    """
    ephids = []

    rx_str = str(rx)
    if len(rx_str) == 1:
        rx_str = '0'+rx_str

    vs_rpi = 'bthci_cmd  and (frame contains 03:03:6f:fd:17:16:6f:fd)'
    pkts = pyshark.FileCapture(path+rx_str+'.pklg', display_filter=vs_rpi)
    raw_pkts = pyshark.FileCapture(path+rx_str+'.pklg', display_filter=vs_rpi,
            use_json=True, include_raw=True)

    i = 0
    for pkt in pkts:
        pkt_datetime = datetime.fromtimestamp(pkt.sniff_time.timestamp())
        if pkt_datetime < ti[0] or pkt_datetime > ti[1]:
            i += 1
            continue
        else:
            # NOTE: remove first 17 bytes
            raw_ephid = raw_pkts[i].get_raw_packet().hex()[34:]
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
    start_datetime = datetime(2020, 6,  11,  9+2, 9, 00, 0)
    end_datetime =   datetime(2020, 6,  11, 13+2, 15, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in HCI_IDs:
        parse_hcicmds(path, i, ti)
    for i in [1]:
        parse_vscmds(path, i, ti)

    create_db('scenario01-10-08', rm_old=True)
    start_datetime = datetime(2020, 6,  11,  9+2,  9, 00, 0)
    end_datetime =   datetime(2020, 6,  11, 10+2, 10, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in [10, 8]:
        results = parse_hcievents(path, i, ti)
        put_results('scenario01-10-08', results)


    create_db('scenario02-10-06', rm_old=True)
    start_datetime = datetime(2020, 6,  11, 10+2, 12, 00, 0)
    end_datetime =   datetime(2020, 6,  11, 11+2, 12, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in [10, 6]:
        results = parse_hcievents(path, i, ti)
        put_results('scenario02-10-06', results)

    create_db('scenario03-10-02', rm_old=True)
    start_datetime = datetime(2020, 6,  11, 11+2, 13, 00, 0)
    end_datetime =   datetime(2020, 6,  11, 12+2, 13, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in [10, 2]:
        results = parse_hcievents(path, i, ti)
        put_results('scenario03-10-02', results)

    create_db('scenario04-10-01', rm_old=True)
    start_datetime = datetime(2020, 6,  11, 12+2, 15, 00, 0)
    end_datetime =   datetime(2020, 6,  11, 13+2, 15, 00, 0)
    ti = (start_datetime, end_datetime)
    for i in [10, 1]:
        results = parse_hcievents(path, i, ti)
        # print(results)
        put_results('scenario04-10-01', results)


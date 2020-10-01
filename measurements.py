#!/usr/bin/python3

"""
Collect helper functions to load data from sqlite files and apply different
calibration values.
"""

import sqlite3
import json

MODEL_RX_TX_COMPENSATION_OUR = {
# Based on our measurements in an anechoic chamber
    'iPhone7': [3.0, -5.0],
    'iPhoneXR': [0.5, 0.0],
    'iPhoneXS': [0.0, 1.0],
    'iPhone11': [0.0, 1.0], # no i11 - i11 measurements
    'iPhone11Pro': [0.0, 0.0],
    'SM-G973F': [-3.0, -24.0],
    'SM-G970F': [-5.0, -23.0],
    'SM-A405FN': [4.0, -24.0],
    'SM-A515F': [-7, -23.0],
    'SM-A908B': [-2.0, -20.0],
    'SM-G981B/DS': [3.0, -25.5]
}

MODEL_RX_TX_COMPENSATION = { # date: 200918
# Official Google calibration of 20/09/18
    'iPhone7': [0.0, 3.0],
    'iPhoneXR': [0.0, 0.0],
    'iPhoneXS': [0.0, 3.0],
    'iPhone11': [0.0, 1.0],
    'iPhone11Pro': [0.0, 3.0],
    'SM-G973F': [2.0, -29.0],
    'SM-G970F': [5.0, -24.0],
    'SM-A405FN': [2.0, -23.0],
    'SM-A515F': [5.0, -24.0],
    'SM-A908B': [5.0, -24.0],
    'SM-G981B/DS': [5.0, -24.0] # SM-G981B in table
}

MODEL_RX_TX_COMPENSATION_200813 = { # date: 200813
# Official Google calibration of 20/08/13
    'iPhone7': [0.0, 3.0],
    'iPhoneXR': [0.0, 0.0],
    'iPhoneXS': [0.0, 3.0],
    'iPhone11': [0.0, 1.0],
    'iPhone11Pro': [0.0, 3.0],
    'SM-G973F': [5.0, -24.0],
    'SM-G970F': [5.0, -24.0],
    'SM-A405FN': [5.0, -24.0],
    'SM-A515F': [5.0, -24.0],
    'SM-A908B': [5.0, -24.0],
    'SM-G981B/DS': [5.0, -24.0] # SM-G981B in table
}

MODEL_RX_TX_COMPENSATION_200613 = {
# Official Google calibration of 20/06/13
    'iPhone7': [0.0, 3.0],
    'iPhoneXR': [0.0, 0.0],
    'iPhoneXS': [0.0, 3.0],
    'iPhone11': [0.0, 1.0],
    'iPhone11Pro': [0.0, 3.0],
    'SM-G973F': [-3.0, -24.0],
    'SM-G970F': [-3.0, -24.0],
    'SM-A405FN': [-3.0, -24.0],
    'SM-A515F': [-3.0, -24.0],
    'SM-A908B': [-3.0, -24.0],
    'SM-G981B/DS': [-3.0, -24.0] # SM-G981B in table
}

MODEL_RX_TX_COMPENSATION_200530 = {
# early internal data used for testing
    'iPhone7': [0.0, 3.0],
    'iPhoneXR': [0.0, 0.0],
    'iPhoneXS': [0.0, 3.0],
    'iPhone11': [0.0, 1.0],
    'iPhone11Pro': [0.0, 3.0],
    'SM-G973F': [10.0, 0.0], # off
    'SM-G970F': [-4.0, -14.0],
    'SM-A405FN': [-4.0, -14.0],
    'SM-A515F': [-4.0, -14.0],
    'SM-A908B': [-4.0, -14.0],
    'SM-G981B/DS': [-4.0, -14.0]
}

# Google values taken from https://developers.google.com/android/exposure-notifications/ble-attenuation-computation


def get_measurements(filename, receiver, transmitter):
    '''
    Get measurements sent from a transmitter to a receiver.
    Returns an array of [RSSI] values
    '''
    results = []

    conn = sqlite3.connect(filename)
    c = conn.cursor()
    args = (receiver, transmitter)
    c.execute('SELECT rssi FROM results WHERE transmitter_id = ? AND receiver_id = ?', args)
    temp = c.fetchall()

    for i in range(0, len(temp)):
        if temp[i][0] < -20:
            # filter iPhone "special" values
            results.append(temp[i][0])

    conn.close()
    return results


def get_model(filename, phone_id):
    '''
    Get model of a transmitting phone.
    Returns a string
    '''
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    c.execute('SELECT transmitter_model FROM results WHERE transmitter_id = ?', (phone_id,))
    temp = c.fetchall()

    model = temp[0][0]

    conn.close()
    return model


def get_attenuations(filename, compensation=MODEL_RX_TX_COMPENSATION):
    '''
    Get a set of attenuations, compensated with the supplied model.
    Returns an array of [(attenuation, ground truth distance)] tuples
    '''
    results = []

    conn = sqlite3.connect(filename)

    c = conn.cursor()
    c.execute('SELECT rssi, tx_power, receiver_model, transmitter_model, ground_truth_distance FROM results')
    temp = c.fetchall()

    for i in range(0, len(temp)):
        rssi = temp[i][0]

        phonetx = temp[i][1]
        # Check if data was recorded with TX_POWER_ULTRA_LOW, adjust to GAEN
        # ULTRA_LOW = -21, LOW = -15, must adjust attenuation by 6
        # This allows us to use the calibration values in the table uniformly
        adjust = 0
        if phonetx == -21 or phonetx == -20:
            adjust = 6

        # Extract txpower and rxadjust from compensation table
        txpower = compensation[temp[i][2]][1]
        rxadjust = compensation[temp[i][3]][0]

        # NOTE: before using the updated GAEN calibration data, we used an
        #       approximation of the calibration for all Samsung devices which
        #       resulted in a txpower of -24 and an adjustment of -3. Together
        #       with the adjustment due to TX_POWER_ULTRA_LOW, the old
        #       attenuation calculation was:
        #           attenuation = -24 - (rssi + 3)
        attenuation = txpower - (rssi + adjust + rxadjust)

        gtd = temp[i][4]
        if gtd != None:
            results.append((attenuation, gtd))

    conn.close()

    return results

def get_attenuations_en(filename, gtd='avg', att='avg'):
    '''
    This function parses a v1.6 EN JSON file and returns a set of observations,
    compatible with the get_attenuations function so that it can be used for
    plotting and statistics
    gtd: either 'avg' or 'min' ground truth distance measured over the interval
    att: either 'avg' or 'min' attenuation measured over the interval
    Returns an array of [(attenuation, ground truth distance)] tuples
    '''

    results = []
    exposure_windows = json.load(open(filename, 'rb'))
    for _, exposure_window in exposure_windows.items():
        for _, scan_window in exposure_window.items():
            for _, rx in scan_window.items():
                for _, tx in rx.items():
                    if tx[gtd+'_gtd'] != None:
                        results.append((tx[att+'_att'], tx[gtd+'_gtd']))

    return results

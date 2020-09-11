#!/usr/bin/python3
"""
Generate calibration data from our calibration tests.
"""

import statistics

from figures import *
from measurements import *

def get_median(filename, receiver, transmitter):
    rx = statistics.median(get_measurements(filename, receiver, transmitter))
    tx = statistics.median(get_measurements(filename, transmitter, receiver))
    return (rx, tx)

if __name__ == "__main__":

    # iPhone11
    exp25 = [
        (110, 103, './exp25-calibration-iphone-to-android-anechoic/scenario01-110-103.sqlite'),
        (110, 2, './exp25-calibration-iphone-to-android-anechoic/scenario02-110-02.sqlite'),
        (110, 3, './exp25-calibration-iphone-to-android-anechoic/scenario03-110-03.sqlite'),
        (110, 6, './exp25-calibration-iphone-to-android-anechoic/scenario04-110-06.sqlite'),
        (110, 8, './exp25-calibration-iphone-to-android-anechoic/scenario05-110-08.sqlite'),
        (110, 10, './exp25-calibration-iphone-to-android-anechoic/scenario06-110-10.sqlite'),
        (110, 18, './exp25-calibration-iphone-to-android-anechoic/scenario07-110-18.sqlite'),
    ]

    # iPhone 11
    exp27 = [
        (10, 1, './exp27-calibration-iphone-to-iphone-anechoic/scenario04-10-01.sqlite'),
        (10, 2, './exp27-calibration-iphone-to-iphone-anechoic/scenario03-10-02.sqlite'),
        (10, 6, './exp27-calibration-iphone-to-iphone-anechoic/scenario02-10-06.sqlite'),
        (10, 8, './exp27-calibration-iphone-to-iphone-anechoic/scenario01-10-08.sqlite'),
    ]

    # Pixel 4
    exp28 = [
        (23, 2, './exp28-calibration-pixel4-to-android-anechoic/scenario06-23-02.sqlite'),
        (23, 6, './exp28-calibration-pixel4-to-android-anechoic/scenario05-23-06.sqlite'),
        (23, 8, './exp28-calibration-pixel4-to-android-anechoic/scenario04-23-08.sqlite'),
        (23, 10, './exp28-calibration-pixel4-to-android-anechoic/scenario03-23-10.sqlite'),
        (23, 18, './exp28-calibration-pixel4-to-android-anechoic/scenario02-23-18.sqlite'),
        (23, 24, './exp28-calibration-pixel4-to-android-anechoic/scenario01-23-24.sqlite'),
    ]

    exp29 = [
        (23, 1, './exp29-calibration-pixel4-anechoic/scenario03-23-01.sqlite'),
        (23, 2, './exp29-calibration-pixel4-anechoic/scenario04-23-02.sqlite'),
        (23, 3, './exp29-calibration-pixel4-anechoic/scenario02-23-03.sqlite'),
        (23, 6, './exp29-calibration-pixel4-anechoic/scenario05-23-06.sqlite'),
        (23, 8, './exp29-calibration-pixel4-anechoic/scenario06-23-08.sqlite'),
        (23, 10, './exp29-calibration-pixel4-anechoic/scenario07-23-10.sqlite'),
        (23, 24, './exp29-calibration-pixel4-anechoic/scenario01-23-24.sqlite'),
    ]

    calibration = [
        (110, 103, './exp25-calibration-iphone-to-android-anechoic/scenario01-110-103.sqlite'),
        (23, 24, './exp28-calibration-pixel4-to-android-anechoic/scenario01-23-24.sqlite'),
        (23, 24, './exp29-calibration-pixel4-anechoic/scenario01-23-24.sqlite'),
    ]

    iphone11 = get_median(calibration[0][2], calibration[0][0], calibration[0][1])
    pixel4_1 = get_median(calibration[1][2], calibration[1][0], calibration[1][1])
    pixel4_2 = get_median(calibration[2][2], calibration[2][0], calibration[2][1])

    print('Baseline measurement for iPhone11 (should be ~equal): {} {}'.format(iphone11[0], iphone11[1]))
    print('Baseline measurement for Pixel 4 (should be ~equal): {} {}'.format(pixel4_1[0], pixel4_1[1]))
    print('Baseline measurement for Pixel 4 (should be ~equal): {} {}'.format(pixel4_2[0], pixel4_2[1]))
   
    box_data = []
    for (base, test, bench) in exp25:
        base_model = get_model(bench, base)
        phone = get_model(bench, test)
        res = get_measurements(bench, base, test)
        for rssi in res:
            box_data.append((rssi, phone+'-tx'))
        res = get_measurements(bench, test, base)
        for rssi in res:
            box_data.append((rssi, phone+'-rx'))
    boxplot(box_data, ylabel='RSSI [dB]', xlabel='Measured by ' + base_model, filename='./figures/exp25-calibration-boxplot.png')

    box_data = []
    for (base, test, bench) in exp27:
        base_model = get_model(bench, base)
        phone = get_model(bench, test)
        res = get_measurements(bench, base, test)
        for rssi in res:
            box_data.append((rssi, phone+'-tx'))
        res = get_measurements(bench, test, base)
        for rssi in res:
            box_data.append((rssi, phone+'-rx'))
    boxplot(box_data, ylabel='RSSI [dB]', xlabel='Measured by ' + base_model, filename='./figures/exp27-calibration-boxplot.png')

    box_data = []
    for (base, test, bench) in exp28:
        base_model = get_model(bench, base)
        phone = get_model(bench, test)
        res = get_measurements(bench, base, test)
        for rssi in res:
            box_data.append((rssi, phone+'-tx'))
        res = get_measurements(bench, test, base)
        for rssi in res:
            box_data.append((rssi, phone+'-rx'))
    boxplot(box_data, ylabel='RSSI [dB]', xlabel='Measured by ' + base_model, filename='./figures/exp28-calibration-boxplot.png')

    box_data = []
    for (base, test, bench) in exp29:
        base_model = get_model(bench, base)
        phone = get_model(bench, test)
        res = get_measurements(bench, base, test)
        for rssi in res:
            box_data.append((rssi, phone+'-tx'))
        res = get_measurements(bench, test, base)
        for rssi in res:
            box_data.append((rssi, phone+'-rx'))
    boxplot(box_data, ylabel='RSSI [dB]', xlabel='Measured by ' + base_model, filename='./figures/exp29-calibration-boxplot.png')

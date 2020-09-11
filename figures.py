#!/usr/bin/python3

"""
Helper functions to plot different figures and tables from the standardized
measurements in the sqlite files.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

def heatmap(data, title="Distance vs. Attenuation", filename=""):
    npdata = np.asarray(data)
    filtered_data = npdata[(npdata[:,1] != -1)] # filter all bad distances
    filtered_data = npdata[(npdata[:,1] != None)] # filter all bad distances
    if len(filtered_data) == 0:
        print("No data for {} left!".format(filename))
        return
    #filtered_data = data
    heatmapBins=31

    plt.figure(figsize=(14,10))
    plt.hist2d(filtered_data[:,0], filtered_data[:,1], bins=heatmapBins, normed=True, cmap='YlOrRd', alpha=1.0, norm=mpl.colors.LogNorm())
    #plt.scatter(rssiVsDistanceNonB[:,0], rssiVsDistanceNonB[:,1], s=0.2, color="black")
    plt.ylim(0, np.max(filtered_data[:,1]))
    plt.title(title)
    plt.grid(True)
    plt.colorbar()
    plt.ylabel("Distance [m]")
    plt.xlabel("Attenuation [dB]")
    if filename == "":
        plt.show()
    else:
        plt.savefig(filename)

def boxplot(data, title="Phones at 1m distance vs. receiving (r)/sending (s) RSSI", ylabel="Attenuation [dB]", xlabel="", filename=""):
    buckets = {}
    for (att, phone) in data:
        if not phone in buckets:
            buckets[phone] = [att]
        else:
            buckets[phone].append(att)

    boxdata = []
    labels = []
    for key in sorted(buckets):
        if key == -1:
            continue
        boxdata.append(buckets[key])
        labels.append('{}'.format(key))
        #print(key)

    fig = plt.figure(figsize=(35,10))
    ax = fig.add_subplot(111)
    #plt.hist2d(filtered_data[:,0], filtered_data[:,1], bins=heatmapBins, normed=True, cmap='YlOrRd', alpha=1.0, norm=mpl.colors.LogNorm())
    ax.boxplot(boxdata)
    ax.set_xticklabels(labels)
    #plt.scatter(filtered_data[:,0], filtered_data[:,1], s=0.2, color="black")
    #plt.ylim(0, 120)
    plt.title(title)
    plt.grid(True)
    #plt.colorbar()
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    if filename == "":
        plt.show()
    else:
        plt.savefig(filename)
    plt.close()


def precision_recall(data, start, end, dists=[1.5, 2.0, 3.0], title="Precision/recall figure based on single-value classification", filename=""):
    plt.figure()

    for dist_thr in dists:

        att_vec = np.array([x[0] for x in data])
        dist_vec = np.array([x[1] for x in data])

        n_att_thr = 21
        # n_att_thr = 51
        att_thr_vec = np.linspace(start, end, n_att_thr)
        print(att_thr_vec)
        nfp_arr = np.array([])
        ntp_arr = np.array([])
        num_relevant = sum(dist_vec <= dist_thr)
        print(str(num_relevant) + " relevant elements, out of " + str(len(dist_vec)))
        # Classification based on single readings
        for att_thr in att_thr_vec:
            # Distances of attenuation values that trigger
            dist_trigg = dist_vec[att_vec <= att_thr]
            nfp_arr = np.append(nfp_arr, sum(dist_trigg > dist_thr))
            ntp_arr = np.append(ntp_arr, sum(dist_trigg <= dist_thr))

        prec_vec = ntp_arr / (nfp_arr + ntp_arr)
        rec_vec = ntp_arr / num_relevant

        plt.plot(prec_vec, rec_vec, label=str(dist_thr).replace('.', '_') + 'm')
        plt.grid(True)
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        att_i = 0
        for att in att_thr_vec:
            if prec_vec[att_i] < 0.95 and rec_vec[att_i] < 0.98:
                plt.text(prec_vec[att_i], rec_vec[att_i], str(att_thr_vec[att_i]))
            att_i += 1

    plt.xlabel('Precision')
    plt.ylabel('Recall')
    plt.title(title)
    plt.legend(loc='lower left')

    if filename == "":
        plt.show()
    else:
        plt.savefig(filename)
    plt.close()

def precision_recall_table(data, start, end, dists=[1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]):
    result = {}
    for att, gtd in data:
        if not gtd in result:
            result[gtd] = []
        result[gtd].append(att)

    print('att ', end='')
    for dist in dists:
        print('{:.1f}m        '.format(dist), end='')
    print('\n     ', end='')
    for _ in range(len(dists)):
        print('p     r     ', end='')
    print()

    for att in range(start, end):
        print('{} '.format(att), end='')

        for dist in dists:
            tp = 0 # correctly detected
            fp = 0 # incorrectly detected (trigger but not in range)
            fn = 0 # not detected (in range but not triggered)
            for gtd in sorted(result):
                for matt in result[gtd]:
                    if gtd <= dist and matt <= att:
                        tp += 1
                    if gtd <= dist and matt > att:
                        fn += 1
                    if gtd >= dist and matt <= att:
                        fp += 1
            prec = tp / (tp + fp)
            rec = tp / (tp + fn)
            print('{:.3f} {:.3f} '.format(prec, rec), end='')
        print()

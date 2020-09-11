# Failure to rotate RPI and MAC addresses

Concerns have been raised about Android devices not rotating (changing) the RPI
and MAC addresses simultaneously, thereby permitting an attacker to link RPIs
from a phone. Out of an abundance of caution, we examined the logs from our
experiments to see if we could detect this issue.  We found a small number (38
of 160,556) of instances in which the RPI remained fixed when the MAC rotated.
While incorrect, this fault only raises linkability concerns for the interval
until the RPI next changes (the total lifetime of these 38 RPIs was between 5-17
minutes).  We also found one model, Samsung Galaxy S10, that did not rotate its
MAC in some experiments.  This is a more serious concern, but it appears to be a
device-specific failure.


## Press statement from Google, Sept 09, 2020

We reached out to Google regarding issues with RPI rotation.
In response to our report and the "little thumb" attack, Google published a
statement on September 9, 2020:

> We are aware of a scenario that could potentially impact some device models
> and we are working on a mitigation that will be available soon. Our 
> investigation has determined that an attacker would need to follow a single 
> user around, or have an extensive network of Bluetooth scanners across a 
> wide geography, capable of constantly observing the device throughout the 
> day to execute this attack.


## Our experiments

Experiment 05 contains a total of 139,837 samples based on our pre-GAEN
protocol. This data was adjusted to GAEN levels and then calibrated using the
calibration data provided by Google.

Experiment 34 contains a total of 20,719 samples based on the GAEN protocol.
This data is calibrated using the calibration data provided by Google.

For details on the different experiments, please check out the top folders
describing the measured scenarios and setups.


## Linkability of RPI and MAC addresses

When RPI and MAC are not updated simultaneously, either the RPI or MAC can be
linked across changes of the MAC or RPI respectively. In general, the MAC
address should change when the RPI changes. We analyzed  data in experiments
25, 28, 29, 34 for two patterns:

* RPI remains the same across a MAC address rotation (i.e., the BT address
  changes but the RPI remains constant).
* MAC remains the same across a RPI rotation (i.e., the RPI changes while the
  BT address remains constant).

RPIs that can be linked across MAC address rotations pose a privacy violation.
So long as the MAC address changes with each RPI rotation, even if the RPI does
not change when the MAC address changes, a user can only be tracked for the
duration that the RPI is valid (as anticipated by the GAEN/DP-3T protocol).

In analyzing our data, we discovered 38 violations of the first kind (the
RPI remained constant across an MAC address rotation). None of these violations
was followed by an MAC address violation. So, the duration of the
linkability is limited to the validity of the underlying RPI. Our dataset
records the following validity periods for these 38 RPI violations:

```
Found RPI validity of 13:06 min.
Found RPI validity of 17:46 min.
Found RPI validity of 15:52 min.
Found RPI validity of 09:04 min.
Found RPI validity of 15:25 min.
Found RPI validity of 15:22 min.
Found RPI validity of 11:06 min.
Found RPI validity of 10:34 min.
Found RPI validity of 13:17 min.
Found RPI validity of 15:16 min.
Found RPI validity of 12:33 min.
Found RPI validity of 12:52 min.
Found RPI validity of 13:36 min.
Found RPI validity of 13:03 min.
Found RPI validity of 12:28 min.
Found RPI validity of 12:05 min.
Found RPI validity of 11:45 min.
Found RPI validity of 12:15 min.
Found RPI validity of 13:15 min.
Found RPI validity of 11:56 min.
Found RPI validity of 11:52 min.
Found RPI validity of 13:28 min.
Found RPI validity of 10:41 min.
Found RPI validity of 11:05 min.
Found RPI validity of 12:17 min.
Found RPI validity of 11:45 min.
Found RPI validity of 12:52 min.
Found RPI validity of 12:14 min.
Found RPI validity of 12:20 min.
Found RPI validity of 13:03 min.
Found RPI validity of 13:12 min.
Found RPI validity of 12:58 min.
Found RPI validity of 12:07 min.
Found RPI validity of 12:31 min.
Found RPI validity of 13:26 min.
Found RPI validity of 12:02 min.
Found RPI validity of 05:15 min.
Found RPI validity of 12:29 min.
```

This means that, except for the outlier of 17:45 min, the windows of
vulnerability were under 15 min. The GAEN API specifies an RPI validity of
below 20 minutes, all observed RPIs were valid for less than 20 minutes.

> A random ID derived from the device's Temporary Exposure Key. The RPI is
> generated on the device and a new RPI is generated every 10-20 minutes.

See [EN API](https://developers.google.com/android/exposure-notifications/exposure-notifications-api)
for more details.

One issue that we discovered in our dataset is a device model that did not
rotate its MAC address. This enables an outside entity to track users without
having to link individual packets. We have reported this issue and Google is
investigating it. The device in our dataset that exhibited this bug is the
Samsung Galaxy S10, model `SM-G973F`, build number
`QP1A.190711.020.G973FXXS7CTG1`.

The two Samsung Galaxy S10 devices used, in experiment 34, advertised with
unchanged MAC addresses for the following durations:

```
Found BTaddr validity of 3:34:58 hour
Found BTaddr validity of 3:39:17 hour
```

## Threats to validity

After each experiment we dumped the raw packet logs from all the devices. To
recover all information about each device (e.g., what RPI was being sent from
what address at what time for each device), we analyzed all commands to set
advertisement information from the Bluetooth packet log. To check for
violations, we searched for received advertisement data across all devices
involved in the experiment.

Due to the implementation of GAEN (in addition to physical limitations), the
devices will not capture all advertised data but only a subset of the beacons.
We placed a limited amount of BLE sniffers around the scene, they also only had
a limited view of the interactions due to recording limitations. Similarly, a
device may be outside the receiving distance for *all* listening devices or
advertisements may be lost due to collision or obstruction.  This means that
we may not catch all violations because none of our devices was listening at a
given time or not in range.

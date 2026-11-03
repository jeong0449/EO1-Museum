# EO1 Museum --- Wireless ADB Setup and Troubleshooting

**Date:** 2026-11-03\
**Project:** EO1 Museum\
**Target device:** Electric Objects EO1\
**Android:** 4.4.2 KitKat\
**Development unit USB serial:** `115343222`

------------------------------------------------------------------------

## 1. Why Wireless ADB Is Useful on the EO1

The EO1 has only one micro-USB port. During development this creates a
practical conflict:

``` text
USB connected to PC
    -> ADB development

USB used as OTG host
    -> mouse / keyboard / other USB device
```

Wireless ADB solves this problem by moving the ADB connection to Wi-Fi,
leaving the micro-USB port available for OTG devices.

For ordinary development, USB ADB is still the simplest and most
reliable method. Wireless ADB is especially useful when the USB port
must simultaneously be used in OTG host mode.

------------------------------------------------------------------------

## 2. Basic Wireless ADB Setup

Wireless ADB on this EO1 is enabled from an existing USB ADB connection.

First connect the EO1 to the PC by USB and check the device:

``` powershell
cd C:\platform-tools
.\adb.exe devices
```

The EO1 development unit appears as:

``` text
115343222    device
```

If several ADB targets are present, always specify the EO1 explicitly
with `-s`.

Enable ADB over TCP port 5555:

``` powershell
.\adb.exe -s 115343222 tcpip 5555
```

Expected response:

``` text
restarting in TCP mode port: 5555
```

The USB cable can then be disconnected if necessary.

Find the current EO1 Wi-Fi address and connect to it. For example, the
address used during the latest development session was:

``` powershell
.\adb.exe connect 192.168.1.104:5555
```

Check the result:

``` powershell
.\adb.exe devices
```

A successful connection should contain an entry similar to:

``` text
192.168.1.104:5555    device
```

From this point onward, target the wireless device explicitly:

``` powershell
.\adb.exe -s 192.168.1.104:5555 shell
```

or:

``` powershell
.\adb.exe -s 192.168.1.104:5555 install -r app-debug.apk
```

The IP address is not permanent. Earlier sessions used different
addresses, so the current EO1 address must be used rather than copying
an old command blindly.

------------------------------------------------------------------------

## 3. Wireless ADB Does Not Survive Reboot

An important characteristic of the current EO1 setup is that TCP ADB
mode does not persist across a reboot.

The following sequence:

``` text
USB ADB
    ↓
adb tcpip 5555
    ↓
Wireless ADB
```

must therefore be repeated after the EO1 has rebooted.

If this command fails after a reboot:

``` powershell
.\adb.exe connect 192.168.1.104:5555
```

do not assume that the network is broken. The first thing to suspect is
that `adbd` is no longer listening on TCP port 5555.

Recovery:

``` powershell
.\adb.exe -s 115343222 tcpip 5555
.\adb.exe connect 192.168.1.104:5555
```

This requires temporarily reconnecting the EO1 to the PC by USB.

------------------------------------------------------------------------

## 4. Always Check `adb devices` First

A surprisingly large amount of confusion came from having more than one
ADB target or stale targets in the device list.

Before issuing an install, shell, push, or debugging command, check:

``` powershell
.\adb.exe devices
```

Possible output may contain several entries:

``` text
115343222                device
192.168.1.104:5555       device
emulator-5562            offline
```

The presence of an unrelated or stale `offline` target does not mean
that the EO1 itself is offline.

Avoid ambiguous commands such as:

``` powershell
.\adb.exe shell
```

Instead use the exact target:

``` powershell
.\adb.exe -s 115343222 shell
```

for USB, or:

``` powershell
.\adb.exe -s 192.168.1.104:5555 shell
```

for Wi-Fi.

This simple habit prevents many cases where ADB appears to be
"confused."

------------------------------------------------------------------------

## 5. Symptom: `adb connect` Fails After It Worked Before

A previously working wireless connection may fail later even though the
EO1 is still on Wi-Fi.

Check the following in order.

### Step 1 --- Verify the EO1 IP address

The EO1 address can change after reconnecting to Wi-Fi or after DHCP
assigns a new lease.

An old address such as:

``` text
192.168.1.105
```

must not be assumed to remain valid. During later development the EO1
was at:

``` text
192.168.1.104
```

Use the current address.

### Step 2 --- Check whether TCP ADB mode was lost

If the EO1 has rebooted, reconnect it by USB and run:

``` powershell
.\adb.exe -s 115343222 tcpip 5555
```

Then:

``` powershell
.\adb.exe connect 192.168.1.104:5555
```

### Step 3 --- Check the device list

``` powershell
.\adb.exe devices
```

Do not confuse a stale emulator or another `offline` entry with the EO1
connection.

------------------------------------------------------------------------

## 6. Symptom: USB ADB Shows `unauthorized`

During early EO1 development, USB ADB initially appeared as:

``` text
unauthorized
```

Android normally displays an RSA authorization dialog:

``` text
Allow USB debugging?

[ ] Always allow from this computer
[Cancel] [OK]
```

Accessing this dialog on the EO1 was inconvenient. The project therefore
used `ADBApprovalHelper`, an AccessibilityService helper that
automatically selects **Always allow from this computer** and confirms
**OK**.

Once the PC's ADB key has been authorized, the device should appear as:

``` text
115343222    device
```

This authorization issue is different from wireless TCP configuration.
Wireless ADB cannot be repaired until a usable ADB connection exists in
the first place.

------------------------------------------------------------------------

## 7. Symptom: EO1 Appears in `adb devices`, but Shell Does Not Respond

One of the more confusing situations encountered during development was
that the EO1 could still appear in the ADB device list while a shell
command failed to respond normally.

This was particularly troublesome while switching the single micro-USB
port between:

``` text
PC USB ADB
        ↕
OTG mouse / USB host mode
```

The displayed ADB state should therefore not be treated as proof that
the complete USB connection is healthy.

First try the explicit target:

``` powershell
.\adb.exe -s 115343222 shell
```

If the USB connection itself has become unstable, use the physical
recovery procedure described below.

------------------------------------------------------------------------

## 8. Symptom: Windows No Longer Sees the EO1 USB Device

A more severe failure occurred when repeated switching between USB ADB
and OTG left the Windows USB connection in a bad state.

In this case, restarting the ADB server alone is not sufficient because
the failure is below ADB: Windows itself has lost the USB device.

Recovery procedure:

``` text
1. Remove the OTG device.
2. Disconnect the USB cable from the EO1.
3. Wait briefly.
4. Reconnect only the PC USB cable.
5. Check `adb devices`.
```

If Windows still does not detect the EO1:

``` text
1. Disconnect everything from the EO1 micro-USB port.
2. Reboot the EO1 with the port empty.
3. Wait until Android has fully booted.
4. Connect only the PC USB cable.
5. Run `adb devices`.
```

Then, if wireless ADB is required again:

``` powershell
.\adb.exe -s 115343222 tcpip 5555
.\adb.exe connect 192.168.1.104:5555
```

The important lesson is:

> `adb kill-server` cannot repair a USB device that Windows itself no
> longer sees.

------------------------------------------------------------------------

## 9. Avoid Mixing USB and Wi-Fi Targets Accidentally

After TCP mode is enabled, the same physical EO1 can potentially be
represented by different ADB serials at different times:

``` text
USB
115343222

Wi-Fi
192.168.1.104:5555
```

Commands should therefore always identify which transport is intended.

Examples:

``` powershell
# USB
.\adb.exe -s 115343222 shell

# Wi-Fi
.\adb.exe -s 192.168.1.104:5555 shell
```

The same applies to APK installation:

``` powershell
.\adb.exe -s 192.168.1.104:5555 install -r "app-debug.apk"
```

and application launch:

``` powershell
.\adb.exe -s 192.168.1.104:5555 shell monkey -p com.dan.eo1 -c android.intent.category.LAUNCHER 1
```

Explicit targeting is preferable to trying to clean up every unrelated
ADB entry.

------------------------------------------------------------------------

## 10. Recommended Daily Workflow

For normal development:

``` text
EO1
  ↓ USB
PC
  ↓
adb -s 115343222 ...
```

Use USB ADB whenever the micro-USB port is not needed for another
purpose.

When an OTG mouse or other host-mode device is required:

``` text
1. Connect EO1 to PC by USB.
2. Confirm USB ADB.
3. Enable TCP mode.
4. Connect through Wi-Fi.
5. Confirm the wireless target.
6. Disconnect the PC USB cable.
7. Attach the OTG device.
8. Continue development through wireless ADB.
```

Commands:

``` powershell
cd C:\platform-tools

.\adb.exe devices

.\adb.exe -s 115343222 tcpip 5555

.\adb.exe connect 192.168.1.104:5555

.\adb.exe devices

.\adb.exe -s 192.168.1.104:5555 shell
```

------------------------------------------------------------------------

## 11. Quick Recovery Checklist

When wireless ADB suddenly stops working, use this order rather than
changing several things at once:

``` text
[1] adb devices
     |
     +-- Is 192.168.1.xxx:5555 shown as device?
     |
     no
     ↓
[2] Confirm the current EO1 IP address
     |
     ↓
[3] Did EO1 reboot?
     |
     yes
     ↓
[4] Reconnect USB
     |
     ↓
[5] adb -s 115343222 tcpip 5555
     |
     ↓
[6] adb connect <current-EO1-IP>:5555
     |
     ↓
[7] adb devices
```

If USB recovery itself fails:

``` text
Remove OTG
    ↓
Disconnect USB
    ↓
Reconnect PC USB only
    ↓
still missing?
    ↓
Reboot EO1 with USB port empty
    ↓
Reconnect PC USB after Android boots
```

------------------------------------------------------------------------

## 12. Lessons Learned

Wireless ADB on the EO1 is not difficult once its state model is
understood. Most of the earlier confusion came from mixing several
independent issues:

``` text
ADB authorization
        +
USB / OTG role switching
        +
multiple ADB targets
        +
changing Wi-Fi IP addresses
        +
non-persistent TCP mode
```

These problems can look similar from the command line but require
different remedies.

The most useful rules are:

1.  **Use USB ADB as the normal development path.**
2.  **Use wireless ADB when the EO1 micro-USB port is needed for OTG.**
3.  **After every reboot, assume TCP ADB must be enabled again.**
4.  **Always inspect `adb devices` before troubleshooting.**
5.  **Use `-s` with the exact EO1 serial or IP target.**
6.  **Do not confuse stale or offline emulator entries with the EO1.**
7.  **If Windows has lost the USB device, fix the physical USB state
    before debugging ADB.**
8.  **Treat the EO1 IP address as changeable unless it has been reserved
    separately.**

The key distinction is:

``` text
ADB problem
    -> inspect ADB state

Network problem
    -> inspect IP / TCP connection

USB enumeration problem
    -> recover the physical USB connection
```

Keeping these layers separate makes wireless ADB recovery much more
predictable.

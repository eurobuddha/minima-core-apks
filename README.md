# Minima Core APKs

A collection of native Android companion apps for the Minima Core node, which talk to the node on-device via the minimaapi broadcast-Intent IPC.

## Minima Faucet (v1.0)

Native Android port of the Faucet MiniDapp. Package `org.minimarex.faucet`. It gets the node address via the IPC `getaddress` command and requests free Minima from the eurobuddha faucet backend.

### Install

```
adb install -r minima-faucet-1.0.apk
```

Note: this APK is debug-key signed for sideloading (not the Play Store). The Minima Core node app must be installed, and the Faucet must be enabled in Minima Core → Apps.

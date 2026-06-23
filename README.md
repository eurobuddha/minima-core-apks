# Minima Core APKs

A collection of native Android companion apps for the Minima Core node, which talk to the node on-device via the minimaapi broadcast-Intent IPC.

## Minima Faucet (v1.0)

Native Android port of the Faucet MiniDapp. Package `org.minimarex.faucet`. It gets the node address via the IPC `getaddress` command and requests free Minima from the eurobuddha faucet backend.

### Install

```
adb install -r minima-faucet-1.0.apk
```

Note: this APK is debug-key signed for sideloading (not the Play Store). The Minima Core node app must be installed, and the Faucet must be enabled in Minima Core → Apps.

## Minima UTXO Wallet (v1.0)

Native Android port of the utxoWallet MiniDapp. Package `org.minimarex.utxo`. A tabbed wallet over the IPC:

- **Wallet** — every address (including zero-balance) with its UTXOs; single-token multi-select.
- **Balances** — per-token aggregates with icon graphics and full token data.
- **Receive** — node address + QR code.
- **Send** — spend selected coins (builds and posts a custom transaction).
- **Tools** — Split, Consolidate, and Distribute (spread across up to 56 of your addresses, auto-chained across up to 4 transactions).
- **History** — local record of posted transactions with explorer links.

Live updates via the node's NEWBLOCK / NEWBALANCE events.

### Install

```
adb install -r minima-utxo-wallet-1.0.apk
```

Note: debug-key signed for sideloading (not the Play Store). The Minima Core node app must be installed, and the UTXO Wallet must be enabled in Minima Core → Apps.

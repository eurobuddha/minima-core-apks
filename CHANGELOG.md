# Changelog

- 2026-06-24 · minima-utxo-wallet 0.1.6 — Wallet UX: Tools moved off a separate tab into a Tools dropdown on the Wallet page (Split/Consolidate/Distribute/Untrack); restored per-address COPY, tap-to-copy coinid, and collapsible address cards; Consolidate reworked (no selection = consolidate Minima 0x00; 2+ selected = merge exactly those); distribute progress shown on the wallet page
- 2026-06-24 · minima-utxo-wallet 0.1.5 — Reconciled parsers against the node's command JSON (coins/balance/checkaddress/scripts/block/txn-outputs all confirmed correct); honest Coin.confirmed (no phantom blkconfirmed field)
- 2026-06-24 · minima-utxo-wallet 0.1.4 — Review round 2: node checkaddress validation on send; form-agnostic change-coin match; Distribute reservation closes double-start window; bounded image LruCache + off-thread QR/icon decode; NodeApi cancels pending timeouts on destroy; release.sh fails closed when GitHub is unreachable
- 2026-06-24 · minima-utxo-wallet 0.1.3 — Code-review fixes: validate recipient address (no command injection); Distribute tracks exact change coinid + retries mid-chain failures (no stranded jobs); clamp amounts to token decimals; non-destructive history DB upgrades; debounced reloads; guard callbacks against destroyed activity
- 2026-06-23 · minima-faucet 0.1.1 — Native Faucet companion app (getaddress over IPC + faucet backend request)
- 2026-06-23 · minima-utxo-wallet 0.1.2 — Wallet tab: list addresses with coins first, empty addresses below (match the MiniDapp UX)
- 2026-06-23 · minima-utxo-wallet 0.1.1 — Multi-batch Distribute (spread across up to 56 addresses); native UTXO wallet (Wallet/Balances/Receive/Send/Tools/History) over the IPC

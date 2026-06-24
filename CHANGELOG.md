# Changelog

- 2026-06-24 · minima-utxo-wallet 0.1.3 — Code-review fixes: validate recipient address (no command injection); Distribute tracks exact change coinid + retries mid-chain failures (no stranded jobs); clamp amounts to token decimals; non-destructive history DB upgrades; debounced reloads; guard callbacks against destroyed activity
- 2026-06-23 · minima-faucet 0.1.1 — Native Faucet companion app (getaddress over IPC + faucet backend request)
- 2026-06-23 · minima-utxo-wallet 0.1.2 — Wallet tab: list addresses with coins first, empty addresses below (match the MiniDapp UX)
- 2026-06-23 · minima-utxo-wallet 0.1.1 — Multi-batch Distribute (spread across up to 56 addresses); native UTXO wallet (Wallet/Balances/Receive/Send/Tools/History) over the IPC

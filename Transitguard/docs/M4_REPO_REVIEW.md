# M4 review of the repository (what I found when comparing)

The existing 19 tests pass. Nothing in the repo covered events, risk, reports, calibration or documentation, so those
were added. Points the team should decide:

1. **Two log formats.** `simulator.py` and `data/` use `seq,epoch,t_air,t_pay,door,t_est,ttl_s,alert`. `logger.py`
   (CSVLogger) uses `seq,timestamp,t0_air_c,t1_pay_c,t2_out_c,lid,status`. Pick one standard. `log_tools.load_log`
   reads both, but for `lid` please confirm whether 1 means open.
2. **Sequence numbers** start at 0 in the simulator and at 1 in the CSVLogger. `check_sequence` handles both.
3. **The `alert` column is always 0** in the simulated logs, so no alert decision is stored. M4 computes it from
   `t_est` and `ttl_s`. Decide whether the alert logic lives in the simulator and firmware and is written to the log.
4. **`evaluate.py` measures label accuracy** (NORMAL / HIGH / LOW). The validation plan promises lead time, false
   alarms and missed alarms compared with simple methods. Those metrics are still missing.
5. **The simulator gives the estimator the true time constant** (`tau_model` defaults to `tau_pay`), which favours
   our method. Add runs with the model tau wrong by 30 percent.
6. **`estimator.time_to_limit` returns None** when not applicable. The firmware and any other Python code must treat
   that the same way (the logs leave `ttl_s` empty).
7. **No outside-temperature column** in the simulated logs, but the CSVLogger has `t2_out_c`. Add it to the standard if we keep the outside probe.
8. **`__pycache__` files are committed** and there is no `.gitignore`. Suggested `.gitignore`: `__pycache__/`, `*.pyc`, `.pytest_cache/`.
9. **README.md is empty.** `docs/M4_README.md` documents the M4 part. The team README still needs writing.
10. I did not review `logger.py` hashing or `sync_receiver.py` in depth.

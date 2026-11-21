# Changelog

## 0.1.0 -- 2026-11-21

- Initial release: seeded canary generator (4 formats x verbatim /
  spaced / reversed plantings, free-text facts as digits or digit
  words), six deterministic pipeline stages (ingest, extractive
  summarise, chunk, regex redact, dictionary translate, base64
  template mail), three detectors (oracle ground truth, audit
  detector, verbatim-grep baseline), stage x format survival matrix,
  redactor kill / false-claim grading, killing-stage attribution.
- Headline evaluation over 48 seeded documents (192 canaries) with
  shipped results in `results/`.
- Streamlit dashboard (survival matrix / canary explorer /
  evaluation), CLI demo + evaluate, reproduction guard.

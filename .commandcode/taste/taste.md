# Taste

## Configuration & tooling
- Prefers app configuration as a dotfile in the user's home directory (e.g., `~/.wurl`) rather than project-local config. Confidence: 0.9
- Prefers config files to be auto-created with sensible defaults on first load/run, not documented for manual creation. Confidence: 0.8
- Prefers centralizing hardcoded/duplicated values (theming, colors, formatting options, HTTP defaults like timeout/user-agent) into a single config so the code reads values from config instead of scattering literals. Confidence: 0.8

# OpenDroid Website

This directory contains the production source code for the OpenDroid marketing and documentation website.

## Architecture & Structure

- `index.html`: Main landing page with live interactive preview.
- `about.html`: Information about OpenDroid mission and architecture.
- `features.html`: Showcase of OpenDroid capabilities.
- `contributor.html`: Guide for open-source contributors and project setup.
- `privacy.html`: Data privacy principles and policy.
- `security.html`: Security baseline and vulnerability disclosure instructions.
- `support.html`: FAQ, support channels, and community links.
- `terms.html`: Terms of service.
- `css/style.css`: Unified styling system.
- `js/main.js` and `js/theme-init.js`: Dependency-free browser behavior for theme state, navigation, copy controls, video controls, and GitHub statistics.
- `assets/`: Website media and static assets.
- `build.sh`: Reproducible source-to-`dist/` build using the tools available on the runner.
- `tests/validate.py`: Dependency-free structural/link/asset/CSP/JSON-LD validator.

`website/dist/` is generated output. It is ignored by Git and must not be committed.

## Local Development

Build the production output:

```bash
bash website/build.sh
python3 website/tests/validate.py website
python3 website/tests/validate.py website/dist
```

Serve the generated output:

```bash
cd website/dist && python3 -m http.server 8080
```

Then open `http://localhost:8080` in a browser.

For syntax checks without third-party packages:

```bash
bash -n website/build.sh
node --check website/js/main.js
node --check website/js/theme-init.js
ruby -e 'require "yaml"; ARGV.each { |f| YAML.parse_file(f) }' .github/workflows/*.yml
```

## CI/CD Pipeline & Deployment

`.github/workflows/deploy.yml` validates website pull requests and pushes that affect the website. Validation includes workflow YAML parsing, shell and JavaScript syntax checks, HTML structure, local links and assets, CSP checks, JSON-LD parsing, a deliberate negative test, the production build, generated-output validation, and a check that `website/dist/` is not tracked.

Only a push to `main` proceeds to the deployment job. The validation job uses read-only repository contents; the deployment job receives `contents: write` only because it publishes `website/dist/` to the `gh-pages` branch.

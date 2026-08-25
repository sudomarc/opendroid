# OpenDroid Website

This directory contains the production source code for the official OpenDroid marketing and documentation website.

## Architecture & Structure

- `index.html`: Main landing page with live interactive preview.
- `about.html`: Information about OpenDroid mission and architecture.
- `features.html`: Deep-dive showcase of all autonomous Android capabilities.
- `contributor.html`: Guide for open-source contributors and project setup.
- `privacy.html`: Data privacy principles and policy.
- `security.html`: Security baseline and vulnerability disclosure instructions.
- `support.html`: FAQ, support channels, and community links.
- `terms.html`: Terms of service.
- `css/style.css`: Unified styling system adhering to dark-first aesthetic rules.
- `js/main.js` & `js/theme-init.js`: Modular, dependency-free vanilla JS handling theme state, mobile menus, copy buttons, and fallback APIs.
- `build.sh`: Production build script minifying CSS & JS into `website/dist/`.

## Local Development

To run the website locally for testing and verification:

1. **Build `dist/` artifacts:**
   ```bash
   bash website/build.sh
   ```

2. **Serve `dist/` locally:**
   ```bash
   cd website/dist && python3 -m http.server 8080
   ```
   Open `http://localhost:8080` in your browser.

## CI/CD Pipeline & Deployment

Automated build and validation checks run on every push to `main` via `.github/workflows/deploy.yml`. Upon successful validation, the contents of `website/dist/` are automatically deployed to GitHub Pages (`gh-pages` branch).

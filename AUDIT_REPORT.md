# RAPPORT D'AUDIT DU DÉPÔT GITHUB — OpenDroid

---

### 1. SÉCURITÉ
⚠️ Problèmes trouvés :
- [HAUTE] `app/build.gradle:29-32` — Condition de signature d'APK de release exigeant un fichier keystore local `opendroid-release.keystore` à la racine — vérification `git ls-files` : fichier heureusement non-tracké (`git ls-files opendroid-release.keystore` renvoie vide).
- [MOYENNE] `.github/workflows/deploy.yml:25` — Action tierce `peaceiris/actions-gh-pages@v4` épinglée par tag Majeur (`@v4`) et non par commit SHA complet — risque supply-chain si le tag distant est altéré.
- [MOYENNE] `.github/workflows/android-ci.yml:27,33,40,71,77,84,124,130,137,159,165,172` — Actions GitHub officielles (`actions/checkout@v4`, `actions/setup-java@v4`, `gradle/actions/setup-gradle@v4`, `actions/upload-artifact@v4`) épinglées par tag majeur (`@v4`) au lieu d'un SHA commit immutable.

✅ Ce qui est déjà bon :
- Aucun secret en clair (clés AWS, tokens GitHub, clés privées RSA) détecté dans les fichiers trackés ou l'historique récent de commits (`git log -p`).
- Les workflows CI (`.github/workflows/android-ci.yml`) appliquent des permissions explicites minimales (`permissions: contents: read`) et n'utilisent pas le déclencheur à haut risque `pull_request_target`.
- Aucune tentative d'injection de commande shell dans les workflows (pas d'interpolation direct du type `${{ github.event... }}` dans des blocs `run:`).
- Aucun fichier sensible (`.env`, `*.pem`, `id_rsa`, `credentials.json`) n'est présent dans l'index Git (`git ls-files`).

NON VÉRIFIABLE — API GitHub/CLI `gh` non disponible (`gh command not found`) :
- Protections de branche / Rulesets sur la branche par défaut `main` (`gh api repos/.../branches/main/protection` inaccessible).
- Option "Allow GitHub Actions to create and approve pull requests" (`gh api repos/.../actions/permissions` inaccessible).
- Analyse dynamique de secrets profonds via `gitleaks` ou `trufflehog` (outils CLI non installés).
- Scanner CVE natif Android/Gradle (outils `npm audit` / `pip-audit` / `cargo audit` inadaptés à la stack Gradle/Kotlin).

🔧 Action recommandée :
- [HAUTE] Épingler l'ensemble des GitHub Actions par leur SHA commit immutable dans `.github/workflows/*.yml`.
- [MOYENNE] Ajouter un scanner SAST/Secrets automatisé (ex. Gitleaks / TruffleHog) dans la CI GitHub Actions.

---

### 2. DÉPENDANCES
⚠️ Problèmes trouvés :
- [BASSE] `.github/dependabot.yml` — Absence totale de configuration Dependabot ou Renovate pour l'automatisation des mises à jour de dépendances Gradle et GitHub Actions.

✅ Ce qui est déjà bon :
- Le projet est publié sous licence open-source **Apache License 2.0** (fichier `LICENSE` à la racine).
- Dépendances du projet Android déclarées avec des versions explicites et verrouillées dans `build.gradle` et `app/build.gradle`.

NON VÉRIFIABLE — Absence d'outils CLI de scan de dépendances Android/Gradle (ex. `osv-scanner`, `dependency-check` Gradle plugin) :
- Analyse automatique des vulnérabilités CVE dans le graphe de dépendances Gradle.
- Analyse automatique du graphe de licences des dépendances transitives.

🔧 Action recommandée :
- [MOYENNE] Configurer `.github/dependabot.yml` pour surveiller les mises à jour de packages Gradle et GitHub Actions.
- [BASSE] Intégrer un plugin d'audit de dépendances (comme `OWASP dependency-check-gradle` ou `osv-scanner`) dans la CI.

---

### 3. QUALITÉ DE CODE
⚠️ Problèmes trouvés :
- [MOYENNE] `app/lint-baseline.xml:1-148` — Présence d'un fichier baseline Android Lint contenant des avertissements/erreurs préexistants masqués pour la CI (`./gradlew :app:lintDebug`).

✅ Ce qui est déjà bon :
- Intégration active d'Android Lint exécuté automatiquement à chaque PR/push dans `.github/workflows/android-ci.yml`.
- Aucun `TODO`, `FIXME` ou `HACK` présent dans le code source Kotlin de l'application (`app/src/main/`).

NON VÉRIFIABLE — Outils CLI non installés (`jscpd`, `lizard`, `radon`) :
- Taux de duplication exact du code Kotlin (`jscpd`).
- Mesure de complexité cyclomatique par fonction (`lizard`).

🔧 Action recommandée :
- [MOYENNE] Réduire progressivement les anomalies consignées dans `app/lint-baseline.xml` pour supprimer le fichier baseline.

---

### 4. TESTS & CI
⚠️ Problèmes trouvés :
- [MOYENNE] Couverture de code non mesurée — Aucun rapport de couverture (`coverage.xml`, `lcov.info` ou Jacoco) n'est généré ou suivi dans le dépôt.

✅ Ce qui est déjà bon :
- La suite CI (`.github/workflows/android-ci.yml`) est complète : exécution des tests unitaires (`testDebugUnitTest`), du linter Android (`lintDebug`), des tests d'instrumentation sous émulateur Android (API 26 et API 36) et de la compilation release sous R8 (`assembleRelease -PallowUnsignedRelease`).
- Absence de marqueurs de tests ignorés (`@Disabled`, `@Ignore`) dans les sources de tests.

NON VÉRIFIABLE — API GitHub/CLI `gh` non disponible (`gh run list` inaccessible) :
- Statut des derniers runs CI et historique d'échecs/flakiness des workflows sur GitHub Actions.

🔧 Action recommandée :
- [MOYENNE] Intégrer le plugin Jacoco pour mesurer et publier la couverture de code des tests unitaires en CI.

---

### 5. GIT HYGIENE
⚠️ Problèmes trouvés :
- [BASSE] Branches distantes non fusionnées non nettoyées :
  - `origin/palette-ux-redesign-10917510396055177139` (dernier commit : 2026-07-24)
  - `origin/style-update-landing-page-10043887497994927504` (dernier commit : 2026-08-10)

✅ Ce qui est déjà bon :
- Aucun fichier volumineux/binaire de plus de 5 Mo n'est suivi par Git (`find . -type f -size +5M`).
- Fichier `.gitignore` propre et bien configuré à la racine du dépôt et dans `website/`.

NON VÉRIFIABLE — Aucun outil disponible pour mesurer l'historique complet :
- Détection des commits directs vs Pull Requests (accès API GitHub requis).

🔧 Action recommandée :
- [BASSE] Examiner et supprimer les branches distantes inactives une fois leurs fonctionnalités validées ou abandonnées.

---

### 6. DOCUMENTATION
⚠️ Problèmes trouvés :
- [BASSE] Fichiers de gouvernance absents à la racine ou dans `.github/` :
  - `CHANGELOG.md` absent.
  - Fichier `CODEOWNERS` (`.github/CODEOWNERS`) absent.

✅ Ce qui est déjà bon :
- Documentation exhaustive et structurée : `README.md` complet à la racine, `docs/CONTRIBUTING.md`, `docs/SECURITY.md`, `docs/CODE_OF_CONDUCT.md`, `LICENSE` et `ROADMAP.md` présents.

NON VÉRIFIABLE — Environnement sans simulateur Android actif :
- Exécution réelle pas à pas des instructions de build/install sur terminal physique (instructions uniquement relues).

🔧 Action recommandée :
- [BASSE] Ajouter un fichier `.github/CODEOWNERS` et un `CHANGELOG.md` pour tracer les versions et les propriétaires de composants.

---

### 7. STRUCTURE & ARCHITECTURE
⚠️ Problèmes trouvés :
- Rien à signaler.

✅ Ce qui est déjà bon :
- Respect rigoureux des conventions d'architecture Android / Jetpack Compose / Dagger-Hilt (packages séparés `actions`, `core`, `data`, `di`, `ui`).

NON VÉRIFIABLE — Analyse statique d'architecture approfondie :
- Détection de couplage via outils d'analyse statique avancés (ex. Detekt / SonarQube non configurés).

🔧 Action recommandée :
- [BASSE] Ajouter un linter de code Kotlin spécialisé (`detekt` ou `ktlint`) au build Gradle.

---

### 8. PERFORMANCE
⚠️ Problèmes trouvés :
- Rien à signaler.

✅ Ce qui est déjà bon :
- Inclusion d'une étape de vérification de build Release avec R8/ProGuard (`assembleRelease -PallowUnsignedRelease`) dans `.github/workflows/android-ci.yml` pour garantir l'optimisation du bytecode et la réduction de taille.

NON VÉRIFIABLE — Absence de profilage dynamique en exécution réelle :
- Profilage mémoire, CPU et consommation batterie sur appareil Android physique.

🔧 Action recommandée :
- [BASSE] Suivre la taille de l'APK généré au fil des releases via un artefact CI.

---

### 9. INFRASTRUCTURE / CONTAINERS
⚠️ Problèmes trouvés :
- Non applicable — Aucun `Dockerfile`, `docker-compose.yml` ou fichier IaC (Terraform, Kubernetes) présent dans le dépôt.

✅ Ce qui est déjà bon :
- Rien à signaler.

NON VÉRIFIABLE — Non applicable.

🔧 Action recommandée :
- Aucune action requise.

---

--- MÉTHODOLOGIE ---
Commit analysé : 22c784924a986b31d4685aed87ec1b3e4932992a (Wed Aug 12 19:18:59 2026 +0000)
Outils réellement utilisés : git, npm, python3, java, gradle
Outils absents/non utilisés : gh, gitleaks, trufflehog, osv-scanner, depcheck, jscpd, lizard, radon, hadolint, trivy, grype
Couverture : 378/378 fichiers analysés en mode lecture seule
Mode : lecture-seule

---

### TOP 3
1. **Épingler les GitHub Actions par SHA commit** (`.github/workflows/*.yml`) → Évite les risques de sécurité supply-chain si un tag distant (`@v4`) est altéré → Remplacer les tags de version par les SHA de commit complets.
2. **Éliminer la baseline Android Lint** (`app/lint-baseline.xml`) → Garantit qu'aucun avertissement ou potentiel bug silencieux ne persiste masqué dans la CI → Résoudre les 148 lignes d'anomalies répertoriées dans la baseline.
3. **Configurer Dependabot** (`.github/dependabot.yml`) → Automatise la détection et la mise à jour des dépendances vulnérables ou obsolètes → Ajouter le fichier de configuration Dependabot.

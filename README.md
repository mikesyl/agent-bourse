# 📊 Agent Bourse IA — 100% Gratuit

Reçois chaque matin par email une analyse IA de 3 actions françaises
avec un potentiel de +10% à 3 mois, basée sur l'analyse technique,
les fondamentaux et l'actualité.

**Coût total : 0€** (dans les limites gratuites de chaque service)

---

## Ce que fait l'agent

Chaque matin en semaine à 8h :

1. Collecte les données de 20 actions du SBF 120 via Yahoo Finance
2. Calcule RSI, MACD, Bollinger Bands, moyennes mobiles, volumes
3. Récupère les actualités récentes via Google News RSS
4. Envoie tout ça à Claude (Anthropic API) pour analyse
5. Reçois un email HTML formaté avec les 3 meilleures opportunités

---

## Installation en 5 étapes (~25 minutes)

### Étape 1 — Forker ce dépôt GitHub

1. Crée un compte sur [github.com](https://github.com) si tu n'en as pas
2. Clique sur **Fork** en haut à droite de ce dépôt
3. Tu as maintenant ta propre copie du projet

### Étape 2 — Clé API Anthropic (gratuite)

1. Va sur [console.anthropic.com](https://console.anthropic.com)
2. Crée un compte gratuit
3. Va dans **API Keys** → **Create Key**
4. Copie la clé (commence par `sk-ant-...`)

> Le tier gratuit d'Anthropic offre suffisamment de crédits pour
> cet usage quotidien pendant plusieurs semaines/mois.

### Étape 3 — Mot de passe d'application Gmail

1. Va sur [myaccount.google.com/security](https://myaccount.google.com/security)
2. Active la **Validation en 2 étapes** si ce n'est pas fait
3. Cherche **"Mots de passe des applications"**
4. Clique **Créer** → nomme-le "Agent Bourse"
5. Google génère un code à **16 caractères** → garde-le

### Étape 4 — Configurer les secrets GitHub

Dans ton dépôt GitHub :
**Settings → Secrets and variables → Actions → New repository secret**

Ajoute ces 4 secrets :

| Nom | Valeur |
|-----|--------|
| `ANTHROPIC_API_KEY` | Ta clé Anthropic (sk-ant-...) |
| `GMAIL_USER` | ton.adresse@gmail.com |
| `GMAIL_APP_PASSWORD` | Le code 16 caractères Google |
| `EMAIL_TO` | L'adresse qui reçoit l'email (peut être la même) |

### Étape 5 — Tester manuellement

1. Dans ton dépôt GitHub, clique sur l'onglet **Actions**
2. Clique sur **Agent Bourse Quotidien**
3. Clique **Run workflow** → **Run workflow**
4. Attends ~2 minutes et vérifie ta boîte email !

---

## Structure du projet

```
agent-bourse/
├── agent.py          # Script principal — orchestre tout
├── technical.py      # Analyse technique (RSI, MACD, Bollinger...)
├── news.py           # Collecte actualités Google News RSS
├── email_sender.py   # Envoi email HTML via Gmail SMTP
├── requirements.txt  # Dépendances Python
└── .github/
    └── workflows/
        └── daily.yml # Automatisation GitHub Actions (8h lun-ven)
```

---

## Exemple d'email reçu

```
📊 Analyse du lundi 12 avril 2026

1️⃣ CAPGEMINI (CAP.PA) — Prix actuel : 148€
🎯 Objectif 3 mois : 168€ (+13.5%)
📈 Technique : RSI 38 | MACD ACHAT | Tendance HAUSSIER
✅ Catalyseur 1 : Contrats IA en forte accélération
✅ Catalyseur 2 : Résultats T1 attendus au-dessus des attentes
⚠️ Risque : Modéré — Stop-loss suggéré : 138€

2️⃣ THALES (HO.PA) — Prix actuel : 172€
🎯 Objectif 3 mois : 195€ (+13.4%)
...

⚠️ Pas un conseil financier. DYOR.
```

---

## Personnalisation

### Modifier l'heure d'envoi

Dans `.github/workflows/daily.yml`, change le cron :
```yaml
- cron: '0 6 * * 1-5'   # 8h en été (CEST)
- cron: '0 7 * * 1-5'   # 8h en hiver (CET)  ← défaut
```

### Modifier l'univers d'actions

Dans `technical.py`, modifie la liste `TICKERS_FR` avec
les tickers Yahoo Finance de ton choix (format `XXX.PA` pour Euronext Paris).

### Changer le modèle Claude

Dans `agent.py`, modifie la ligne :
```python
model="claude-opus-4-5",
```

---

## Dépannage

**L'email n'arrive pas** → Vérifie le dossier spam + les secrets GitHub

**Erreur "Authentication failed"** → Le mot de passe d'application Gmail
doit être créé depuis un compte avec la validation 2 étapes activée

**Erreur Anthropic** → Vérifie que ta clé API est valide et que
tu as du crédit disponible sur [console.anthropic.com](https://console.anthropic.com)

---

⚠️ **Avertissement** : Cet outil est fourni à titre éducatif.
Les analyses générées ne constituent pas des conseils en investissement.
Investir en bourse comporte des risques de perte en capital.

Mis à jour le 13/04/2026

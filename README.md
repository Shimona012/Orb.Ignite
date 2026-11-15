##  <span style="color: #CF5408;"> _Org.Ignite_ </span>
Org.Ignite uses NASA databases and technical reports about combustioin science and presents an SI powered dashboard which sumarrizes different experiments (Eg. FLEX, SoFIE, Sapphire, etc.). It ranks the impact and consequence of each type of hazard, provides a 3D flame model to predict the outputs in various conditions and gives a knowledge base about this domain. Presets are avalible to test against certain conditions and precautions are provided.

## Prerequisites

Make sure you have Python installed on your system (Python 3.8 or higher is recommended).

## Installation & Setup

1. **Clone the repository** (or download the project files):
   ```bash
   git clone https://github.com/Shimona012/Orb.Ignite
   cd Orb.Ignite
   ```

2. **Create a virtual environment (Optional, but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Spotify API Credentials (Optional, for Music Player):**
   1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and log in.
   2. Click **Create app**, enter an app name/description, and set a Redirect URI (e.g., `http://localhost:8501`).
   3. Open **Settings** to copy your **Client ID** and **Client Secret**.
   4. Add them to `.streamlit/secrets.toml`:
      ```toml
      SPOTIPY_CLIENT_ID = "your_client_id_here"
      SPOTIPY_CLIENT_SECRET = "your_client_secret_here"
      SPOTIPY_REDIRECT_URI = "http://localhost:8501"
      ```

5. **Configure Supabase Credentials (Optional, for Authentication & Admin Portal):**
   1. Go to the [Supabase Dashboard](https://supabase.com/dashboard) and create or select your project.
   2. Navigate to **Project Settings** > **API**.
   3. Copy your **Project URL** and the **anon / public** API key.
   4. Add them to `.streamlit/secrets.toml`:
      ```toml
      SUPABASE_URL = "your_supabase_project_url"
      SUPABASE_KEY = "your_supabase_anon_key"
      ```

6. **Configure SMTP Email Credentials (Optional, for Contact Form & Direct Dispatch):**
   1. Open your [Google Account](https://myaccount.google.com/) and go to **Security**.
   2. Verify that **2-Step Verification** is enabled.
   3. Navigate to [App Passwords](https://myaccount.google.com/apppasswords), enter an app name (e.g. `Orb.Ignite`), and click **Create**.
   4. Copy the 16-character generated password.
   5. Add them to `.streamlit/secrets.toml`:
      ```toml
      SMTP_EMAIL = "your-email@gmail.com"
      SMTP_PASSWORD = "your-16-char-app-password"
      CONTACT_RECEIVER_EMAIL = "team@orbignite.org" # Optional default
      ```
   > **Note:** The Contact Us form also includes a direct **Receiver Email (Send To)** input field, allowing messages to be dispatched dynamically to any investigator or team inbox.

7. **Configure Google Cloud & Gemini AI Credentials (Optional, for AI Flight Surgeon):**
   1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/) or Google Cloud Console.
   2. Retrieve your Google Cloud Project ID and desired deployment region (e.g. `us-central1`).
   3. Add them to `.streamlit/secrets.toml`:
      ```toml
      GEMINI_API_KEY = "your_google_gemini_api_key"
      GCP_PROJECT_ID = "your_gcp_project_id"
      GCP_REGION = "us-central1"
      ```

   #### Google Cloud APIs Used & System Justifications:
   * **Cloud Resource Manager API**: Programmatically manages project resource hierarchies and IAM permissions across services.
   * **Cloud Billing API & Budget Alerting (CRITICAL COST SAFETY)**:
     > **Create a Budget Immediately**: In Google Cloud Console, navigate to **Billing** > **Budgets & Alerts** and create a budget with spend thresholds (e.g. $10 / $25 or respective amounts in different currencies with email notifications) before deploying heavy jobs to prevent unexpected billing.
   * **Cloud Build API**: Automates containerization, continuous integration, and Docker packaging on repository updates.
   * **Artifact Registry API**: Stores, versions, and scans production container images for scalable deployment.
   * **Compute Engine API**: Provisions compute instances and GPU hardware for multi-dimensional CFD and chemical kinetics batch simulations.
   * **Cloud Storage API (GCS)**: Stores large raw NASA PSI flight archives, video telemetry stacks, and model weights.
   * **Cloud Logging API**: Centralized operational logging, error tracking, and audit trails.
   * **Secret Manager API**: Enterprise encryption and secure runtime access to API keys and production credentials.
   * **Cloud Deploy API**: Manages automated, staged release pipelines across development, staging, and production environments.
   * **Generative Language / Gemini API**: Powers citation-grounded literature Q&A, NTRS document synthesis, and scientific explanations in the AI Flight Surgeon.

   > **Zero-Cloud Fallback Architecture:** *Orb.Ignite does not strictly depend on any cloud provider or API to operate.* Every core module includes a complete offline fallback: local physical equations, local JSON databases, local audio playback, and local keyword search.

## Usage

Run the Streamlit application locally using:

```bash
streamlit run Pages/Dashboard.py
```

## Deployment

### 1. Docker
Build and run the containerized application locally:
```bash
docker build -t orb-ignite .
docker run -p 8080:8080 orb-ignite
```

### 2. Google Cloud Run (Production)
Deploy directly from repository source to Google Cloud Run:
```bash
gcloud run deploy orb-ignite \
  --source . \
  --region us-central1 \
  --project orbignite-514803 \
  --allow-unauthenticated
```
Custom domains can be mapped with:
```bash
gcloud beta run domain-mappings create --service orb-ignite --domain orbignite.earth --region us-central1
```

## Transparency & Super Intelligence (SI) Disclosure

In the spirit of open science, academic honesty, and transparent engineering, this project openly discloses where and how **Super Intelligence (SI) / AI assistance** was utilized during the development of *Orb.Ignite*. All SI-assisted modules were driven by human literature research, engineered with domain-specific microgravity physics, and cross-verified against official NASA Physical Sciences Informatics (PSI) test data and technical reports.

> **Human Oversight & Verification Note:** All SI usage occurred strictly under continuous human supervision with deep human oversight. Every line of generated logic, mathematical formulation, and model threshold was actively checked, verified, and adjusted/refined in multiple places by humans to ensure experimental correctness and safety fidelity.

### Detailed Breakdown of SI Usage by Component:

1. **Combustion Physics & Literature Compilation (`combustion_physics.py`)**
   - **Research Synthesis:** SI was utilized to structure, synthesize, and compile diverse, disparate data across NASA microgravity combustion experiments (FLEX, Saffire, SoFIE, ACME, BASS, SAME, SOFBALL) from human literature research into a unified mathematical and physical specification.
   - **Model Engineering & Dynamic Retraining:** SI assisted with the technicalities of the hybrid physics-ML feature representations, mathematical boundary checks, and automated retraining pipelines.

2. **Machine Learning Model Training & Analysis (`fire_predictor.py`, `train_fire_models.py`)**
   - **Training Pipelines & Dataset Curation:** SI was heavily utilized in architecting the multi-target XGBoost training pipelines, identifying optimal dataset splits, calibrating sample weights, and analyzing evaluation metrics (Macro-F1, Balanced Accuracy, and MAE against PSI-117 digitized experimental curves).
   - **Inference Integration:** Implementing the three-tier confidence classification and mapping human flight test parameters to ML model feature spaces.

3. **3D Flame Simulation & Geometry (`flame_lab.py`)**
   - **Morphology Field Calculations:** SI was used to scaffold and debug the 3D scalar intensity field equations, mock calculations, and buoyancy-stretch transforms (spherical in 0g vs. elongated teardrop in 1g) before calibrating with NASA FLEX-2 observation parameters.

4. **Mission Catalog & Data Exploration (`mission_catalog.py`)**
   - **Search & Filter Logic:** SI assisted in debugging multi-field search algorithms (by mission name, fuel category, and NTRS ID) and dataset filtering logic.
   - **Threat Hierarchy Funnel:** SI was used to construct the interactive Plotly funnel visualization depicting mission threat tiers across varying enclosure scales.

5. **Scientific Representation & Domain Knowledge Base (`KnowledgeBase.py`)**
   - **Scientific Language & Formatting:** SI was used to ensure rigorous, scientifically precise language, proper mathematical LaTeX notation (e.g. Spalding Transfer numbers, Damköhler numbers, Grashof/Rayleigh ratios), and clean formatting of technical definitions.

6. **UI Architecture, Atmosphere & Data Pipelines (`Dashboard.py`, `ambience.py`)**
   - **Streamlit Layout & Ingestion:** SI assisted in structuring the multi-page dashboard, responsive layout containers, and JSON/CSV data-ingestion routines.
   - **Dynamic Ambient Aurora:** SI was utilized to design the CSS radial-gradient drift animations that dynamically reflect ambient environment presets (ISS, Lunar Gateway, Mars Habitat, Earth Lab).

7. **External Service Integrations & Debugging (`contact_us.py`, `Music.py`)**
   - **Supabase & Persistence:** SI was used to implement and debug the Supabase client connection, local JSON failovers, and secure database storage.
   - **Spotify & Audio Integration:** SI was used to debug the Spotipy API integration, player widget styling, and offline NASA audio fallback handling.

*And last, SI was used to generate this SI section :)*

## Built With

* **Streamlit** - Web application framework
* **XGBoost** - Machine learning model
* **Pandas & NumPy** - Data manipulation and numerical operations

## WEBSITE : _[orbignite.earth](https://orbignite.earth)_


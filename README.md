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

Run the Streamlit application using the following command:

```bash
streamlit run Pages/Dashboard.py
```

## Built With

* **Streamlit** - Web application framework
* **XGBoost** - Machine learning model
* **Pandas & NumPy** - Data manipulation and numerical operations

## WEBSITE : _[orbignite.earth](https://orbignite.earth)_

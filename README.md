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

## Usage

Run the Streamlit application using the following command:

```bash
streamlit run Pages/Dashboard.py
```

## Built With

* **Streamlit** - Web application framework
* **XGBoost** - Machine learning model
* **Pandas & NumPy** - Data manipulation and numerical operations

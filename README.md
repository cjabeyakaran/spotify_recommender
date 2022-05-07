# ESE 527 Project
Team Abeyakaran-Menon
Spotify Recommender

### Usage
Create a virtual environment and install matplotlib,numpy, pandas, scikit-learn and spotipy on it. The file "userdata.py" generates user specific .csv files that are run in the Jupyter notebook. In order to use the functions in this file, one needs to create a dashboard on Spotify Developer and generate their own "Client ID" and "Client-Secret" API keys for the OAuth. These are then stored as environment variables in a config file for spotipy to use OAuth. Alternatively, the "data/data.csv" file contains non user specific data that can be partitioned and trained on, however it will take much longer.  

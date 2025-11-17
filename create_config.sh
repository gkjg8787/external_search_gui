mkdir search
curl -o search/settings.py https://raw.githubusercontent.com/gkjg8787/external_search/refs/heads/main/ex_search/settings.py
sed -i 's|"base_url": "http://nodriver:8090"|"base_url": "http://nodriver_api:8090"|g' search/settings.py

sed -i 's|"url": "http://localhost:8060/api/"|"url": "http://search:8060/api/"|g' ex_search_gui/settings.py

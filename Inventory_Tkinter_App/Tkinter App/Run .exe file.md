🧩 Step-by-Step Guide — Convert Your Tkinter App into a .exe File



🪟 1. Prerequisites



Make sure you have:



✅ Windows OS



✅ Python 3.12 or above installed



✅ Your project folder ready (e.g.):



Project IMS/

├── TKINTER\_APP\_FINAL\_VERSION\_inventory.py

├── inventory.json







⚙️ 2. Install PyInstaller



Open your terminal or command prompt (in the same folder as your .py file) and run:



pip install pyinstaller





🧱 3. Create the Executable



In the same folder where your TKINTER\_APP\_FINAL\_VERSION\_INVENTORY.py file exists, run:



pyinstaller --onefile --windowed --icon=app.ico TKINTER\_APP\_FINAL\_VERSION\_INVENTORY.py





Explanation:



--onefile → bundles everything into one single .exe



--windowed → hides the terminal window when running GUI



--icon=app.ico → optional; use any .ico image as your app icon

(You can skip this part if you don’t have an icon yet)





📁 4. Locate Your Executable



After a few minutes, PyInstaller will finish building.



You’ll now find your .exe file in:



**Project IMS/dist/TKINTER\_APP\_FINAL\_VERSION\_INVENTORY.exe**





**⚠️ 5. Important Notes**



**Keep inventory.json in the same folder as the .exe file.**



**On first launch, if inventory.json doesn’t exist, the app will auto-create it.**



**The first .exe run might take 5–10 seconds (since it extracts resources internally).**






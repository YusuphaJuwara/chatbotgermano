
## Create Virtual Environment on Windows

Create Venv. For example:
---
---
```
C:\Users\yusup\AppData\Local\Microsoft\WindowsApps\python3.13.exe -m venv .venv
```
---
Activate it:
---
---
```
.\.venv\Scripts\activate
```
---
Deactivate it:
---
---
```
deactivate
```
---
Install a package:
---
---
```
pip install package_name
```
---
Install all packages in the requirement file:
---
---
```
pip install -r file_name.txt
```
---
## Download and Install MySQL

- Download from the official website at: https://dev.mysql.com/downloads/file/?id=541637
- Set it up ...
- After installation, you can verify with: `sc query MySQL80`

- Nice [article](https://dev.to/kodebae/how-to-remove-a-leaked-env-file-from-github-permanently-3lei) to remove wrongly pushed files to github

## Google sites, Analytics and Search Console

- How to connect your [website](https://sites.google.com/view/chatbot-germano/scenario?authuser=0) to [google analytics](https://analytics.google.com/analytics/web/provision/#/p487121650/reports/intelligenthome?params=_u..nav%3Dmaui&collectionId=user) and search console? [Watch this Youtube video](https://www.youtube.com/watch?v=QiPvlznkA7k) 
- Google Analytics 4 (GA4) Tutorial for Beginners [Youtube video](https://www.youtube.com/watch?v=S7r83NvINiM)


## Network Port
- If you get error relating to network issues (port), check which process is using the port and whether you want to kill it, where :8000 is the example port and 19368 is the process using it.
    - netstat -aon | findstr :8000
    - TaskKill /PID 19368 /F 

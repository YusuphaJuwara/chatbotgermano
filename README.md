
## Create Virtual Environment on Windows

Create Venv. For example:
```
C:\Users\yusup\AppData\Local\Microsoft\WindowsApps\python3.13.exe -m venv .venv
```

Activate it:
```
.\.venv\Scripts\activate
```

Deactivate it:
```
deactivate
```

Install a package:
```
pip install package_name
```

Install all packages in the requirement file:
```
pip install -r file_name.txt
```


## Download and Install MySQL

- Download from the official website at: https://dev.mysql.com/downloads/file/?id=541637
- Set it up ...
- After installation, you can verify with: `sc query MySQL80`

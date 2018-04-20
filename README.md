# pyodbc-sqlserver

Contains some simple helper classes for interacting with SQL Server. Leverages pyodbc and Microsoft's SQL Server driver.

To try it out via Docker, first copy `dockerfiles/apt.conf.sample` to `dockerfiles/apt.conf` and edit the proxy settings, then similarly copy `Dockerfile.sample.Dockerfile` to `Dockerfile` and edit proxy settings there.

```bash
docker build -t pyodbc-sqlserver . && docker run -it pyodbc-sqlserver
```

Interactively:

```bash
docker build -t pyodbc-sqlserver . && docker run -it pyodbc-sqlserver /bin/bash
```

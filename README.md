# spotbugs-to-codacy

A parser to upload manually generated Spotbugs reports to Codacy

## usage

The `requirements.txt` lists all Python libraries that should be installed before running the script:

```bash
pip3 install -r requirements.txt
python3 spotbugs-parser.py [-h] [--report-path REPORTPATH]
                          [--project-token PROJECTTOKEN]
                          [--commit-uuid COMMITUUID] [--basedir BASEDIR]
                          [--baseurl BASEURL]
```
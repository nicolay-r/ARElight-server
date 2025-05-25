# ARElight-server 0.25.1
![](https://img.shields.io/badge/Python-3.9-brightgreen.svg)


This project represent an accessible Web GUI for the
[ARElight](https://github.com/nicolay-r/ARElight/tree/v0.25.1) system, powered by [Flask](https://flask.palletsprojects.com/en/stable/).

<img width="1024" alt="interface" src="https://github.com/user-attachments/assets/552c78ae-5b49-4778-8070-10b913ebcf30" />

# Installation

You have to first install project dependencies: 
```bash
pip install -r dependencies.txt
```

# Usage 

```bash
python3 server.py
```

You may follow the UI page at `http://127.0.0.1:8000/`

## Data Layout
```
noutput/
├── description/
    └── ...         // graph descriptions in JSON.
├── force/
    └── ...         // force graphs in JSON.
├── radial/
    └── ...         // radial graphs in JSON.
└── index.html      // main HTML demo page. 
```
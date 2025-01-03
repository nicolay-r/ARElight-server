# ARElight-server 0.25.1
![](https://img.shields.io/badge/Python-3.9-brightgreen.svg)

This project represent an accessible version for the 
[ARElight](https://github.com/nicolay-r/ARElight/tree/v0.25.1) system.

## Usage

You have to first install 
[ARElight](https://github.com/nicolay-r/ARElight/tree/v0.25.1) 
to enable functionalities of the project: 
```bash
pip install git+https://github.com/nicolay-r/arelight@v0.25.1
```

Download `arelight-server` project and launch server:
```bash
python3 server.py
```

You may follow the UI page at `http://127.0.0.1:8000/`

<img width="1512" alt="interface" src="https://github.com/user-attachments/assets/552c78ae-5b49-4778-8070-10b913ebcf30" />

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

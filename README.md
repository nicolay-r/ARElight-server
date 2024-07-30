# ARElight-server
![](https://img.shields.io/badge/Python-3.9-brightgreen.svg)

This project represent an accessible version for the 
[ARElight](https://github.com/nicolay-r/ARElight/tree/v0.25.0) system.

## Usage

```python
python3 server.py
```

You may follow the UI page at `http://127.0.0.1:8000/`

![image](https://github.com/nicolay-r/ARElight/assets/14871187/341f3b51-d639-46b6-83fe-99b542b1751b)

## Layout of the files in output
```
output/
├── description/
    └── ...         // graph descriptions in JSON.
├── force/
    └── ...         // force graphs in JSON.
├── radial/
    └── ...         // radial graphs in JSON.
└── index.html      // main HTML demo page. 
```
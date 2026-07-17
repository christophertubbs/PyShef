# PyShef

Basic library to parse National Weather Service SHEF `.A`, `.B`, and `.E` data directly into pandas DataFrames.

## Usage

```python
from pyshef import parse_shef

data = """
.A ABCD 240717 Z DH1200/PPH 1.25/TAH 72
"""

df = parse_shef(data)
print(df)
```

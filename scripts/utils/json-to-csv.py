import pandas as pd
import sys

jsonFile = sys.argv[1]
csvFile = sys.argv[2]

print("Converting " + jsonFile + "to" + csvFile)

with open(jsonFile, encoding="utf-8") as inputFile:
  df = pd.read_json(inputFile)
  
df.to_csv(csvFile, encoding="utf-8",index=False)

print("done")

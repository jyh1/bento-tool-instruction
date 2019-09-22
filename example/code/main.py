import sys
import torch
from nltk.tokenize import word_tokenize

data = sys.argv[1]
result = sys.argv[2]
for line in open(data):
    print(word_tokenize(line))

print("GPU count: ", torch.cuda.device_count())
with open(result, 'w') as resH:
    resH.write("Done.")
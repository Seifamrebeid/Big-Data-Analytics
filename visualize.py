# Runs the real countingWords code and saves what happens at each step
# to visualize-data.js. Then open visualize.html in your browser.
# Run: python3 visualize.py

import json
import os
from queue import SimpleQueue

import countingWords as cw

folder = os.path.join(cw.HERE, "..", "datasets", "text-files")
paths = [os.path.join(folder, name) for name in sorted(os.listdir(folder))
         if name.startswith("book_") and name.endswith(".txt")]

files = []
from_mappers = []
for path in paths:
    pairs = cw.map_fn(path)

    # the real mapper, run here without a new process so we can keep its result
    queue = SimpleQueue()
    cw.mapper(path, queue)
    from_mappers.append(queue.get())

    with open(path) as f:
        text = f.read()
    files.append({
        "name": os.path.basename(path),
        "text": text,
        "pairs": [word for word, count in pairs],
        "totals": cw.combine(pairs),
    })

reducers = []
for reducer in range(cw.NUM_REDUCERS):
    rows = []
    for word, counts in cw.shuffle_and_sort(from_mappers, reducer):
        rows.append({"word": word, "values": counts, "total": sum(counts)})
    reducers.append(rows)

with open(os.path.join(cw.HERE, "visualize-data.js"), "w") as out:
    out.write("const DATA = " + json.dumps({"files": files, "reducers": reducers}) + ";\n")

print("saved visualize-data.js, now open visualize.html in your browser")

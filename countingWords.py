import os
import re
import time
from datetime import datetime
from multiprocessing import Process, Queue

NUM_REDUCERS = 2
HERE = os.path.dirname(os.path.abspath(__file__))


def now():
    return datetime.now().strftime("%H:%M:%S.%f")


# MAP: turn one file into (word, 1) pairs
def map_fn(path):
    with open(path) as f:
        text = f.read().lower()

    words = re.findall(r"[a-z0-9]+", text)  # letters and digits only
    pairs = []
    for word in words:
        pairs.append((word, 1))
    return pairs


# COMBINE: add up the 1s inside one file
def combine(pairs):
    totals = {}
    for word, count in pairs:
        if word in totals:
            totals[word] = totals[word] + count
        else:
            totals[word] = count
    return totals


# PARTITION: same word -> same reducer (not hash(), it changes per process)
def partition(word):
    # add up the letter codes, then % 2
    return sum(ord(letter) for letter in word) % NUM_REDUCERS


# MAPPER: runs in its own process, handles one file
def mapper(path, queue):
    start = now()
    timer = time.perf_counter()

    pairs = map_fn(path)
    totals = combine(pairs)

    # one list per reducer
    parts = []
    for _ in range(NUM_REDUCERS):
        parts.append([])

    for word, count in totals.items():
        reducer = partition(word)
        parts[reducer].append((word, count))

    taken = (time.perf_counter() - timer) * 1000
    name = os.path.basename(path)
    print(f"mapper pid={os.getpid()} read {name}  start {start}  end {now()}  took {taken:.3f} ms")
    queue.put(parts)


# SHUFFLE & SORT: gather my words from every mapper, group them, sort them
def shuffle_and_sort(from_mappers, reducer):
    groups = {}  # word -> its subtotals, like "students" -> [1, 1, 1]
    for parts in from_mappers:
        for word, count in parts[reducer]:
            if word not in groups:
                groups[word] = []
            groups[word].append(count)
    return sorted(groups.items())


def run(files, output_dir):
    # start all the mappers together, one process per file
    t0 = time.time()
    queue = Queue()
    processes = [Process(target=mapper, args=(path, queue)) for path in files]
    
    for process in processes:
        process.start()

    # get every result, then wait for the processes to finish
    from_mappers = [queue.get() for _ in processes]
    
    for process in processes:
        process.join()
    print(f"all {len(files)} mappers finished after {time.time() - t0:.2f} s")

    # one output file per reducer
    os.makedirs(output_dir, exist_ok=True)
    for reducer in range(NUM_REDUCERS):
        file_name = f"PartReducer-{reducer + 1}.txt"
        with open(os.path.join(output_dir, file_name), "w") as out:
            for word, counts in shuffle_and_sort(from_mappers, reducer):
                total = sum(counts)
                out.write(f"{word}\t{total}\n")


if __name__ == "__main__":
    folder = os.path.join(HERE, "..", "datasets", "text-files")
    files = [os.path.join(folder, name) for name in sorted(os.listdir(folder))
             if name.startswith("book_") and name.endswith(".txt")]
    run(files, HERE)
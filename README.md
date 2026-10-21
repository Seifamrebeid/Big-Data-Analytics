# MapReduce Word Count

**Name:** Seifallah Amr Mohamed
**Student ID:** 231014746

This program counts how many times each word appears in a folder of text files.
The map, combine, partition, shuffle & sort and reduce code is all my own (Python, standard library only).

## Run

```
python3 countingWords.py
```

It reads `../datasets/text-files/book_*.txt` (5 files, each file is one split) and writes
`PartReducer-1.txt` and `PartReducer-2.txt` next to the code.

## How it works

1. **Map:** each file is turned into `(word, 1)` pairs.
2. **Combine:** inside each file the 1s are added up: `("big", 1)` and `("big", 1)` become `("big", 2)`.
3. **Partition:** every word is sent to reducer 0 or reducer 1.
4. **Shuffle & sort:** each reducer gathers its words from all the mappers, groups the subtotals by word and sorts the words.
5. **Reduce:** each reducer adds up the subtotals of each word and writes one output file.

### How the parallel mappers work

Every file gets its own process (`multiprocessing.Process`), so 5 files means 5 processes.
All of them are started first and only then waited for, so they run at the same time.
Each mapper sends its result back to the main program through a `Queue`.
The different `pid` numbers in the output show that they are separate processes.

### How partitioning sends words to reducers

`partition(word)` adds up the number codes of the letters in the word and takes the remainder when dividing by 2.
A result of 0 sends the word to reducer 0 (`PartReducer-1.txt`) and 1 sends it to reducer 1 (`PartReducer-2.txt`).
The same word always gives the same number, so all the subtotals of a word reach the same reducer, whichever file they came from.
(Python's `hash()` is not used, because it gives different answers in different processes.)

Example: `students` is in 3 files, once in each. The mappers produce `("students", 1)` three times, partition sends them all to reducer 0,
and reducer 0 adds `[1, 1, 1]` to get `students 3`.

## Output

Console output when running the program:

```
mapper pid=54886 read book_05.txt  start 21:27:33.715423  end 21:27:33.715693  took 0.255 ms
mapper pid=54885 read book_04.txt  start 21:27:33.715423  end 21:27:33.715695  took 0.258 ms
mapper pid=54882 read book_01.txt  start 21:27:33.718229  end 21:27:33.718491  took 0.249 ms
mapper pid=54884 read book_03.txt  start 21:27:33.721119  end 21:27:33.721388  took 0.255 ms
mapper pid=54883 read book_02.txt  start 21:27:33.721119  end 21:27:33.721387  took 0.254 ms
all 5 mappers finished after 0.07 s
```

Output files (each line is `word`, a tab, then the count). Each file has 91 words, 182 different words in total, and every word is in only one of the two files:

| PartReducer-1.txt (reducer 0) | PartReducer-2.txt (reducer 1) |
|---|---|
| `big 1`, `can 5`, `data 2`, `students 3` | `and 12`, `words 4` |

## Testing

I ran it on the 5 files `book_01.txt` to `book_05.txt`. They contain different words, and some words appear in several files.
The counts (235 words in total) are the same as an independent count made with a separate script.

Note: the file `expected_word_count.txt` in the dataset folder does not match the text of the books
(for example it lists `reduce` twice and gives `to` as 4, but `to` appears once), so I did not use it.

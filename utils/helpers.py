from pathlib import Path


def save_result(text, filename="output/results.txt"):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")

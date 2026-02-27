from concurrent.futures import ProcessPoolExecutor, as_completed


class ParallelEngine:
    name = "parallel"

    def run(self, worker, tasks, max_workers=4):
        if not tasks:
            return []

        max_workers = max(1, int(max_workers))
        results = [None] * len(tasks)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(worker, task): index for index, task in enumerate(tasks)
            }
            for future in as_completed(future_map):
                index = future_map[future]
                try:
                    results[index] = future.result()
                except Exception as exc:
                    task = tasks[index]
                    number = task.get("number") if isinstance(task, dict) else None
                    results[index] = {
                        "ok": False,
                        "number": number,
                        "error": f"Parallel engine error: {exc}",
                    }

        return results

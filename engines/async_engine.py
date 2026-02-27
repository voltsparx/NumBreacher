import asyncio


class AsyncEngine:
    name = "async"

    async def _run_async(self, worker, tasks, max_workers):
        semaphore = asyncio.Semaphore(max(1, int(max_workers)))
        results = [None] * len(tasks)

        async def execute(index, task):
            async with semaphore:
                try:
                    results[index] = await asyncio.to_thread(worker, task)
                except Exception as exc:
                    number = task.get("number") if isinstance(task, dict) else None
                    results[index] = {
                        "ok": False,
                        "number": number,
                        "error": f"Async engine error: {exc}",
                    }

        await asyncio.gather(*(execute(i, task) for i, task in enumerate(tasks)))
        return results

    def run(self, worker, tasks, max_workers=8):
        if not tasks:
            return []

        return asyncio.run(self._run_async(worker, tasks, max_workers))

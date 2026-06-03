"""Simple thread-pool task queue for background downloads."""
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable
import time


@dataclass
class Task:
    id: int
    description: str
    state: str = "queued"  # queued | active | done | failed
    result: Any = None
    error: str = ""
    progress: int = 0
    progress_max: int = 0
    title: str = ""
    artist: str = ""
    img_url: str = ""
    current_item: str = ""
    music_id: str = ""
    music_type: str = ""
    _fn: Callable = None
    _kwargs: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "state": self.state,
            "result": str(self.result) if self.result else "",
            "error": self.error,
            "progress": self.progress,
            "progress_max": self.progress_max,
            "title": self.title,
            "artist": self.artist,
            "img_url": self.img_url,
            "current_item": self.current_item,
            "music_id": self.music_id,
            "music_type": self.music_type,
        }


class TaskQueue:
    def __init__(self, workers: int = 4):
        self._pool = ThreadPoolExecutor(max_workers=workers)
        self._tasks: list[Task] = []
        self._id_counter = 0
        self._lock = threading.Lock()
        self._current_task = threading.local()

    def enqueue(self, description: str, fn: Callable, title: str = "", artist: str = "", img_url: str = "", music_id: str = "", music_type: str = "", **kwargs) -> Task:
        with self._lock:
            self._id_counter += 1
            task = Task(
                id=self._id_counter,
                description=description,
                title=title,
                artist=artist,
                img_url=img_url,
                music_id=music_id,
                music_type=music_type,
                _fn=fn,
                _kwargs=kwargs
            )
            self._tasks.append(task)

        def run():
            self._current_task.task = task
            task.state = "active"
            try:
                task.result = fn(**kwargs)
                task.state = "done"
            except Exception as e:
                task.state = "failed"
                task.error = str(e)
                traceback.print_exc()

        self._pool.submit(run)
        return task

    def report_progress(self, current: int, total: int, current_item: str = ""):
        """Call from within a task function to update progress."""
        t = getattr(self._current_task, "task", None)
        if t:
            t.progress = current
            t.progress_max = total
            if current_item:
                t.current_item = current_item

    def update_metadata(self, title: str = "", artist: str = "", img_url: str = "", description: str = ""):
        """Update metadata of the currently running task."""
        t = getattr(self._current_task, "task", None)
        if t:
            if title:
                t.title = title
            if artist:
                t.artist = artist
            if img_url:
                t.img_url = img_url
            if description:
                t.description = description

    def clear_completed(self):
        """Remove completed or failed tasks from the list."""
        with self._lock:
            self._tasks = [t for t in self._tasks if t.state in ("queued", "active")]

    def retry_task(self, task_id: int) -> bool:
        """Re-enqueue a failed task."""
        with self._lock:
            task = next((t for t in self._tasks if t.id == task_id), None)
            if not task or task.state != "failed":
                return False
            task.state = "queued"
            task.error = ""
            task.progress = 0
            task.progress_max = 0
            task.current_item = "Retrying..."
            
            fn = task._fn
            kwargs = task._kwargs

        def run():
            self._current_task.task = task
            task.state = "active"
            try:
                task.result = fn(**kwargs)
                task.state = "done"
            except Exception as e:
                task.state = "failed"
                task.error = str(e)
                traceback.print_exc()

        self._pool.submit(run)
        return True

    def all_tasks(self) -> list[dict]:
        return [t.to_dict() for t in reversed(self._tasks)]

    def shutdown(self):
        self._pool.shutdown(wait=False)

"""Simple desktop To-Do application using Tkinter.

Features:
- Add, edit, delete tasks
- Mark task as done / not done
- Filter all/active/completed tasks
- Persist tasks to a local JSON file
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk


DATA_FILE = Path(__file__).with_name("todo_data.json")


@dataclass
class TodoItem:
    text: str
    done: bool = False


class TodoApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Todo App")
        self.geometry("560x540")
        self.minsize(500, 440)

        self.todos: list[TodoItem] = self._load_todos()
        self.filter_mode = tk.StringVar(value="all")

        self._create_widgets()
        self._bind_shortcuts()
        self._refresh_list()

    def _create_widgets(self) -> None:
        container = ttk.Frame(self, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(container, text="오늘 할 일", font=("Arial", 16, "bold"))
        title.pack(anchor="w", pady=(0, 10))

        input_row = ttk.Frame(container)
        input_row.pack(fill=tk.X, pady=(0, 8))

        self.task_entry = ttk.Entry(input_row)
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.task_entry.bind("<Return>", lambda _event: self.add_task())

        ttk.Button(input_row, text="추가", command=self.add_task).pack(side=tk.LEFT, padx=(8, 0))

        filter_row = ttk.Frame(container)
        filter_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(filter_row, text="보기:").pack(side=tk.LEFT)
        for key, label in (("all", "전체"), ("active", "진행중"), ("done", "완료")):
            ttk.Radiobutton(
                filter_row,
                text=label,
                value=key,
                variable=self.filter_mode,
                command=self._refresh_list,
            ).pack(side=tk.LEFT, padx=4)

        list_frame = ttk.Frame(container)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.todo_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.SINGLE,
            activestyle="none",
            font=("Arial", 12),
        )
        self.todo_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.todo_listbox.bind("<Double-Button-1>", lambda _event: self.toggle_task())

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.todo_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.todo_listbox.config(yscrollcommand=scrollbar.set)

        action_row = ttk.Frame(container)
        action_row.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(action_row, text="완료 토글", command=self.toggle_task).pack(side=tk.LEFT)
        ttk.Button(action_row, text="수정", command=self.edit_task).pack(side=tk.LEFT, padx=8)
        ttk.Button(action_row, text="삭제", command=self.delete_task).pack(side=tk.LEFT)
        ttk.Button(action_row, text="완료 항목 정리", command=self.clear_done).pack(side=tk.RIGHT)

        self.status_var = tk.StringVar(value="할 일을 입력해 주세요.")
        ttk.Label(container, textvariable=self.status_var).pack(anchor="w", pady=(8, 0))

        guide_text = "단축키: Enter(추가), Ctrl+D(완료 토글), Ctrl+E(수정), Delete(삭제), Ctrl+N(입력창 이동)"
        ttk.Label(container, text=guide_text, foreground="#666").pack(anchor="w", pady=(6, 0))

    def _bind_shortcuts(self) -> None:
        self.bind("<Delete>", lambda _event: self.delete_task())
        self.bind("<Control-d>", lambda _event: self.toggle_task())
        self.bind("<Control-e>", lambda _event: self.edit_task())
        self.bind("<Control-n>", lambda _event: self.task_entry.focus_set())

    def _filtered_indices(self) -> list[int]:
        mode = self.filter_mode.get()
        indices: list[int] = []

        for i, item in enumerate(self.todos):
            if mode == "all":
                indices.append(i)
            elif mode == "active" and not item.done:
                indices.append(i)
            elif mode == "done" and item.done:
                indices.append(i)
        return indices

    def _refresh_list(self) -> None:
        self.todo_listbox.delete(0, tk.END)
        for idx in self._filtered_indices():
            item = self.todos[idx]
            prefix = "✅" if item.done else "⬜"
            self.todo_listbox.insert(tk.END, f"{prefix} {item.text}")

        total = len(self.todos)
        done = sum(item.done for item in self.todos)
        active = total - done
        self.status_var.set(f"전체 {total}개 / 진행중 {active}개 / 완료 {done}개")

    def add_task(self) -> None:
        text = self.task_entry.get().strip()
        if not text:
            messagebox.showinfo("안내", "할 일을 입력해 주세요.")
            return

        self.todos.append(TodoItem(text=text))
        self.task_entry.delete(0, tk.END)
        self._save_todos()
        self._refresh_list()

    def _selected_actual_index(self) -> int | None:
        selection = self.todo_listbox.curselection()
        if not selection:
            return None

        filtered_indices = self._filtered_indices()
        if not filtered_indices:
            return None
        return filtered_indices[selection[0]]

    def toggle_task(self) -> None:
        idx = self._selected_actual_index()
        if idx is None:
            messagebox.showinfo("안내", "먼저 항목을 선택해 주세요.")
            return

        self.todos[idx].done = not self.todos[idx].done
        self._save_todos()
        self._refresh_list()

    def edit_task(self) -> None:
        idx = self._selected_actual_index()
        if idx is None:
            messagebox.showinfo("안내", "먼저 항목을 선택해 주세요.")
            return

        new_text = simpledialog.askstring("할 일 수정", "수정할 내용을 입력해 주세요.", initialvalue=self.todos[idx].text)
        if new_text is None:
            return

        text = new_text.strip()
        if not text:
            messagebox.showinfo("안내", "빈 내용으로 수정할 수 없습니다.")
            return

        self.todos[idx].text = text
        self._save_todos()
        self._refresh_list()

    def delete_task(self) -> None:
        idx = self._selected_actual_index()
        if idx is None:
            messagebox.showinfo("안내", "먼저 항목을 선택해 주세요.")
            return

        if not messagebox.askyesno("삭제 확인", "선택한 항목을 삭제할까요?"):
            return

        del self.todos[idx]
        self._save_todos()
        self._refresh_list()

    def clear_done(self) -> None:
        before = len(self.todos)
        self.todos = [item for item in self.todos if not item.done]
        removed = before - len(self.todos)

        if removed == 0:
            messagebox.showinfo("안내", "완료된 항목이 없습니다.")
            return

        self._save_todos()
        self._refresh_list()

    def _load_todos(self) -> list[TodoItem]:
        if not DATA_FILE.exists():
            return []

        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            return [TodoItem(**item) for item in data if isinstance(item, dict) and "text" in item]
        except (OSError, json.JSONDecodeError, TypeError):
            return []

    def _save_todos(self) -> None:
        try:
            payload = [asdict(item) for item in self.todos]
            DATA_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            messagebox.showerror("저장 오류", "할 일 목록을 저장하지 못했습니다.")


def main() -> None:
    try:
        app = TodoApp()
        app.mainloop()
    except tk.TclError as error:
        print("GUI 실행에 필요한 디스플레이 환경을 찾지 못했습니다.")
        print(f"상세 오류: {error}")


if __name__ == "__main__":
    main()

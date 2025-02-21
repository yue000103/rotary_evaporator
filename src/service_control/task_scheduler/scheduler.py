import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Task:
    id: str
    type: str
    parameters: Dict[str, Any]
    priority: int
    scheduled_time: datetime
    status: str = "pending"

class TaskScheduler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tasks: List[Task] = []
        
    def add_task(self, task: Task) -> bool:
        """添加新任务"""
        try:
            self.tasks.append(task)
            self.tasks.sort(key=lambda x: (x.priority, x.scheduled_time))
            self.logger.info(f"任务 {task.id} 已添加到调度队列")
            return True
        except Exception as e:
            self.logger.error(f"添加任务失败: {str(e)}")
            return False
            
    def get_next_task(self) -> Task:
        """获取下一个要执行的任务"""
        return self.tasks[0] if self.tasks else None 
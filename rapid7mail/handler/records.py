from dataclasses import dataclass


@dataclass(frozen=True)
class EvalRequestTask:
    eval_body: str
    task_from_email: str

from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal, NamedTuple, Tuple, Union
from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar, IntervalVar


@dataclass
class TaskData:
    start: IntVar
    end: IntVar
    interval: IntervalVar


@dataclass
class AssignedTaskType:
    start: int
    job: int
    index: int
    duration: int


@dataclass
class TaskSchedule:
    machine: int
    start: int
    end: int
    job: int


@dataclass
class SchedulerSuccess:
    objective_value: float
    output: list[TaskSchedule]


@dataclass
class SchedulerFailure:
    message: str
    status: str


CpSolverStatus = Union[
    Literal[0],
    Literal[1],
    Literal[2],
    Literal[3],
    Literal[4],
]


class TaskInput(NamedTuple):
    machine: int
    duration: int


# A job is a sequential list of tasks
JobsData = list[list[TaskInput]]

JobsByMachine = dict[int, list[AssignedTaskType]]

SchedulerOutput = Union[SchedulerSuccess, SchedulerFailure]


def schedule_jobs(
    jobs_data: JobsData,
    random_seed: int | None = None,
    num_search_workers: int | None = None,
) -> SchedulerOutput:
    machines_count = 1 + max(task.machine for job in jobs_data for task in job)
    all_machines = range(machines_count)
    # Computes horizon dynamically as the sum of all durations.
    horizon: int = sum(task.duration for job in jobs_data for task in job)

    model = cp_model.CpModel()

    # Creates job intervals and add to the corresponding machine lists.
    all_tasks: dict[Tuple[int, int], TaskData] = {}
    machine_to_intervals: defaultdict[int, list[IntervalVar]] = defaultdict(list)

    for job_id, job in enumerate(jobs_data):
        for task_id, task in enumerate(job):
            machine, duration = task
            suffix = f"_{job_id}_{task_id}"
            start_var = model.new_int_var(0, horizon, "start" + suffix)
            end_var = model.new_int_var(0, horizon, "end" + suffix)
            interval_var = model.new_interval_var(
                start_var, duration, end_var, "interval" + suffix
            )
            all_tasks[job_id, task_id] = TaskData(
                start=start_var, end=end_var, interval=interval_var
            )
            machine_to_intervals[machine].append(interval_var)

    # Create and add disjunctive constraints.
    for machine in all_machines:
        model.add_no_overlap(machine_to_intervals[machine])

    # Precedences inside a job.
    for job_id, job in enumerate(jobs_data):
        for task_id in range(len(job) - 1):
            model.add(
                all_tasks[job_id, task_id + 1].start >= all_tasks[job_id, task_id].end
            )

    # Makespan objective.
    obj_var = model.new_int_var(0, horizon, "makespan")
    model.add_max_equality(
        obj_var,
        [all_tasks[job_id, len(job) - 1].end for job_id, job in enumerate(jobs_data)],
    )
    model.minimize(obj_var)

    solver = cp_model.CpSolver()
    if random_seed is not None:
        solver.parameters.random_seed = random_seed
    if num_search_workers is not None:
        solver.parameters.num_search_workers = num_search_workers
    status = solver.solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:  # pyright: ignore[reportUnnecessaryComparison]
        # Create one list of assigned tasks per machine.
        assigned_jobs: JobsByMachine = defaultdict(list)
        for job_id, job in enumerate(jobs_data):
            for task_id, task in enumerate(job):
                machine = task[0]
                assigned_jobs[machine].append(
                    AssignedTaskType(
                        start=solver.value(all_tasks[job_id, task_id].start),
                        job=job_id,
                        index=task_id,
                        duration=task[1],
                    )
                )

        output: list[TaskSchedule] = []
        for job_id, job in enumerate(jobs_data):
            for task_id, task in enumerate(job):
                machine = task.machine
                duration = task.duration
                start = solver.value(all_tasks[job_id, task_id].start)

                output.append(
                    TaskSchedule(
                        machine=machine, start=start, end=start + duration, job=job_id
                    )
                )
        output.sort(key=lambda o: (o.start, o.machine))

        return SchedulerSuccess(
            objective_value=solver.objective_value,
            output=output,
        )
    else:
        return SchedulerFailure(
            message=f"No solution found: {solver.StatusName(status)}",
            status=solver.StatusName(status),
        )


if __name__ == "__main__":
    jobs_data: JobsData = [
        # Job0
        [
            TaskInput(machine=0, duration=3),
            TaskInput(machine=1, duration=2),
            TaskInput(machine=2, duration=2),
        ],
        # Job1
        [
            TaskInput(machine=0, duration=2),
            TaskInput(machine=2, duration=1),
            TaskInput(machine=1, duration=4),
        ],
        # Job2
        [
            TaskInput(machine=1, duration=4),
            TaskInput(machine=2, duration=3),
        ],
    ]
    print("running...")
    result = schedule_jobs(jobs_data)
    if isinstance(result, SchedulerFailure):
        print(result.message)
    else:
        print(f"Objective value: {result.objective_value}")
        print(result.output)

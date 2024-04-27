from robot_cafe.solver import (
    TaskSchedule,
    JobsData,
    SchedulerSuccess,
    TaskInput,
    schedule_jobs,
)

TEST_SEED = 10


def test_schedule_jobs():
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

    # sorted by start time and then by machine
    expected = [
        TaskSchedule(machine=0, start=0, end=2, job=1),
        TaskSchedule(machine=1, start=0, end=4, job=2),
        TaskSchedule(machine=0, start=2, end=5, job=0),
        TaskSchedule(machine=2, start=2, end=3, job=1),
        TaskSchedule(machine=2, start=4, end=7, job=2),
        TaskSchedule(machine=1, start=5, end=7, job=0),
        TaskSchedule(machine=1, start=7, end=11, job=1),
        TaskSchedule(machine=2, start=7, end=9, job=0),
    ]

    # this is generally nondeterministic, so we use one worker
    # (and set random seed, but I'm not sure that matters)
    # (it seems that two workers would also be consistent, as long as it's a fixed number?)
    result = schedule_jobs(jobs_data, random_seed=TEST_SEED, num_search_workers=1)

    assert isinstance(result, SchedulerSuccess)
    assert result.objective_value == 11.0
    assert result.output == expected

import pandas as pd
from csp import Constraint, CSP
from typing import Dict, List, Optional
from itertools import combinations
from pprint import pprint


class OnePerDeskConstraint(Constraint[str, str]):
    def __init__(self, h1: str, h2: str) -> None:
        super().__init__([h1, h2])
        self.h1: str = h1
        self.h2: str = h2

    def satisfied(self, assignment: Dict[str, str]) -> bool:
        if self.h1 not in assignment or self.h2 not in assignment:
            return True
        return assignment[self.h1] != assignment[self.h2]

    pass


class SequentialTimeConstraint(Constraint[str, str]):
    def __init__(self, h1: str, h2: str) -> None:
        super().__init__([h1, h2])
        self.h1: str = h1
        self.h2: str = h2

    def satisfied(self, assignment: Dict[str, str]) -> bool:
        if self.h1 not in assignment or self.h2 not in assignment:
            return True
        return assignment[self.h1] == assignment[self.h2]

    pass


software = {
    'Photoshop': ["Mango 2", "Mango 1"],
    'LV': ["Mango II", "Pida III", "Up II", "Stannis II"],
    'Note': [
        "Note 1",
        "Note 2",
        "Note 3",
        "Note 4",
        "Note 5",
    ]
}


class PrefConstraint(Constraint[str, str]):
    def __init__(self, h1: str) -> None:
        super().__init__([h1])
        self.h1: str = h1

    def satisfied(self, assignment: Dict[str, str]) -> bool:
        if self.h1 not in assignment:
            return True
        return (assignment[self.h1] in software[self.h1[3]])

    pass


def add_one_per_desk_constraint(csp, vars_):
    df = pd.DataFrame(vars_, columns=["acronym", "day", "time", "notePref"])

    day = (df['day'].drop_duplicates())
    time = (df['time'].drop_duplicates())

    dup = df[df.duplicated(['day', 'time'], keep=False)]
    unique = dup[['day', 'time']].drop_duplicates()

    for i in unique.itertuples():
        conflicts = list(
            combinations([
                tuple(y)
                for y in df.loc[(df['day'] == i.day)
                                & (df['time'] == i.time)].values.tolist()
            ], 2))
        for conflict in conflicts:
            csp.add_constraint(OnePerDeskConstraint(*conflict))
    pass


def add_sequential_time_same_desk_constraint(csp, vars_):
    df = pd.DataFrame(vars_, columns=["acronym", "day", "time", "notePref"])
    df.time = [x + ':00' for x in df.time]
    df.time = pd.to_timedelta(df.time)
    ha = pd.Timedelta('00:50:00')
    df = df.sort_values(by=['day', 'time'])
    seq_p_person = []
    for ac in df.acronym.drop_duplicates():
        seq = df.loc[df.acronym == ac]
        for d in seq.day.drop_duplicates():
            seq_p_day = seq.loc[seq.day == d]
            seq_p_day['interval'] = (
                (seq_p_day.time - seq_p_day.time.iloc[0]) / ha)
            if seq_p_day['interval'].sum():
                seq_p_day = seq_p_day.reset_index(drop=True).drop(
                    columns=['interval'])
                mask = seq_p_day.time.diff().apply(
                    lambda x: x % ha < pd.Timedelta('00:30:00'))
                seq_p_day.time = seq_p_day.time.apply(
                    lambda x:
                    f'{x.components.hours:02d}:{x.components.minutes:02d}'
                    if not pd.isnull(x) else '')
                indexes = (mask.index[mask == False].tolist())
                for idx, val in enumerate(indexes):
                    try:
                        seq_p_person.append(seq_p_day[val:indexes[idx + 1]])
                    except IndexError:
                        seq_p_person.append(seq_p_day[val:])
    seq = [
        list(combinations([tuple(x) for x in i.values.tolist()], 2))
        for i in seq_p_person
    ]
    for i in seq:
        for j in i:
            csp.add_constraint(SequentialTimeConstraint(*j))
    pass


def add_prefs_constraint(csp, vars_):
    for var in vars_:
        csp.add_constraint(PrefConstraint(var))

    pass


def process_variables(times):
    variables: List[tuple] = []

    for member in times.keys():
        for time in times[member]:
            variables.append(tuple([member] + time))
    return variables


def process_domains(variables):
    domains: Dict[str, List[str]] = {}

    for variable in variables:
        domains[variable] = [
            "Note 1", "Note 2", "Note 3", "Note 4", "Note 5", "Mango 1",
            "Mango II", "Pida III", "Up II", "Stannis II", "Container",
            "Santahora", "Stannis I", "1007", "Bovary"
        ]
    return domains


if __name__ == "__main__":
    timeSchedule = {
        "JNR": [["Mon", "13:30", "Note"], ["Mon", "14:20", "Note"],
                ["Tue", "07:30", "Note"], ["Tue", "08:20", "Note"],
                ["Tue", "09:10", "Note"], ["Wed", "07:30", "Note"],
                ["Wed", "08:20", "Note"], ["Wed", "09:10", "Note"],
                ["Wed", "10:10", "Note"], ["Wed", "12:40", "Note"],
                ["Wed", "13:30", "Note"], ["Wed", "14:20", "Note"],
                ["Wed", "15:10", "Note"], ["Thu", "10:10", "Note"],
                ["Thu", "11:00", "Note"], ["Thu", "16:20", "Note"],
                ["Thu", "17:10", "Note"], ["Fri", "07:30", "Note"],
                ["Fri", "10:10", "Note"], ["Fri", "11:00", "Note"]],
        "FSN": [["Mon", "07:30", "LV"], ["Mon", "08:20", "LV"],
                ["Mon", "09:10", "LV"], ["Tue", "07:30", "LV"],
                ["Tue", "08:20", "LV"], ["Tue", "09:10", "LV"],
                ["Wed", "10:10", "LV"], ["Wed", "11:00", "LV"],
                ["Wed", "13:30", "LV"], ["Wed", "14:20", "LV"],
                ["Wed", "15:10", "LV"], ["Thu", "08:20", "Note"],
                ["Thu", "09:10", "Note"], ["Thu", "15:10", "Note"],
                ["Thu", "16:20", "Note"], ["Thu", "17:10", "Note"],
                ["Thu", "18:00", "Note"], ["Fri", "10:10", "Note"],
                ["Fri", "11:00", "Note"], ["Fri", "11:50", "Note"],
                ["Sat", "11:50", "Note"]],
        "PDK": [["Mon", "09:10", "Note"], ["Mon", "10:10", "Note"],
                ["Mon", "11:00", "Note"], ["Mon", "13:30", "Note"],
                ["Mon", "14:20", "Note"], ["Mon", "15:10", "Note"],
                ["Mon", "16:20", "Note"]]
    }

    variables = process_variables(timeSchedule)

    domains = process_domains(variables)

    csp: CSP[str, str] = CSP(variables, domains)

    add_one_per_desk_constraint(csp, variables)

    add_sequential_time_same_desk_constraint(csp, variables)

    add_prefs_constraint(csp, variables)

    solution: Optional[Dict[str, str]] = csp.backtracking_search()

    if solution is None:
        pprint("No solution found!")
    else:
        pprint(solution)
        pass

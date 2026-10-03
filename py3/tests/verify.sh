#!/bin/bash -i
#

# Safety check: must run from a directory named "tests"
if [[ "$(basename "$PWD")" != "tests" ]]; then
    echo "ERROR: verify.sh must be run from a directory named 'tests'." >&2
    echo "  Current PWD: $PWD" >&2
    exit 1
fi

# Starting-point smoke test for bisos.airflow -- covers airflowAdmin.cs (primary
# target for this starting point) and quickAirflow.cs. Converted from
# bisos.dockerProc's py3/tests/verify.sh; will be expanded as the package develops.

# --- CS entry points: smoke test (no args → examples/usage, non-zero ok) ---

lpDo ../bin/airflowAdmin.cs
lpDo ../bin/quickAirflow.cs

# --- airflowAdmin.cs: each admin sub-Cmnd runs and produces examples output ---

lpDo ../bin/airflowAdmin.cs -i examples
lpDo ../bin/airflowAdmin.cs -i hostInfo
lpDo ../bin/airflowAdmin.cs -i servicesInfo
lpDo ../bin/airflowAdmin.cs -i usersInfo
lpDo ../bin/airflowAdmin.cs -i fullUpdate

# --- quickAirflow.cs: default examples entry runs ---

lpDo ../bin/quickAirflow.cs -i examples

# --- airflowAdmin.cs: import + class presence smoke test ---

lpDo python3 -c "
import importlib.util, sys

spec = importlib.util.spec_from_file_location('airflowAdmin', '../bin/airflowAdmin.cs')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

expectedCmnds = [
    'examples', 'fullUpdate', 'hostInfo', 'servicesInfo', 'usersInfo', 'driftCheck',
]

failed = 0
for n in expectedCmnds:
    if not hasattr(m, n):
        print(f'  [FAIL] missing Cmnd: {n}'); failed += 1
    else:
        print(f'  [PASS] Cmnd present: {n}')

if failed:
    print(f'airflowAdmin.cs: {failed} test(s) FAILED')
    sys.exit(1)
else:
    print('airflowAdmin.cs: all cases PASS')
" 2>/dev/null || true

# --- bisos.airflow.airflowInfo: pure module, generators agree with the facts ---

lpDo python3 -c "
from bisos.airflow import airflowInfo as m
i = m.airflowInfo
env = m.envFileContent()
failed = 0
for name, ok in [
    ('home in env file', f'AIRFLOW_HOME={i.home}\n' in env),
    ('env file is 5 lines', len(env.splitlines()) == 5),
    ('execution url has the banna port', f':{i.portNu}/execution/' in env),
    ('service lines name the account', m.sysdServiceLines().startswith(f'User={i.acctName}\n')),
    ('binPath is under the virtenv', i.binPath.parent.parent == i.virtenv),
    ('a generated env file shows no drift', not any(m.envFileDrift(env).values())),
    ('a missing key is reported', m.envFileDrift('AIRFLOW_HOME=/x\n')['missing'] != []),
    ('a changed value is reported', m.envFileDrift(env.replace(str(i.home), '/x'))['differs'] != []),
    ('a unit lacking the identity lines is reported', len(m.unitDrift('[Service]\n')) == 3),
]:
    print(('  [PASS] ' if ok else '  [FAIL] ') + name); failed += (not ok)
raise SystemExit(1 if failed else 0)
" || true

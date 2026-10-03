# -*- coding: utf-8 -*-

""" #+begin_org
* ~[Summary]~ :: =CS-Lib= The single source of the facts of this host's Airflow installation.
#+end_org """

""" #+begin_org
* [[elisp:(org-cycle)][| ~Description~ |]] :: Facts that used to be repeated across airflow-sbom.pcs, airflowAdmin.cs,
the five airflow-*-sysd.pcs units, airflow-here-dns.pcs and airflow-wvd.pcs: the account, AIRFLOW_HOME,
the EnvironmentFile, the virtenv, the fqdn, the port, the metadata DB connection string and the version floor.
** Pure: importing this module has no side effects and touches no host state.
** The generators below return the text of /etc/default/airflow and of the shared [Service] lines of the
units, so that the code that writes them and the code that checks them cannot disagree.
** Status: Starting point -- nothing consumes it yet.
** /[[elisp:(org-cycle)][| Planned Improvements |]]/ :
*** TODO Switch airflow-sbom.pcs, airflowAdmin.cs, the units, dns and wvd to this module (4.4 and 4.6).
*** TODO Use minVersion as the apache-airflow floor in airflow-sbom.pcs (4.5).
#+end_org """

####+BEGIN: b:prog:file/proclamations :outLevel 1
""" #+begin_org
* *[[elisp:(org-cycle)][| Proclamations |]]* :: Libre-Halaal Software --- Part Of BISOS ---  Poly-COMEEGA Format.
** This is Libre-Halaal Software. © Neda Communications, Inc. Subject to AGPL.
** It is part of BISOS (ByStar Internet Services OS)
** Best read and edited  with Blee in Poly-COMEEGA (Polymode Colaborative Org-Mode Enhance Emacs Generalized Authorship)
#+end_org """
####+END:

####+BEGIN: b:prog:file/particulars :authors ("./inserts/authors-mb.org")
""" #+begin_org
* *[[elisp:(org-cycle)][| Particulars |]]* :: Authors, version
** This File: /bisos/git/bxRepos/bisos-pip/airflow/py3/bisos/airflow/airflowInfo.py
** Authors: Mohsen BANAN, http://mohsen.banan.1.byname.net/contact
#+end_org """
####+END:

import dataclasses
import pathlib

from bisos.banna import tcpPorts as bannaTcpPorts


def _bannaPortNu() -> int:
    """The api-server port. The registry, bisos.banna, is authoritative: never hardcode it."""
    return bannaTcpPorts.tcpPortsAssignedList.tcpPortsList['airflow'].portNu


@dataclasses.dataclass(frozen=True)
class AirflowInfo:
    """The facts of this host's Airflow installation. Built once, as airflowInfo below."""

    # The OS account the units run as. PostgreSQL peer authentication maps it to the
    # like-named role, so the role and the metadata database are named the same.
    acctName: str = "airflow"

    # Runtime state only (dags, logs, airflow.cfg). Not the python venv: see virtenv.
    home: pathlib.Path = pathlib.Path("/opt/airflow")

    # Read by systemd as root before the units drop to User=. root:acctName 640.
    envFile: pathlib.Path = pathlib.Path("/etc/default/airflow")

    # The shared venv Airflow is installed into. Deliberately not per-application.
    virtenv: pathlib.Path = pathlib.Path("/bisos/venv/py3/asc")

    fqdn: str = "airflow.here"

    # api-server, dag-processor and the Task Execution API only exist from Airflow 3.
    minVersion: str = "3.0"

    # Peer auth over the unix socket: no user, no password, no secret anywhere.
    pgConnStr: str = "postgresql+psycopg2://@/airflow?host=/var/run/postgresql"

    portNu: int = dataclasses.field(default_factory=_bannaPortNu)

    @property
    def dagsDir(self) -> pathlib.Path:
        return self.home / "dags"

    @property
    def logsDir(self) -> pathlib.Path:
        return self.home / "logs"

    @property
    def binPath(self) -> pathlib.Path:
        return self.virtenv / "bin" / "airflow"

    @property
    def baseUrl(self) -> str:
        """The address humans browse, through the nginx vhost."""
        return f"http://{self.fqdn}"

    @property
    def executionApiUrl(self) -> str:
        """Straight to the api-server, so that task execution does not depend on nginx."""
        return f"http://localhost:{self.portNu}/execution/"

    @property
    def pipVersionSpec(self) -> str:
        return f">={self.minVersion}"

    @property
    def cliPrefix(self) -> str:
        """Prefix for every by-hand CLI invocation.

        sudo -u acct  -- AIRFLOW_HOME and its files are owned by the account.
        env AIRFLOW_HOME -- the EnvironmentFile is read by systemd, not by an interactive
                         shell. Without it the CLI silently operates on ~acct/airflow.
        """
        return f"sudo -u {self.acctName} env AIRFLOW_HOME={self.home} {self.binPath}"


# A Singleton
airflowInfo = AirflowInfo()


def envFileContent(info: AirflowInfo = airflowInfo) -> str:
    """The content /etc/default/airflow is generated with. Written only when absent.

    BASE_URL and EXECUTION_API_SERVER_URL are not optional niceties. Airflow 3 task
    processes reach the api-server over HTTP (the Task Execution API) instead of
    touching the DB; when BASE_URL is unset the task SDK falls back to
    http://localhost:8080. The port here comes from bisos.banna, not Airflow's default,
    so every task would die with [Errno 111] Connection refused before it starts while
    all units stay green and the UI serves normally.
    """
    return (
        f"AIRFLOW_HOME={info.home}\n"
        f"AIRFLOW__DATABASE__SQL_ALCHEMY_CONN={info.pgConnStr}\n"
        f"AIRFLOW__API__BASE_URL={info.baseUrl}\n"
        f"AIRFLOW__CORE__EXECUTION_API_SERVER_URL={info.executionApiUrl}\n"
        "# Add any overrides or environment variables needed by your DAGs here\n"
    )


def sysdServiceLines(info: AirflowInfo = airflowInfo) -> str:
    """The identity lines every airflow-*.service has in its [Service] section."""
    return (
        f"User={info.acctName}\n"
        f"Group={info.acctName}\n"
        f"EnvironmentFile={info.envFile}\n"
    )



def _envFileMap(text: str) -> dict[str, str]:
    """KEY=VALUE lines of an EnvironmentFile; comments and blank lines are skipped."""
    pairs: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        pairs[key] = value
    return pairs


def envFileDrift(liveText: str, info: AirflowInfo = airflowInfo) -> dict[str, list]:
    """Compare a live /etc/default/airflow with what envFileContent() would generate.

    The file is written only when absent, so hand overrides are legitimate and later
    generator lines never reach existing hosts. This therefore only reports:
      missing -- keys the generator has and the live file lacks
      differs -- (key, expected, live) where both have the key with different values
      extra   -- keys only the live file has (hand additions)
    """
    expected = _envFileMap(envFileContent(info))
    live = _envFileMap(liveText)
    return {
        "missing": [k for k in expected if k not in live],
        "differs": [(k, expected[k], live[k]) for k in expected if k in live and live[k] != expected[k]],
        "extra": [k for k in live if k not in expected],
    }


def unitDrift(unitText: str, info: AirflowInfo = airflowInfo) -> list[str]:
    """The identity lines (sysdServiceLines) that an installed unit file lacks."""
    present = {line.strip() for line in unitText.splitlines()}
    return [line for line in sysdServiceLines(info).splitlines() if line not in present]


####+BEGIN: b:py3:cs:framework/endOfFile :basedOn "classification"
""" #+begin_org
* [[elisp:(org-cycle)][| *End-Of-Editable-Text* |]] :: emacs and org variables and control parameters
#+end_org """

#+STARTUP: showall

### local variables:
### no-byte-compile: t
### end:
####+END:

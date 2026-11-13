"""DeadlineLens trace format v1.

This is an application-level schema so a QNX 8.0 target and a host tool can
share evidence without depending on a particular tracelogger binary layout.
When SDP is available, a QNX target should emit this JSON (and may also keep
raw kernel traces as optional attachments).

Required:
  format: "deadlinelens-trace/v1"
  threads: list of {id, name, priority, period_ns, deadline_ns}
  events: list of {t_ns, type, thread_id, job}

Optional provenance (used to tell contest evidence from development traces):
  source: free-text origin label
  qnx_version, target, toolchain: official-rules fields
  qnx: optional object with the same keys plus uname_* and sched_note
  clock_hz: clock frequency used to interpret t_ns (1e9 if omitted)
"""

FORMAT = "deadlinelens-trace/v1"

# Event types
RELEASE = "release"  # job became ready (period start)
START = "start"      # thread began running the job
END = "end"          # job finished
MISS = "miss"        # recorded miss at or after the deadline
PREEMPT = "preempt"  # running thread preempted
READY = "ready"

/*
 * Application-level DeadlineLens trace helper for QNX 8.0.
 * Compiled and run on QNX 8.0 (qcc -Vgcc_ntox86_64, QEMU).
 * This header is not for the Linux host analyzer.
 */
#ifndef DEADLINE_TRACE_H
#define DEADLINE_TRACE_H

#ifndef __QNX__
#error This QNX 8.0 emitter is not for the Linux host; use target/posix_fallback on a development machine.
#endif

#include <stdint.h>

int64_t dl_now_ns(void);
void dl_init(void);
void dl_add_thread(int id, const char *name, int priority, int64_t period_ns,
                   int64_t deadline_ns);
void dl_log(int64_t t_ns, const char *type, int thread_id, int job);
int dl_write_json(const char *path, const char *source, const char *qnx_version,
                  const char *target, const char *toolchain);

#endif /* DEADLINE_TRACE_H */

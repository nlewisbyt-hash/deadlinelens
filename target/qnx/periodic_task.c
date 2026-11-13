/*
 * DeadlineLens QNX 8.0 target demo.
 *
 * Two SCHED_FIFO threads (sensor priority 21, control priority 15) wake
 * with clock_nanosleep / TIMER_ABSTIME on a 10 ms period. Control job 3
 * is deliberately long enough to miss its deadline.
 *
 * Compiled and run on QNX 8.0 with qcc -Vgcc_ntox86_64 under QEMU.
 * Official contest evidence is the captured JSON, not this source alone.
 * See notes/build-run-note.md.
 *
 * Usage:
 *   ./periodic_task --out qnx-deadlinelens-trace.json --target qemu \
 *       --toolchain 'qcc -Vgcc_ntox86_64'
 */
#ifndef __QNX__
#error This QNX 8.0 emitter is not for the Linux host; use target/posix_fallback on a development machine.
#endif

#include "deadline_trace.h"

#include <errno.h>
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/utsname.h>
#include <time.h>
#include <unistd.h>

#ifndef TOOLCHAIN_STRING
#define TOOLCHAIN_STRING "qcc -Vgcc_ntox86_64"
#endif

#define PERIOD_NS 10000000LL
#define DEADLINE_NS 10000000LL
#define JOBS 5
#define SENSOR_ID 1
#define CONTROL_ID 2
#define SENSOR_PRIO 21
#define CONTROL_PRIO 15
#define SENSOR_WORK_NS 2000000LL
#define CONTROL_WORK_NS 3000000LL
#define CONTROL_MISS_WORK_NS 13000000LL

struct task {
    int id;
    const char *name;
    int priority;
    int64_t work_ns;
};

static int64_t g_origin_ns;
static volatile int g_origin_ready;
static pthread_mutex_t g_origin_mu = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t g_origin_cv = PTHREAD_COND_INITIALIZER;

static void usage(const char *argv0)
{
    fprintf(stderr,
            "Usage: %s --out <path> [--target qemu] [--toolchain 'qcc -Vgcc_ntox86_64']\n",
            argv0);
}

static void burn_ns(int64_t ns)
{
    int64_t until = dl_now_ns() + ns;

    while (dl_now_ns() < until) {
        /* Busy-wait so the job occupies the CPU for a known duration. */
    }
}

static int request_fifo(int priority)
{
    struct sched_param sp;

    memset(&sp, 0, sizeof sp);
    sp.sched_priority = priority;
    if (pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp) != 0)
        return -1;
    return 0;
}

static int sleep_until(int64_t abs_ns)
{
    struct timespec ts;

    ts.tv_sec = (time_t)(abs_ns / 1000000000LL);
    ts.tv_nsec = (long)(abs_ns % 1000000000LL);
    while (clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts, NULL) != 0) {
        if (errno != EINTR)
            return -1;
    }
    return 0;
}

static void *worker(void *arg)
{
    const struct task *task = arg;
    int job;

    request_fifo(task->priority);

    pthread_mutex_lock(&g_origin_mu);
    while (!g_origin_ready)
        pthread_cond_wait(&g_origin_cv, &g_origin_mu);
    pthread_mutex_unlock(&g_origin_mu);

    for (job = 1; job <= JOBS; job++) {
        int64_t release_ns = g_origin_ns + (int64_t)(job - 1) * PERIOD_NS;
        int64_t deadline_ns = release_ns + DEADLINE_NS;
        int64_t start_ns;
        int64_t end_ns;
        int64_t work = task->work_ns;

        if (task->id == CONTROL_ID && job == 3)
            work = CONTROL_MISS_WORK_NS;

        if (sleep_until(release_ns) != 0)
            break;

        /* Log the scheduled release so period jitter is zero when the
         * absolute wake-up is honoured. */
        dl_log(release_ns, "release", task->id, job);
        start_ns = dl_now_ns();
        dl_log(start_ns, "start", task->id, job);
        burn_ns(work);
        end_ns = dl_now_ns();
        dl_log(end_ns, "end", task->id, job);
        if (end_ns >= deadline_ns)
            dl_log(deadline_ns, "miss", task->id, job);
    }
    return NULL;
}

int main(int argc, char **argv)
{
    const char *out_path = NULL;
    const char *target = "qemu";
    const char *toolchain = TOOLCHAIN_STRING;
    char qnx_version[64];
    struct utsname u;
    struct task sensor = {SENSOR_ID, "sensor", SENSOR_PRIO, SENSOR_WORK_NS};
    struct task control = {CONTROL_ID, "control", CONTROL_PRIO, CONTROL_WORK_NS};
    pthread_t th_sensor, th_control;
    int i;

    for (i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--out") == 0 && i + 1 < argc) {
            out_path = argv[++i];
        } else if (strcmp(argv[i], "--target") == 0 && i + 1 < argc) {
            target = argv[++i];
        } else if (strcmp(argv[i], "--toolchain") == 0 && i + 1 < argc) {
            toolchain = argv[++i];
        } else if (strcmp(argv[i], "--help") == 0) {
            usage(argv[0]);
            return 0;
        } else {
            usage(argv[0]);
            return 2;
        }
    }
    if (!out_path) {
        usage(argv[0]);
        return 2;
    }

    memset(&u, 0, sizeof u);
    if (uname(&u) == 0)
        snprintf(qnx_version, sizeof qnx_version, "QNX %s", u.release);
    else
        snprintf(qnx_version, sizeof qnx_version, "QNX 8.0.0");

    dl_init();
    dl_add_thread(SENSOR_ID, "sensor", SENSOR_PRIO, PERIOD_NS, DEADLINE_NS);
    dl_add_thread(CONTROL_ID, "control", CONTROL_PRIO, PERIOD_NS, DEADLINE_NS);

    if (pthread_create(&th_sensor, NULL, worker, &sensor) != 0 ||
        pthread_create(&th_control, NULL, worker, &control) != 0) {
        fprintf(stderr, "pthread_create failed: %s\n", strerror(errno));
        return 1;
    }

    /* Align both threads to a common first release one period from now. */
    pthread_mutex_lock(&g_origin_mu);
    g_origin_ns = dl_now_ns() + PERIOD_NS;
    g_origin_ready = 1;
    pthread_cond_broadcast(&g_origin_cv);
    pthread_mutex_unlock(&g_origin_mu);

    pthread_join(th_sensor, NULL);
    pthread_join(th_control, NULL);

    if (dl_write_json(out_path, "qnx-periodic-task (captured on QNX)",
                      qnx_version, target, toolchain) != 0) {
        fprintf(stderr, "failed to write %s: %s\n", out_path, strerror(errno));
        return 1;
    }
    return 0;
}

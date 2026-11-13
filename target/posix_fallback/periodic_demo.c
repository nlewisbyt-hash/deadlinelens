/*
 * POSIX fallback emitter for developing the DeadlineLens host tool.
 * This is NOT contest evidence and is not captured on QNX.
 *
 *   cc -std=gnu11 -Wall -o periodic_demo periodic_demo.c
 *   ./periodic_demo /tmp/demo-trace.json
 */
#define _GNU_SOURCE

#include <errno.h>
#include <pthread.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

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
#define MAX_EVENTS 512

struct event {
    int64_t t_ns;
    const char *type;
    int thread_id;
    int job;
};

struct task {
    int id;
    const char *name;
    int priority;
    int64_t work_ns;
};

static struct event events[MAX_EVENTS];
static int nevents;
static pthread_mutex_t evlock = PTHREAD_MUTEX_INITIALIZER;
static int64_t origin_ns;
static volatile int origin_ready;
static pthread_mutex_t origin_mu = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t origin_cv = PTHREAD_COND_INITIALIZER;

static int64_t now_ns(void)
{
    struct timespec ts;

    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
        return 0;
    return (int64_t)ts.tv_sec * 1000000000LL + (int64_t)ts.tv_nsec;
}

static void log_ev(int64_t t_ns, const char *type, int thread_id, int job)
{
    pthread_mutex_lock(&evlock);
    if (nevents < MAX_EVENTS) {
        events[nevents].t_ns = t_ns;
        events[nevents].type = type;
        events[nevents].thread_id = thread_id;
        events[nevents].job = job;
        nevents++;
    }
    pthread_mutex_unlock(&evlock);
}

static void burn_ns(int64_t ns)
{
    int64_t until = now_ns() + ns;

    while (now_ns() < until) {
    }
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
    struct sched_param sp;
    int job;

    memset(&sp, 0, sizeof sp);
    sp.sched_priority = task->priority;
    pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp); /* best-effort */

    pthread_mutex_lock(&origin_mu);
    while (!origin_ready)
        pthread_cond_wait(&origin_cv, &origin_mu);
    pthread_mutex_unlock(&origin_mu);

    for (job = 1; job <= JOBS; job++) {
        int64_t release_ns = origin_ns + (int64_t)(job - 1) * PERIOD_NS;
        int64_t deadline_ns = release_ns + DEADLINE_NS;
        int64_t start_ns, end_ns, work = task->work_ns;

        if (task->id == CONTROL_ID && job == 3)
            work = CONTROL_MISS_WORK_NS;
        if (sleep_until(release_ns) != 0)
            break;
        log_ev(release_ns, "release", task->id, job);
        start_ns = now_ns();
        log_ev(start_ns, "start", task->id, job);
        burn_ns(work);
        end_ns = now_ns();
        log_ev(end_ns, "end", task->id, job);
        if (end_ns >= deadline_ns)
            log_ev(deadline_ns, "miss", task->id, job);
    }
    return NULL;
}

static int write_json(const char *path)
{
    FILE *fp;
    int i;

    fp = fopen(path, "w");
    if (!fp)
        return -1;
    fputs("{\n", fp);
    fputs("  \"format\": \"deadlinelens-trace/v1\",\n", fp);
    fputs("  \"clock_hz\": 1000000000,\n", fp);
    fputs("  \"source\": \"posix-fallback-periodic-demo (NOT contest evidence; not captured on QNX)\",\n", fp);
    fputs("  \"threads\": [\n", fp);
    fputs("    {\"id\": 1, \"name\": \"sensor\", \"priority\": 21, \"period_ns\": 10000000, \"deadline_ns\": 10000000},\n", fp);
    fputs("    {\"id\": 2, \"name\": \"control\", \"priority\": 15, \"period_ns\": 10000000, \"deadline_ns\": 10000000}\n", fp);
    fputs("  ],\n", fp);
    fputs("  \"events\": [\n", fp);
    for (i = 0; i < nevents; i++) {
        fprintf(fp,
                "    {\"t_ns\": %lld, \"type\": \"%s\", \"thread_id\": %d, \"job\": %d}%s\n",
                (long long)events[i].t_ns, events[i].type,
                events[i].thread_id, events[i].job,
                (i + 1 < nevents) ? "," : "");
    }
    fputs("  ]\n}\n", fp);
    return fclose(fp) == 0 ? 0 : -1;
}

int main(int argc, char **argv)
{
    const char *path;
    struct task sensor = {SENSOR_ID, "sensor", SENSOR_PRIO, SENSOR_WORK_NS};
    struct task control = {CONTROL_ID, "control", CONTROL_PRIO, CONTROL_WORK_NS};
    pthread_t th_sensor, th_control;

    if (argc != 2) {
        fprintf(stderr, "Usage: %s <trace.json>\n", argv[0]);
        return 2;
    }
    path = argv[1];

    if (pthread_create(&th_sensor, NULL, worker, &sensor) != 0 ||
        pthread_create(&th_control, NULL, worker, &control) != 0) {
        fprintf(stderr, "pthread_create failed: %s\n", strerror(errno));
        return 1;
    }

    pthread_mutex_lock(&origin_mu);
    origin_ns = now_ns() + PERIOD_NS;
    origin_ready = 1;
    pthread_cond_broadcast(&origin_cv);
    pthread_mutex_unlock(&origin_mu);

    pthread_join(th_sensor, NULL);
    pthread_join(th_control, NULL);

    if (write_json(path) != 0) {
        fprintf(stderr, "failed to write %s: %s\n", path, strerror(errno));
        return 1;
    }
    return 0;
}

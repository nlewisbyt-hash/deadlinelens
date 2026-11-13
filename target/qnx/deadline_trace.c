/*
 * DeadlineLens trace buffer and JSON writer for QNX 8.0.
 * Compiled and run on QNX 8.0 with qcc -Vgcc_ntox86_64.
 */
#ifndef __QNX__
#error This QNX 8.0 emitter is not for the Linux host; use target/posix_fallback on a development machine.
#endif

#include "deadline_trace.h"

#include <errno.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <sys/utsname.h>
#include <time.h>

#define DL_MAX_THREADS 8
#define DL_MAX_EVENTS 512
#define DL_NAME_MAX 64
#define DL_TYPE_MAX 16

struct dl_thread {
    int id;
    char name[DL_NAME_MAX];
    int priority;
    int64_t period_ns;
    int64_t deadline_ns;
};

struct dl_event {
    int64_t t_ns;
    char type[DL_TYPE_MAX];
    int thread_id;
    int job;
};

static struct dl_thread threads[DL_MAX_THREADS];
static int nthreads;
static struct dl_event events[DL_MAX_EVENTS];
static int nevents;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

int64_t dl_now_ns(void)
{
    struct timespec ts;

    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
        return 0;
    return (int64_t)ts.tv_sec * 1000000000LL + (int64_t)ts.tv_nsec;
}

void dl_init(void)
{
    pthread_mutex_lock(&lock);
    nthreads = 0;
    nevents = 0;
    pthread_mutex_unlock(&lock);
}

void dl_add_thread(int id, const char *name, int priority, int64_t period_ns,
                   int64_t deadline_ns)
{
    pthread_mutex_lock(&lock);
    if (nthreads < DL_MAX_THREADS) {
        struct dl_thread *th = &threads[nthreads++];

        th->id = id;
        snprintf(th->name, sizeof th->name, "%s", name ? name : "");
        th->priority = priority;
        th->period_ns = period_ns;
        th->deadline_ns = deadline_ns;
    }
    pthread_mutex_unlock(&lock);
}

void dl_log(int64_t t_ns, const char *type, int thread_id, int job)
{
    pthread_mutex_lock(&lock);
    if (nevents < DL_MAX_EVENTS) {
        struct dl_event *ev = &events[nevents++];

        ev->t_ns = t_ns;
        snprintf(ev->type, sizeof ev->type, "%s", type ? type : "");
        ev->thread_id = thread_id;
        ev->job = job;
    }
    pthread_mutex_unlock(&lock);
}

static void json_escape(FILE *fp, const char *s)
{
    if (!s)
        s = "";
    fputc('"', fp);
    for (; *s; s++) {
        if (*s == '\\' || *s == '"') {
            fputc('\\', fp);
            fputc(*s, fp);
        } else if (*s == '\n') {
            fputs("\\n", fp);
        } else {
            fputc(*s, fp);
        }
    }
    fputc('"', fp);
}

int dl_write_json(const char *path, const char *source, const char *qnx_version,
                  const char *target, const char *toolchain)
{
    FILE *fp;
    struct utsname u;
    int i;
    const char *sysname = "";
    const char *release = "";
    const char *version = "";
    const char *machine = "";

    if (!path)
        return -1;
    memset(&u, 0, sizeof u);
    if (uname(&u) == 0) {
        sysname = u.sysname;
        release = u.release;
        version = u.version;
        machine = u.machine;
    }

    fp = fopen(path, "w");
    if (!fp)
        return -errno;

    pthread_mutex_lock(&lock);
    fputs("{\n", fp);
    fputs("  \"format\": \"deadlinelens-trace/v1\",\n", fp);
    fputs("  \"clock_hz\": 1000000000,\n", fp);
    fputs("  \"source\": ", fp);
    json_escape(fp, source);
    fputs(",\n  \"qnx_version\": ", fp);
    json_escape(fp, qnx_version);
    fputs(",\n  \"target\": ", fp);
    json_escape(fp, target);
    fputs(",\n  \"toolchain\": ", fp);
    json_escape(fp, toolchain);
    fputs(",\n  \"qnx\": {\n", fp);
    fputs("    \"version\": ", fp);
    json_escape(fp, qnx_version);
    fputs(",\n    \"target\": ", fp);
    json_escape(fp, target);
    fputs(",\n    \"toolchain\": ", fp);
    json_escape(fp, toolchain);
    fputs(",\n    \"uname_sysname\": ", fp);
    json_escape(fp, sysname);
    fputs(",\n    \"uname_release\": ", fp);
    json_escape(fp, release);
    fputs(",\n    \"uname_version\": ", fp);
    json_escape(fp, version);
    fputs(",\n    \"uname_machine\": ", fp);
    json_escape(fp, machine);
    fputs(",\n    \"sched_note\": \"SCHED_FIFO requested for sensor and control threads.\"\n", fp);
    fputs("  },\n", fp);
    fputs("  \"threads\": [\n", fp);
    for (i = 0; i < nthreads; i++) {
        fprintf(fp,
                "    {\"id\": %d, \"name\": ", threads[i].id);
        json_escape(fp, threads[i].name);
        fprintf(fp,
                ", \"priority\": %d, \"period_ns\": %lld, \"deadline_ns\": %lld}%s\n",
                threads[i].priority,
                (long long)threads[i].period_ns,
                (long long)threads[i].deadline_ns,
                (i + 1 < nthreads) ? "," : "");
    }
    fputs("  ],\n", fp);
    fputs("  \"events\": [\n", fp);
    for (i = 0; i < nevents; i++) {
        fprintf(fp,
                "    {\"t_ns\": %lld, \"type\": ",
                (long long)events[i].t_ns);
        json_escape(fp, events[i].type);
        fprintf(fp, ", \"thread_id\": %d, \"job\": %d}%s\n",
                events[i].thread_id, events[i].job,
                (i + 1 < nevents) ? "," : "");
    }
    fputs("  ]\n}\n", fp);
    pthread_mutex_unlock(&lock);

    if (fclose(fp) != 0)
        return -errno;
    return 0;
}

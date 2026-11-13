# QNX 8.0 target demo. Source qnxsdp-env.sh first so qcc is on PATH.
# Verified compile line (same as notes/build-run-note.md):
#   qcc -Vgcc_ntox86_64 -Wall -Wextra -O2 \
#       -DTOOLCHAIN_STRING='"qcc -Vgcc_ntox86_64"' \
#       -o periodic_task periodic_task.c deadline_trace.c

CC ?= qcc
VFLAG ?= -Vgcc_ntox86_64
CFLAGS ?= $(VFLAG) -Wall -Wextra -O2 -DTOOLCHAIN_STRING='"qcc -Vgcc_ntox86_64"'
TARGET = periodic_task
SRCS = periodic_task.c deadline_trace.c

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SRCS) deadline_trace.h
	$(CC) $(CFLAGS) -o $@ $(SRCS)

clean:
	rm -f $(TARGET) *.o

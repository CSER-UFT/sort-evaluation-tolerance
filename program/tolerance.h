#ifndef TOLERANCE_H
#define TOLERANCE_H

#include <stdlib.h>
#include <time.h>

#ifndef TOL_DEFAULT_DELTA
#define TOL_DEFAULT_DELTA 0
#endif

static int tol_delta = TOL_DEFAULT_DELTA;

static double tol_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static void tol_init(void) {
    const char *s = getenv("SORT_DELTA");
    if (s) {
        int d = atoi(s);
        tol_delta = (d > 0) ? d : 0;
    }
}

static inline int cmp_tol(int a, int b) {
    long diff = (long) a - (long) b;
    if (diff <= tol_delta && diff >= -tol_delta) return 0;
    return (diff < 0) ? -1 : 1;
}

static long long tol_count_inv(int *v, int *tmp, long lo, long hi) {
    if (hi - lo < 1) return 0;
    long mid = lo + (hi - lo) / 2;
    long long inv = tol_count_inv(v, tmp, lo, mid) + tol_count_inv(v, tmp, mid + 1, hi);
    long i = lo, j = mid + 1, k = lo;
    while (i <= mid && j <= hi) {
        if (v[i] <= v[j]) tmp[k++] = v[i++];
        else { inv += mid - i + 1; tmp[k++] = v[j++]; }
    }
    while (i <= mid) tmp[k++] = v[i++];
    while (j <= hi) tmp[k++] = v[j++];
    for (k = lo; k <= hi; k++) v[k] = tmp[k];
    return inv;
}

static void tol_report(const int *a, long n, double seconds) {
    if (!getenv("SORT_METRICS") || n <= 0) return;

    long desc = 0;
    long max_err = 0;
    int prefix_max = a[0];
    for (long i = 1; i < n; i++) {
        if (a[i - 1] > a[i]) desc++;
        if ((long) prefix_max - a[i] > max_err) max_err = (long) prefix_max - a[i];
        if (a[i] > prefix_max) prefix_max = a[i];
    }

    int *tails = malloc(n * sizeof(int));
    int *copy = malloc(n * sizeof(int));
    int *tmp = malloc(n * sizeof(int));
    if (!tails || !copy || !tmp) { free(tails); free(copy); free(tmp); return; }
    long len = 0;
    for (long i = 0; i < n; i++) {
        long lo = 0, hi = len;
        while (lo < hi) {
            long mid = (lo + hi) / 2;
            if (tails[mid] <= a[i]) lo = mid + 1; else hi = mid;
        }
        tails[lo] = a[i];
        if (lo == len) len++;
    }

    for (long i = 0; i < n; i++) copy[i] = a[i];
    long long inv = tol_count_inv(copy, tmp, 0, n - 1);

    printf("TOL delta=%d n=%ld time=%.6f rem=%ld inv=%lld desc=%ld max_err=%ld\n",
           tol_delta, n, seconds, n - len, inv, desc, max_err);
    free(tails); free(copy); free(tmp);
}

#endif

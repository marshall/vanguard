#include <glib.h>
#include <math.h>
#include <stdio.h>

// reference voltage in millivolts
#define REF_VOLTAGE           3300
#define SERIAL_RESISTOR       10000.0f
#define BCOEFFICIENT          3950.0f
#define THERMISTOR_NOMINAL    10000.0f
#define KELVIN_TO_C           273.15f
#define TEMPERATURE_NOMINAL_K (25.0f + KELVIN_TO_C)

static float calc_temp(float value) {
    float reading, steinhart;

    reading = SERIAL_RESISTOR / (value / 1800.0f);

    steinhart = reading / THERMISTOR_NOMINAL;
    steinhart = log(steinhart);
    steinhart /= BCOEFFICIENT;
    steinhart += 1.0f / TEMPERATURE_NOMINAL_K;

    return (1.0f / steinhart) - KELVIN_TO_C;
}

static gboolean read_temps(gpointer data) {
    printf("1024 mV: %0.1f C\n", calc_temp(1024.0f));
    printf("1800 mV: %0.1f C\n", calc_temp(2048.0f));
    return TRUE;
}

int main(int argc, gchar **argv) {
    GMainLoop *main_loop = NULL;
    main_loop = g_main_loop_new(NULL, FALSE);

    g_timeout_add_seconds(1, read_temps, NULL);
    g_main_loop_run(main_loop);
    return 0;
}

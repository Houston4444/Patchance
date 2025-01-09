#include <stdio.h>
#include <stdint.h>
#include <jack/jack.h>

jack_port_t *main_port;

void set_jack_port(jack_port_t *jack_port){
    main_port = jack_port;
}

int process_cb(uint32_t frames, void *arg){
    // printf("framesas %lu\n", frames);
    if (main_port != NULL){ return 0;}

    jack_default_audio_sample_t *in;

    in = jack_port_get_buffer(main_port, frames);

    for (int i=0; i < frames; i++){
        printf("todou %d %.2f\n", i, in[i]);
    }

    return 0;
 }


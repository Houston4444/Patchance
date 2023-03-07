 

from pyalsa import alsaseq
from time import sleep

seq = alsaseq.Sequencer(clientname='testing')

input_id = seq.create_simple_port(
    name='input',
    type=alsaseq.SEQ_PORT_TYPE_MIDI_GENERIC|alsaseq.SEQ_PORT_TYPE_APPLICATION,
    caps=alsaseq.SEQ_PORT_CAP_WRITE|alsaseq.SEQ_PORT_CAP_SUBS_WRITE|
    alsaseq.SEQ_PORT_CAP_SYNC_WRITE)

seq.connect_ports((alsaseq.SEQ_CLIENT_SYSTEM, alsaseq.SEQ_PORT_SYSTEM_ANNOUNCE), (seq.client_id, input_id))

while True:
    event_list = seq.receive_events(timeout=1024, maxevents=1)
    for event in event_list:
        data = event.get_data()
        if event.type == alsaseq.SEQ_EVENT_CLIENT_START:
            print('client started')
        elif event.type == alsaseq.SEQ_EVENT_CLIENT_EXIT:
            print('client exited')
        elif event.type == alsaseq.SEQ_EVENT_PORT_START:
            print('port created')
        elif event.type == alsaseq.SEQ_EVENT_PORT_EXIT:
            print('port destroyed')
        elif event.type == alsaseq.SEQ_EVENT_PORT_SUBSCRIBED:
            print('port connected')
            print(data)
        elif event.type == alsaseq.SEQ_EVENT_PORT_UNSUBSCRIBED:
            print('port disconnected')

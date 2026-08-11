
def group_belongs_to_client(group_name: str, jack_client_name: str) -> bool:
    if group_name == jack_client_name:
        return True

    if group_name.startswith(jack_client_name + '/'):
        return True

    if (group_name.startswith(jack_client_name + ' (')
            and group_name.endswith(')')):
        # Non-Mixer way
        return True

    if group_name == jack_client_name + '-midi':
        # Hydrogen specific
        return True

    return False


class NsmClient:
    executable = ''
    name = ''
    has_optional_gui = False
    gui_visible = False
    icon = ''


class NsmClients(dict[str, NsmClient]):
    def client_for_jack_group(
            self, group_name: str) -> tuple[str, NsmClient] | None:
        for client_id, nsm_client in self.items():
            if group_belongs_to_client(
                    group_name, f'{nsm_client.name}.{client_id}'):
                return client_id, nsm_client

nsm_clients = NsmClients()
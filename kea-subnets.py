#!/usr/bin/env python3

from sys import stdout
import pynetbox
import click
import netaddr
import json
import yaml
import jinja2
import dotenv

dotenv.load_dotenv()

def filter_host_ip(value, hostnum=0):
    return netaddr.IPNetwork(value)[hostnum]

def filter_ip(value):
    return netaddr.IPNetwork(value).ip

@click.command
@click.option('--url', envvar='NETBOX_URL', show_default='NETBOX_URL', required=True, help='Netbox base URL')
@click.option('--token', envvar='NETBOX_TOKEN', show_default='NETBOX_TOKEN', required=True, help='Netbox API Token')
@click.option('--parent-prefix', default='0.0.0.0/0', show_default=True, help='Parent prefix (IPv4 or IPv6)')
@click.option('--ip-range-role', default='dhcp-pool', show_default=True, help='Role slug for DHCP IP ranges')
@click.option('--config', help='Kea config file')
@click.option('--template-path', default='./templates', show_default=True, 
    help='Template search path. Must contain "subnet.yaml.j2".')
def main(url, token, parent_prefix, ip_range_role, config, template_path):
    _parent_prefix = netaddr.IPNetwork(parent_prefix)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path),
        autoescape=jinja2.select_autoescape(),
    )
    env.filters['host_ip'] = filter_host_ip
    env.filters['ip'] = filter_ip

    nb = pynetbox.api(url, token)
    prefixes = nb.ipam.prefixes.filter(status='active', within=parent_prefix)
    ip_ranges = list(nb.ipam.ip_ranges.filter(status='active', role=ip_range_role))
    ip_addresses = list(nb.ipam.ip_addresses.filter(status='dhcp', parent=parent_prefix))
    subnets = []

    for prefix in prefixes:
        _prefix = netaddr.IPNetwork(prefix.prefix)
        pools = []
        reservations = []

        for ip_range in filter(lambda r : netaddr.IPNetwork(r.start_address).ip in _prefix, ip_ranges):
            pools.append(ip_range)
        for ip_address in filter(lambda a : netaddr.IPNetwork(a.address).ip in _prefix, ip_addresses):
            reservations.append(ip_address)
        
        subnet_template = env.get_template('subnet.yaml.j2')
        subnets.append(yaml.safe_load(subnet_template.render(
            prefix=prefix,
            pools=pools,
            reservations=reservations
        )))
    
    if (config):
        config_json = yaml.safe_load(open(config, 'r'))
        
        if _parent_prefix.version == 4:
            config_json['Dhcp4']['subnet4'] = subnets
        elif _parent_prefix.version == 6:
            config_json['Dhcp6']['subnet6'] = subnets
        json.dump(config_json, stdout, indent=2)

    else:
        json.dump(subnets, stdout, indent=2)

if __name__ == '__main__':
    main()
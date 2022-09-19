# Configure Kea DHCP Subnets using Netbox

[![Build Docker Image](https://github.com/michaelkoetter/netbox-kea-subnets/actions/workflows/build-image.yml/badge.svg)](https://github.com/michaelkoetter/netbox-kea-subnets/actions/workflows/build-image.yml)
[![image-version](https://img.shields.io/static/v1?logo=docker&label=Docker+Hub&message=mkoetter/netbox-kea-subnets&color=informational)](https://hub.docker.com/r/mkoetter/netbox-kea-subnets)

This script fetches data from Netbox to create Kea subnet configuration from Prefixes, IP Ranges and IP Addresses.

A Jinja2 template is used to render each subnet. It can be customized to add additional data, e.g. from Netbox custom fields (see example in `templates`).

## Docker Images

Docker Images are automatically built for new releases.

```bash
docker run --rm mkoetter/netbox-kea-subnets:latest --help
```

## Development

```bash
python3 -m venv venv/
source venv/bin/activate
pip3 install -r requirements.txt
```

## Usage

> The script prints the generated configuration to `stdout`, it never updates config files directly.
> You should always test the generated config (ie. `kea-dhcp4 -t /tmp/config.json`) before activating it.

### Netbox URL and API Token (`--url`, `--token`)

Set the Netbox URL and API token using the environment variables `NETBOX_URL` and `NETBOX_TOKEN`,
or pass the `--url` and `--token` arguments on invocation.

### Prefix Filter (`--parent-prefix`)

Netbox Prefixes (which represent Kea Subnets) can be selected using the `--parent-prefix` flag. 
This also determines the address family - IPv4 or IPv6 - of the subnets.

`0.0.0.0/0` (the default) or `::/0` can be used to select all subnets.

Examples:
- `--parent-prefix 192.168.0.0/16`
- `--parent-prefix 2001:db8:1::/48`

### IP Range Filter (`--ip-range-role`)

Netbox IP Ranges (which represent Kea Pools) are filtered using roles. Specify the slug of the role you want to use for DHCP ranges,
e.g. if the role is called "DHCP Pool" the default slug would be `dhcp-pool`. 

### IP Addresses

Netbox IP Addresses are used for Kea reservations. The addresses must have status `DHCP` in Netbox, and they should be assigned to an interface with a MAC address (although client identification could be customized in the subnet template).

### DHCP Options

The default subnet template uses to following Netbox custom fields to add DHCP options (`option-data`) to subnets, pools and reservations:

- `dhcp_default_gateway` - IP Address
- `dhcp_dns_servers` - List of IP Addresses
- `dhcp_domain` - Text
- `dhcp_mtu` - Integer
- `dhcp_ntp_servers` - List of IP Addresses
- `dhcp_option_data` - JSON, custom `option-data` for options not covered above

### Merge With Existing Config (`--config`)

You can specify an existing `Dhcp4` or `Dhcp6` config file (must match the address family of `--parent-prefix`!)
to generate a new configuration with updated `subnet4`/`subnet6` attributes.

> The specified config file must not include comments, ie. it must be a standard JSON file!

If this is omitted, the script just generates the subnet list.

## Examples

Generate subnets within 192.168.0.0/16:
```bash
python3 kea-subnets.py --parent-prefix 192.168.0.0/16
```

Update existing config with subnets within 192.168.0.0/16:
```bash
python3 kea-subnets.py --config example-dhcp4.json --parent-prefix 192.168.0.0/16
```

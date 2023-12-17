#!/bin/bash
iptables -A FORWARD -i ctfuser -o eth1 -j LOG --log-prefix "ctfdfwlog"
iptables -A FORWARD -i ctfuser -o tunnel -j LOG --log-prefix "ctfdfwlog"

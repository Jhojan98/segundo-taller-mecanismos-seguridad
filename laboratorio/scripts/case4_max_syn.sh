#!/bin/bash
# case4_max_syn.sh /captures/X.pcap -> máximo de SYN (sin ACK) en una ventana de 5 s (para calibrar la regla Suricata)
tshark -r "$1" -Y 'tcp.flags.syn==1 && tcp.flags.ack==0' -T fields -e frame.time_relative \
  | awk -v f="$1" '{b=int($1/5); c[b]++} END{m=0; for(k in c) if(c[k]>m) m=c[k]; print f, "max SYN/5s:", m}'
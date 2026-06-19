# Fixed-size benchmark message. Only plain, fixed-width fields (no strings or
# unbounded sequences), so it qualifies for DDS zero-copy shared memory
# (CycloneDDS/Iceoryx loaning, Fast DDS data-sharing). 64 KiB payload is large
# enough for zero-copy to matter and stays under the AF_UNIX datagram cap.
int64 send_ns
int64 seq
uint8[65536] payload

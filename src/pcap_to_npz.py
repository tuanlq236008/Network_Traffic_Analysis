import os
import subprocess
import numpy as np
from multiprocessing import Pool
import json
import time
from tqdm import tqdm
import struct
import socket

NUM_WORKERS = 8
TSHARK_PATH = "/Applications/Wireshark.app/Contents/MacOS/tshark"

def parse_pcapng_data(f):
    # Peek at BOM at offset 8 to determine endianness
    f.seek(8)
    bom = f.read(4)
    f.seek(0)
    if bom == b'\x1a\x2b\x3c\x4d':
        endian = '>'
    else:
        endian = '<'
        
    packets = []
    link_type = 1
    time_resolution = 1e6
    first_ts = None
    
    while True:
        header = f.read(8)
        if len(header) < 8:
            break
        block_type, block_len = struct.unpack(endian + 'II', header)
        if block_len < 12 or block_len > 16 * 1024 * 1024:
            break
        
        body_len = block_len - 8
        body = f.read(body_len)
        if len(body) < body_len:
            break
        
        if block_type == 0x00000001: # IDB (Interface Description Block)
            link_type = struct.unpack(endian + 'H', body[0:2])[0]
            options_data = body[16:-4]
            offset = 0
            while offset + 4 <= len(options_data):
                opt_code, opt_len = struct.unpack(endian + 'HH', options_data[offset:offset+4])
                if opt_code == 0:
                    break
                if opt_code == 9:
                    tsresol = options_data[offset+4]
                    if tsresol & 0x80:
                        time_resolution = float(2**(tsresol & 0x7F))
                    else:
                        time_resolution = float(10**tsresol)
                offset += 4 + opt_len
                if opt_len % 4 != 0:
                    offset += 4 - (opt_len % 4)
        elif block_type == 0x00000006: # EPB (Enhanced Packet Block)
            if link_type != 1:
                continue
            ts_high, ts_low, cap_len, orig_len = struct.unpack(endian + 'IIII', body[4:20])
            ts = ((ts_high << 32) + ts_low) / time_resolution
            data = body[20:20+cap_len]
            if len(data) < 14:
                continue
            eth_type = struct.unpack('>H', data[12:14])[0]
            ip_data = data[14:]
            
            src_ip = ""
            dst_ip = ""
            src_port = ""
            dst_port = ""
            
            if eth_type == 0x0800:
                if len(ip_data) >= 20:
                    version_ihl = ip_data[0]
                    ihl = (version_ihl & 0x0F) * 4
                    protocol = ip_data[9]
                    src_ip = socket.inet_ntop(socket.AF_INET, ip_data[12:16])
                    dst_ip = socket.inet_ntop(socket.AF_INET, ip_data[16:20])
                    l4_data = ip_data[ihl:]
                    if protocol == 6:
                        if len(l4_data) >= 4:
                            src_port = str(struct.unpack('>H', l4_data[0:2])[0])
                            dst_port = str(struct.unpack('>H', l4_data[2:4])[0])
                    elif protocol == 17:
                        if len(l4_data) >= 4:
                            src_port = str(struct.unpack('>H', l4_data[0:2])[0])
                            dst_port = str(struct.unpack('>H', l4_data[2:4])[0])
            elif eth_type == 0x86DD:
                if len(ip_data) >= 40:
                    next_header = ip_data[6]
                    src_ip = socket.inet_ntop(socket.AF_INET6, ip_data[8:24])
                    dst_ip = socket.inet_ntop(socket.AF_INET6, ip_data[24:40])
                    l4_data = ip_data[40:]
                    if next_header == 6:
                        if len(l4_data) >= 4:
                            src_port = str(struct.unpack('>H', l4_data[0:2])[0])
                            dst_port = str(struct.unpack('>H', l4_data[2:4])[0])
                    elif next_header == 17:
                        if len(l4_data) >= 4:
                            src_port = str(struct.unpack('>H', l4_data[0:2])[0])
                            dst_port = str(struct.unpack('>H', l4_data[2:4])[0])
            
            if first_ts is None:
                first_ts = ts
            rel_time = ts - first_ts
            packets.append((rel_time, src_ip, dst_ip, src_port, dst_port, orig_len))
    return packets

def parse_pcap_data(f, magic):
    global_header = f.read(24)
    if len(global_header) < 24:
        return None
    if magic == b'\xa1\xb2\xc3\xd4':
        endian = '>'
    elif magic == b'\xd4\xc3\xb2\xa1':
        endian = '<'
    elif magic == b'\xa1\xb2\x3c\x4d' or magic == b'\x4d\x3c\xb2\xa1':
        endian = '<'
    else:
        return None
    
    link_type = struct.unpack(endian + 'I', global_header[20:24])[0]
    if link_type != 1:
        return []
        
    packets = []
    first_ts = None
    while True:
        header = f.read(16)
        if len(header) < 16:
            break
        ts_sec, ts_usec, incl_len, orig_len = struct.unpack(endian + 'IIII', header)
        data = f.read(incl_len)
        if len(data) < incl_len:
            break
        if len(data) < 14:
            continue
        
        eth_type = struct.unpack('>H', data[12:14])[0]
        ip_data = data[14:]
        
        src_ip = ""
        dst_ip = ""
        src_port = ""
        dst_port = ""
        
        if eth_type == 0x0800:
            if len(ip_data) >= 20:
                version_ihl = ip_data[0]
                ihl = (version_ihl & 0x0F) * 4
                protocol = ip_data[9]
                src_ip = socket.inet_ntop(socket.AF_INET, ip_data[12:16])
                dst_ip = socket.inet_ntop(socket.AF_INET, ip_data[16:20])
                l4_data = ip_data[ihl:]
                if protocol == 6:
                    if len(l4_data) >= 4:
                        src_port = str(struct.unpack('>H', l4_data[0:2])[0])
                        dst_port = str(struct.unpack('>H', l4_data[2:4])[0])
                elif protocol == 17:
                    if len(l4_data) >= 4:
                        src_port = str(struct.unpack('>H', l4_data[0:2])[0])
                        dst_port = str(struct.unpack('>H', l4_data[2:4])[0])
        elif eth_type == 0x86DD:
            if len(ip_data) >= 40:
                next_header = ip_data[6]
                src_ip = socket.inet_ntop(socket.AF_INET6, ip_data[8:24])
                dst_ip = socket.inet_ntop(socket.AF_INET6, ip_data[24:40])
                l4_data = ip_data[40:]
                if next_header == 6:
                    if len(l4_data) >= 4:
                        src_port = str(struct.unpack('>H', l4_data[0:2])[0])
                        dst_port = str(struct.unpack('>H', l4_data[2:4])[0])
                elif next_header == 17:
                    if len(l4_data) >= 4:
                        src_port = str(struct.unpack('>H', l4_data[0:2])[0])
                        dst_port = str(struct.unpack('>H', l4_data[2:4])[0])
        
        ts = ts_sec + ts_usec / 1e6
        if first_ts is None:
            first_ts = ts
        rel_time = ts - first_ts
        packets.append((rel_time, src_ip, dst_ip, src_port, dst_port, orig_len))
    return packets

def parse_pcap_or_pcapng(filepath):
    try:
        with open(filepath, 'rb') as f:
            magic = f.read(4)
            if len(magic) < 4:
                return None
            f.seek(0)
            if magic == b'\x0a\x0d\x0d\x0a':
                return parse_pcapng_data(f)
            elif magic in (b'\xa1\xb2\xc3\xd4', b'\xd4\xc3\xb2\xa1', b'\xa1\xb2\x3c\x4d', b'\x4d\x3c\xb2\xa1'):
                return parse_pcap_data(f, magic)
            else:
                return None
    except Exception:
        return None

def process_pcap(args):
    file_path, label = args
    
    # Try custom parser first
    packets = parse_pcap_or_pcapng(file_path)
    
    if packets is not None and len(packets) > 0:
        dir_seq = np.zeros(5000, dtype=np.int8)
        time_seq = np.zeros(5000, dtype=np.float32)
        length_seq = np.zeros(5000, dtype=np.float32)
        total_time = 0.0
        total_incoming = 0
        total_outgoing = 0
        packet_num = 0
        
        # First pass: Discover all client IP addresses
        client_ips = set()
        for rel_time, src_ip, dst_ip, src_port, dst_port, orig_len in packets:
            if dst_port in ("443", "80", "53") or src_port in ("443", "80", "53"):
                if dst_port in ("443", "80", "53") and src_ip:
                    client_ips.add(src_ip)
                if src_port in ("443", "80", "53") and dst_ip:
                    client_ips.add(dst_ip)

        if not client_ips:
            for rel_time, src_ip, dst_ip, src_port, dst_port, orig_len in packets:
                if src_ip and (src_ip.startswith("192.168.") or src_ip.startswith("10.") or src_ip.startswith("172.") or src_ip.startswith("fe80:")):
                    client_ips.add(src_ip)

        # Second pass: Extract features
        for rel_time, src_ip, dst_ip, src_port, dst_port, orig_len in packets:
            if not src_ip:
                continue
                
            if src_ip in client_ips:
                curr_dir = 1  # Outgoing
                total_outgoing += 1
            else:
                curr_dir = -1 # Incoming
                total_incoming += 1
                
            if packet_num < 5000:
                dir_seq[packet_num] = curr_dir
                time_seq[packet_num] = rel_time
                length_seq[packet_num] = orig_len
                
            packet_num += 1
            total_time = rel_time
            
        total_packets = total_incoming + total_outgoing
        if total_packets == 0:
            metadata = np.zeros(7, dtype=np.float32)
        else:
            metadata = np.array([total_packets, total_incoming, total_outgoing,
                                 total_incoming / total_packets,
                                 total_outgoing / total_packets,
                                 total_time, total_time / total_packets],
                                dtype=np.float32)
                                
        return dir_seq, time_seq, length_seq, metadata, label

    # Fallback to tshark
    cmd = [
        TSHARK_PATH,
        "-r", file_path,
        "-n",
        "-T", "fields",
        "-e", "frame.time_relative",
        "-e", "ip.src",
        "-e", "ipv6.src",
        "-e", "ip.dst",
        "-e", "ipv6.dst",
        "-e", "tcp.srcport",
        "-e", "tcp.dstport",
        "-e", "udp.srcport",
        "-e", "udp.dstport",
        "-e", "frame.len"
    ]
    
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

    if proc.returncode != 0:
        print(f"tshark failed for {file_path}: {err.strip()}")
        return None
        
    lines = out.strip().split('\n')
    
    dir_seq = np.zeros(5000, dtype=np.int8)
    time_seq = np.zeros(5000, dtype=np.float32)
    length_seq = np.zeros(5000, dtype=np.float32)
    total_time = 0.0
    total_incoming = 0
    total_outgoing = 0
    packet_num = 0
    
    # First pass: Discover all client IP addresses
    client_ips = set()
    for line in lines:
        if not line: continue
        parts = line.split('\t')
        if len(parts) < 1: continue
        
        src = parts[1].strip() if len(parts) > 1 and parts[1].strip() else (parts[2].strip() if len(parts) > 2 else "")
        dst = parts[3].strip() if len(parts) > 3 and parts[3].strip() else (parts[4].strip() if len(parts) > 4 else "")
        tcp_src = parts[5].strip() if len(parts) > 5 else ""
        tcp_dst = parts[6].strip() if len(parts) > 6 else ""
        udp_src = parts[7].strip() if len(parts) > 7 else ""
        udp_dst = parts[8].strip() if len(parts) > 8 else ""
        
        if tcp_dst in ("443", "80", "53") or udp_dst in ("443", "80", "53"):
            if src: client_ips.add(src)
        if tcp_src in ("443", "80", "53") or udp_src in ("443", "80", "53"):
            if dst: client_ips.add(dst)

    if not client_ips:
        for line in lines:
            if not line: continue
            parts = line.split('\t')
            src = parts[1].strip() if len(parts) > 1 and parts[1].strip() else (parts[2].strip() if len(parts) > 2 else "")
            if src and (src.startswith("192.168.") or src.startswith("10.") or src.startswith("172.") or src.startswith("fe80:")):
                client_ips.add(src)

    # Second pass: Extract features
    for line in lines:
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) < 1:
            continue
            
        try:
            curr_time = float(parts[0])
        except ValueError:
            continue
            
        src = parts[1].strip() if len(parts) > 1 and parts[1].strip() else (parts[2].strip() if len(parts) > 2 else "")
        
        if not src:
            continue # Skip packets without IP layer
            
        if src in client_ips:
            curr_dir = 1  # Outgoing
            total_outgoing += 1
        else:
            curr_dir = -1 # Incoming
            total_incoming += 1
            
        if packet_num < 5000:
            dir_seq[packet_num] = curr_dir
            time_seq[packet_num] = curr_time
            curr_len = float(parts[9].strip()) if len(parts) > 9 and parts[9].strip() else 0.0
            length_seq[packet_num] = curr_len
            
        packet_num += 1
        total_time = curr_time
        
    total_packets = total_incoming + total_outgoing
    if total_packets == 0:
        metadata = np.zeros(7, dtype=np.float32)
    else:
        metadata = np.array([total_packets, total_incoming, total_outgoing,
                             total_incoming / total_packets,
                             total_outgoing / total_packets,
                             total_time, total_time / total_packets],
                            dtype=np.float32)
                            
    return dir_seq, time_seq, length_seq, metadata, label

def main():
    with open('config.json') as f:
        config = json.load(f)
        
    data_dir = config['data_dir']
    
    classes = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    classes.sort()
    
    num_mon_inst = config['num_mon_inst_train'] + config['num_mon_inst_test']
    
    arg_list = []
    for label, cls in enumerate(classes):
        cls_dir = os.path.join(data_dir, cls)
        files = sorted(os.listdir(cls_dir))
        count = 0
        for f in files:
            if f.endswith('.pcap'):
                arg_list.append((os.path.join(cls_dir, f), label))
                count += 1
                if count >= num_mon_inst:
                    break
                
    print(f"Total PCAP files to process: {len(arg_list)}")
    
    start_time = time.time()
    
    print(f"Using {NUM_WORKERS} parallel tshark workers")

    with Pool(processes=NUM_WORKERS) as pool:
        results = list(tqdm(
            pool.imap_unordered(process_pcap, arg_list, chunksize=1),
            total=len(arg_list)
        ))
        
    print(f"Finished processing in {time.time() - start_time:.2f} seconds")
    
    # Filter out any failed processing
    results = [r for r in results if r is not None]
    
    dir_seq_mon = np.array([r[0] for r in results], dtype=np.int8)
    time_seq_mon = np.array([r[1] for r in results], dtype=np.float32)
    length_seq_mon = np.array([r[2] for r in results], dtype=np.float32)
    metadata_mon = np.array([r[3] for r in results], dtype=np.float32)
    labels_mon = np.array([r[4] for r in results])
    
    print(f"Saving {len(labels_mon)} monitored traces...")
    np.savez_compressed(os.path.join(data_dir, 'all_closed_world.npz'), 
                        dir_seq=dir_seq_mon, time_seq=time_seq_mon, 
                        length_seq=length_seq_mon,
                        metadata=metadata_mon, labels=labels_mon)
                        
    print(f"Saving empty unmonitored traces...")
    np.savez_compressed(os.path.join(data_dir, 'all_open_world.npz'), 
                        dir_seq=np.empty((0, 5000), dtype=np.int8), 
                        time_seq=np.empty((0, 5000), dtype=np.float32), 
                        length_seq=np.empty((0, 5000), dtype=np.float32),
                        metadata=np.empty((0, 7), dtype=np.float32), 
                        labels=np.empty((0,), dtype=np.int32))
                        
    print("Done!")

if __name__ == '__main__':
    main()

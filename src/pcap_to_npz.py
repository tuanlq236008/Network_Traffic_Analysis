import os
import subprocess
import numpy as np
from multiprocessing import Pool
import json
import time
from tqdm import tqdm

NUM_WORKERS = 8
TSHARK_PATH = "/Applications/Wireshark.app/Contents/MacOS/tshark"

def process_pcap(args):
    file_path, label = args
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
        "-e", "udp.dstport"
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
                            
    return dir_seq, time_seq, metadata, label

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
    metadata_mon = np.array([r[2] for r in results], dtype=np.float32)
    labels_mon = np.array([r[3] for r in results])
    
    print(f"Saving {len(labels_mon)} monitored traces...")
    np.savez_compressed(os.path.join(data_dir, 'all_closed_world.npz'), 
                        dir_seq=dir_seq_mon, time_seq=time_seq_mon, 
                        metadata=metadata_mon, labels=labels_mon)
                        
    print(f"Saving empty unmonitored traces...")
    np.savez_compressed(os.path.join(data_dir, 'all_open_world.npz'), 
                        dir_seq=np.empty((0, 5000), dtype=np.int8), 
                        time_seq=np.empty((0, 5000), dtype=np.float32), 
                        metadata=np.empty((0, 7), dtype=np.float32), 
                        labels=np.empty((0,), dtype=np.int32))
                        
    print("Done!")

if __name__ == '__main__':
    main()

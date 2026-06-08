import os
import sys
import json
import subprocess
import numpy as np
from sklearn.preprocessing import StandardScaler
from keras.models import Model
import var_cnn

def extract_pcap_features(pcap_path):
    """Run tshark on the single pcap file and extract features."""
    tshark_path = "/Applications/Wireshark.app/Contents/MacOS/tshark"
    if not os.path.exists(tshark_path):
        tshark_path = "tshark"
        
    cmd = [
        tshark_path,
        "-r", pcap_path,
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
        if proc.returncode != 0:
            print(f"Error running tshark: {err}")
            return None
    except Exception as e:
        print(f"Failed to run tshark command: {e}")
        return None
        
    lines = out.strip().split('\n')
    if not lines or lines == ['']:
        print("Error: No packets processed from PCAP file.")
        return None
        
    # First pass: Discover client IPs using port-based rules
    client_ips = set()
    for line in lines:
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) < 1:
            continue
            
        ip_src = parts[1].strip() if len(parts) > 1 else ""
        ipv6_src = parts[2].strip() if len(parts) > 2 else ""
        src = ip_src if ip_src else ipv6_src
        
        ip_dst = parts[3].strip() if len(parts) > 3 else ""
        ipv6_dst = parts[4].strip() if len(parts) > 4 else ""
        dst = ip_dst if ip_dst else ipv6_dst
        
        tcp_src = parts[5].strip() if len(parts) > 5 else ""
        tcp_dst = parts[6].strip() if len(parts) > 6 else ""
        udp_src = parts[7].strip() if len(parts) > 7 else ""
        udp_dst = parts[8].strip() if len(parts) > 8 else ""
        
        if tcp_dst in ("443", "80", "53") or udp_dst in ("443", "80", "53"):
            if src:
                client_ips.add(src)
        if tcp_src in ("443", "80", "53") or udp_src in ("443", "80", "53"):
            if dst:
                client_ips.add(dst)

    # Fallback to local subnet matching if no IPs discovered via port rules
    if not client_ips:
        for line in lines:
            if not line:
                continue
            parts = line.split('\t')
            ip_src = parts[1].strip() if len(parts) > 1 else ""
            ipv6_src = parts[2].strip() if len(parts) > 2 else ""
            src = ip_src if ip_src else ipv6_src
            if src:
                if src.startswith("192.168.") or src.startswith("10.") or src.startswith("172.") or src.startswith("fe80:"):
                    client_ips.add(src)

    # Second pass: Process packets and assign direction and relative times
    dir_seq = np.zeros(5000, dtype=np.int8)
    time_seq = np.zeros(5000, dtype=np.float32)
    total_time = 0.0
    total_incoming = 0
    total_outgoing = 0
    packet_num = 0
    
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
            
        ip_src = parts[1].strip() if len(parts) > 1 else ""
        ipv6_src = parts[2].strip() if len(parts) > 2 else ""
        src = ip_src if ip_src else ipv6_src
        
        if not src:
            continue
            
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
                            
    return dir_seq, time_seq, metadata

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 predict_single_pcap.py <path_to_pcap_file>")
        print("Example: python3 predict_single_pcap.py data/1967_20stingray/1967_20stingray_136.pcap")
        return
        
    pcap_path = sys.argv[1]
    if not os.path.exists(pcap_path):
        print(f"Error: File '{pcap_path}' does not exist.")
        return
        
    # 1. Load config
    with open('config.json') as f:
        config = json.load(f)
        
    data_dir = config['data_dir']
    
    # 2. Get class names
    classes = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    classes.sort()
    
    # 3. Extract features from the input PCAP file
    print(f"Analyzing and extracting features from '{pcap_path}'...")
    features = extract_pcap_features(pcap_path)
    if features is None:
        return
    dir_seq, time_seq, metadata = features
    
    # 4. Preprocess: Compute inter-arrival times if inter_time is True
    if config['inter_time']:
        inter_time_seq = np.zeros_like(time_seq)
        inter_time_seq[1:] = time_seq[1:] - time_seq[:-1]
        time_seq = inter_time_seq
        
    # Reshape sequences for CNN input
    dir_input = np.reshape(dir_seq, (1, 5000, 1))
    time_input = np.reshape(time_seq, (1, 5000, 1))
    
    # 5. Preprocess: Scale metadata
    if config['scale_metadata']:
        npz_path = os.path.join(data_dir, 'all_closed_world.npz')
        if os.path.exists(npz_path):
            npz_data = np.load(npz_path)
            all_metadata = npz_data['metadata']
            scaler = StandardScaler()
            scaler.fit(all_metadata)
            metadata_scaled = scaler.transform(np.reshape(metadata, (1, -1)))
        else:
            print("Warning: all_closed_world.npz not found. Skipping metadata scaling.")
            metadata_scaled = np.reshape(metadata, (1, -1))
    else:
        metadata_scaled = np.reshape(metadata, (1, -1))
        
    # Load and evaluate all ensemble components
    ensemble_predictions = []
    
    for mixture_num, inner_comb in enumerate(config['mixture']):
        sub_model_name = '_'.join(inner_comb)
        print(f"Building Var-CNN model for ensemble component: {sub_model_name}...")
        model, _ = var_cnn.get_model(config, mixture_num)
        
        # Load weights
        weights_path = f"model_{sub_model_name}.weights.h5"
        if not os.path.exists(weights_path):
            print(f"Error: Model weights '{weights_path}' not found!")
            return
            
        model.load_weights(weights_path)
        
        # Determine which inputs to pass
        model_inputs = []
        if 'dir' in inner_comb:
            model_inputs.append(dir_input)
        if 'time' in inner_comb:
            model_inputs.append(time_input)
        if 'metadata' in inner_comb:
            model_inputs.append(metadata_scaled)
            
        prediction = model.predict(model_inputs, verbose=0)[0]
        ensemble_predictions.append(prediction)
        
    # Compute ensemble prediction (simple average)
    ensemble_predictions = np.array(ensemble_predictions)
    prediction = np.mean(ensemble_predictions, axis=0)
    
    predicted_label = np.argmax(prediction)
    predicted_class = classes[predicted_label]
    confidence = prediction[predicted_label] * 100
    
    print("\n" + "=" * 60)
    print(f"RESULT FOR: {pcap_path}")
    print(f"Predicted Website: {predicted_class}")
    print(f"Model Confidence : {confidence:.2f}%")
    print("=" * 60)
    
    # Show top 3 predictions
    top_indices = np.argsort(prediction)[::-1][:3]
    print("\nTop 3 Candidate Websites:")
    for rank, idx in enumerate(top_indices, 1):
        print(f"  {rank}. {classes[idx]:<40} | probability: {prediction[idx]*100:>6.2f}%")

if __name__ == '__main__':
    main()

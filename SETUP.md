# Setup Guide - Hướng Dẫn Cài Đặt Chi Tiết

## 📦 Hệ Thống Yêu Cầu

- **Python**: 3.8 - 3.11
- **RAM**: Tối thiểu 8GB (khuyến nghị 16GB+)
- **Disk**: 50GB+ cho dữ liệu
- **GPU** (Optional): NVIDIA GPU với CUDA support

## 🖥️ Cài Đặt từng Bước

### macOS

#### 1. Cài Đặt Python

```bash
# Sử dụng Homebrew
brew install python@3.11

# Xác minh
python3 --version
```

#### 2. Cài Đặt Wireshark (tshark)

```bash
# Cài Wireshark
brew install wireshark

# Xác minh
which tshark
tshark --version
```

#### 3. Clone Repository

```bash
cd ~/Documents
git clone https://github.com/tuanlq236008/Network_Traffic_Analysis.git
cd Network_Traffic_Analysis
```

#### 4. Tạo Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 5. Cài Đặt Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Linux (Ubuntu/Debian)

#### 1. Cài Đặt Python

```bash
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev

python3.11 --version
```

#### 2. Cài Đặt Wireshark

```bash
sudo apt-get install wireshark tshark

# Cho phép user sử dụng tshark
sudo usermod -a -G wireshark $USER
newgrp wireshark
```

#### 3. Clone Repository

```bash
cd ~
git clone https://github.com/tuanlq236008/Network_Traffic_Analysis.git
cd Network_Traffic_Analysis
```

#### 4. Tạo Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

#### 5. Cài Đặt Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Windows

#### 1. Cài Đặt Python

- Tải Python từ https://www.python.org/downloads/
- Chạn "Add Python to PATH" trong installer
- Xác minh: `python --version`

#### 2. Cài Đặt Wireshark

- Tải từ https://www.wireshark.org/download/
- Chạy installer
- Tích chọn "WinPcap/Npcap" và "Wireshark" components
- Xác minh: `tshark --version` (từ Command Prompt)

#### 3. Clone Repository

```bash
cd Documents
git clone https://github.com/tuanlq236008/Network_Traffic_Analysis.git
cd Network_Traffic_Analysis
```

#### 4. Tạo Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

#### 5. Cài Đặt Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 🎮 GPU Support (Tuỳ Chọn)

### NVIDIA GPU with CUDA

```bash
# Cài CUDA 11.8
# Từ https://developer.nvidia.com/cuda-11-8-0-download-archive

# Cài cuDNN 8.x
# Từ https://developer.nvidia.com/cudnn

# Cài Tensorflow GPU
pip install tensorflow[and-cuda]>=2.13.0
```

### Xác Minh GPU

```python
python
>>> import tensorflow as tf
>>> tf.config.list_physical_devices('GPU')
# Sẽ hiển thị GPU devices
```

## 📝 Cấu Hình Ban Đầu

### 1. Copy Cấu Hình Mẫu

```bash
cp config.json.example config.json
```

### 2. Tạo Thư Mục Dữ Liệu

```bash
mkdir -p data
mkdir -p predictions
```

### 3. Chuẩn Bị Dữ Liệu PCAP

```bash
# Copy PCAP files vào thư mục data/
cp /path/to/*.pcap data/
```

## ✅ Kiểm Tra Cài Đặt

### Test 1: Kiểm Tra Python

```bash
python -c "import sys; print(f'Python {sys.version}')"
```

### Test 2: Kiểm Tra Dependencies

```bash
python -c "import tensorflow, keras, numpy, h5py, sklearn, tqdm; print('All libraries installed!')"
```

### Test 3: Kiểm Tra tshark

```bash
tshark --version
```

### Test 4: Kiểm Tra Script

```bash
cd src
python -c "import var_cnn, df, evaluate"
echo "Scripts can be imported successfully!"
```

## 🚀 Quick Start

```bash
# Kích hoạt environment
source venv/bin/activate  # macOS/Linux
# hoặc
venv\Scripts\activate  # Windows

# Chuyển đổi PCAP
cd src
python pcap_to_npz.py

# Tiền xử lý
python preprocess_data.py

# Huấn luyện
python run_model.py

# Xem kết quả
cat ../job_result.json
```

## 🔧 Troubleshooting

### Lỗi: "command not found: tshark"

**macOS**:
```bash
# Kiểm tra path của tshark
which tshark

# Nếu không tìm thấy, cài lại
brew uninstall wireshark
brew install wireshark

# Thêm vào PATH nếu cần
echo 'export PATH="/usr/local/opt/wireshark/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Linux**:
```bash
# Cài đặt lại tshark
sudo apt-get install --reinstall wireshark tshark
```

### Lỗi: "ModuleNotFoundError"

```bash
# Kiểm tra environment được kích hoạt
which python  # Phải là path trong venv

# Cài lại dependencies
pip install -r requirements.txt --force-reinstall
```

### Lỗi: "MemoryError"

- Giảm `batch_size` trong `config.json`
- Giảm `seq_length`
- Giảm số lượng mô hình trong `mixture`

### Lỗi: "CUDA/GPU not found"

```bash
# Xác minh TensorFlow thấy GPU
python -c "import tensorflow as tf; print(tf.config.list_physical_devices())"

# Nếu không có GPU, sử dụng CPU
# TensorFlow sẽ tự động fallback sang CPU
```

## 📞 Support

Nếu gặp vấn đề:

1. Kiểm tra [Issues](../../issues)
2. Tạo Issue mới với:
   - Python version
   - OS và version
   - Full error message
   - Setup steps bạn đã thực hiện

---

**Happy coding!** 🎉

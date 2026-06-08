# Network Traffic Analysis

Dự án này phân tích lưu lượng mạng iCloud Private Relay bằng phương pháp học sâu trên dữ liệu PCAP. Mục tiêu là sử dụng các đặc trưng hướng gói, thời gian và metadata để phân loại lưu lượng và đánh giá khả năng nhận diện lớp lưu lượng riêng tư.

Nó hỗ trợ hai kiến trúc chính:

- `var-cnn` – một mô hình ResNet 1D kết hợp các kênh `dir`, `time`, `metadata`
- `df` – mô hình Deep Fingerprinting (DF) chỉ dùng hướng gói tin

## Mục tiêu

- Chuyển đổi tệp PCAP thành dữ liệu đầu vào cho mạng nơ-ron
- Tiền xử lý và tạo bộ dữ liệu `.h5`
- Huấn luyện và đánh giá mô hình
- Xuất dự đoán và tính chỉ số hiệu suất

## Yêu cầu

- Python 3.x
- TensorFlow
- Keras
- h5py
- scikit-learn
- tqdm
- `tshark` (thuộc Wireshark)

Nội dung có sẵn trong `requirements.txt`.

## Cấu trúc thư mục chính

- `src/pcap_to_npz.py` – chuyển đổi PCAP sang `all_closed_world.npz` và `all_open_world.npz`
- `src/preprocess_data.py` – tiền xử lý dữ liệu và lưu trữ `.h5`
- `src/run_model.py` – huấn luyện, dự đoán và đánh giá mô hình
- `src/var_cnn.py` – kiến trúc Var-CNN và các callback
- `src/df.py` – kiến trúc Deep Fingerprinting
- `src/evaluate.py` – tính chỉ số TPR/FPR và ghi `job_result.json`
- `src/data_generator.py` – tạo batch dữ liệu an toàn cho nhiều luồng
- `src/wang_to_varcnn.py` – hỗ trợ chuyển đổi dữ liệu định dạng cũ sang định dạng Var-CNN
- `src/predic/` – các script dự đoán và kiểm tra riêng

## Cách dùng

### 1. Cài đặt môi trường

Chạy:

```bash
pip install -r requirements.txt
```

### 2. Chuẩn bị `config.json`

`src/run_model.py` và nhiều script khác đọc cấu hình từ `config.json` nằm ở thư mục gốc.
Bạn cần tạo file này với những trường sau:

```json
{
  "data_dir": "./data/",
  "predictions_dir": "./predictions/",
  "model_name": "var-cnn",
  "mixture": [["dir"], ["time"], ["metadata"], ["dir", "time", "metadata"]],
  "batch_size": 128,
  "var_cnn_max_epochs": 100,
  "df_epochs": 50,
  "num_mon_sites": 50,
  "num_mon_inst_train": 10,
  "num_mon_inst_test": 5,
  "num_unmon_sites_train": 10,
  "num_unmon_sites_test": 10,
  "seq_length": 5000,
  "inter_time": true,
  "scale_metadata": true,
  "dir_dilations": true,
  "time_dilations": true,
  "var_cnn_base_patience": 5
}
```

> Chú ý: thay đổi giá trị theo bộ dữ liệu và thử nghiệm của bạn.

### 3. Chuyển đổi PCAP thành NPZ

Chạy:

```bash
python src/pcap_to_npz.py
```

- Script này dùng `tshark` để giải mã file PCAP.
- Nếu `tshark` không nằm ở đường dẫn macOS mặc định, chỉnh `TSHARK_PATH` trong `src/pcap_to_npz.py`.

### 4. Tiền xử lý dữ liệu

Chạy:

```bash
python src/preprocess_data.py
```

Nó sẽ đọc `all_closed_world.npz` và `all_open_world.npz`, tách dữ liệu thành training/test, chuẩn hóa metadata và lưu file `.h5`.

### 5. Huấn luyện và đánh giá

Chạy:

```bash
python src/run_model.py
```

- Với `model_name: "var-cnn"`, project sử dụng `src/var_cnn.py`.
- Với `model_name: "df"`, project sử dụng `src/df.py`.

Kết quả:

- Trọng số model tốt nhất được lưu vào `model_weights.weights.h5`
- Dự đoán lưu vào thư mục `predictions_dir`
- Báo cáo đánh giá lưu tại `job_result.json`

## Gợi ý cấu hình

- `data_dir`: thư mục chứa dữ liệu và file `.npz`
- `predictions_dir`: nơi lưu file `*_model.npy`
- `mixture`: danh sách cấu hình mô hình kết hợp `dir`, `time`, `metadata`
- `batch_size`: kích thước batch huấn luyện
- `seq_length`: độ dài chuỗi gói tin (mặc định 5000)
- `inter_time`: chuyển đổi thời gian tuyệt đối sang khoảng thời gian giữa gói
- `scale_metadata`: chuẩn hóa metadata trước khi đưa vào mô hình

## Lưu ý

- File `config.json` là bắt buộc.
- Nếu dữ liệu chưa có `all_closed_world.npz` / `all_open_world.npz`, chạy `src/pcap_to_npz.py` trước.
- Nếu dùng GPU, đảm bảo TensorFlow đã được cài đúng phiên bản tương thích.

## Thêm

Các script trong `src/predic/` hỗ trợ kiểm tra dự đoán và dự đoán một file PCAP đơn lẻ.

---

Nếu cần, bạn có thể mở rộng README bằng ví dụ `config.json` cụ thể cho bộ dữ liệu của bạn hoặc thêm hướng dẫn chuẩn bị thư mục dữ liệu. 
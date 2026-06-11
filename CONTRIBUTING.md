# Hướng Dẫn Đóng Góp (Contributing Guide)

Cảm ơn bạn đã quan tâm đóng góp cho dự án **Network Traffic Analysis**! 

## 📋 Quy Trình Đóng Góp

### 1. Fork Repository

Click nút "Fork" trên GitHub để tạo bản copy của repository vào tài khoản của bạn.

### 2. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/Network_Traffic_Analysis.git
cd Network_Traffic_Analysis
```

### 3. Tạo Branch Mới

```bash
git checkout -b feature/YourFeatureName
# hoặc
git checkout -b fix/YourBugFix
```

### 4. Thực Hiện Thay Đổi

- Sửa code hoặc thêm tính năng mới
- Đảm bảo code tuân theo các quy chuẩn của dự án
- Thêm hoặc cập nhật tests nếu cần

### 5. Commit Thay Đổi

```bash
git add .
git commit -m "Mô tả ngắn gọn về thay đổi"
```

**Quy chuẩn Commit Message**:
- Sử dụng tiếng Anh hoặc tiếng Việt
- Bắt đầu bằng động từ: Add, Fix, Update, Remove, Refactor, etc.
- Ví dụ: "Add multi-channel Var-CNN model", "Fix PCAP parsing error"

### 6. Push lên Repository

```bash
git push origin feature/YourFeatureName
```

### 7. Tạo Pull Request

1. Vào GitHub repository của bạn
2. Click "Compare & pull request"
3. Điền tiêu đề và mô tả chi tiết về thay đổi
4. Click "Create pull request"

## 📝 Quy Chuẩn Code

### Python Style Guide

- Tuân theo [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Sử dụng 4 spaces cho indentation
- Giới hạn độ dài dòng ≤ 100 ký tự
- Thêm docstrings cho functions và classes

### Ví Dụ

```python
def process_pcap_file(pcap_path, output_dir):
    """
    Process PCAP file and extract network traffic features.
    
    Args:
        pcap_path (str): Path to PCAP file
        output_dir (str): Directory to save processed data
        
    Returns:
        dict: Dictionary containing processed features
    """
    # Implementation here
    pass
```

## 🧪 Testing

Nếu thêm tính năng mới, vui lòng:

1. Thêm unit tests
2. Chạy tests để đảm bảo không lỗi
3. Thêm integration tests nếu cần

```bash
python -m pytest src/tests/
```

## 🔍 Quy Trình Review

Sau khi tạo Pull Request:

1. Chủ repository sẽ review code
2. Có thể yêu cầu thay đổi hoặc cải tiến
3. Khi được phê duyệt, PR sẽ được merge vào main branch

## 🐛 Báo Cáo Lỗi (Bug Reports)

Nếu tìm thấy lỗi:

1. Kiểm tra [Issues](../../issues) để xem có ai đã báo cáo chưa
2. Nếu chưa, tạo Issue mới với:
   - Tiêu đề mô tả rõ lỗi
   - Mô tả chi tiết vấn đề
   - Bước tái hiện (reproduction steps)
   - Environment info (Python version, OS, etc.)
   - Log/error messages

### Ví Dụ

```
Title: PCAP processing fails with memory error

Description:
When processing large PCAP files (>500MB), the script crashes.

Steps to reproduce:
1. Run `python src/pcap_to_npz.py` with large file
2. Script runs for ~2 minutes then crashes

Environment:
- Python 3.9
- TensorFlow 2.10.0
- macOS 12.5
- 8GB RAM

Error:
MemoryError: Unable to allocate 2.50 GiB for an array...
```

## ✨ Đề Xuất Tính Năng (Feature Requests)

Có ý tưởng mới? Tạo Issue mới với:

- Tiêu đề mô tả tính năng
- Mô tả chi tiết lợi ích
- Ví dụ use case
- Implementation suggestions (nếu có)

## 📚 Tài Liệu

Nếu cải tiến documentation:

1. Update README.md
2. Thêm/update docstrings trong code
3. Thêm comments cho logic phức tạp

## 🎯 Cách Bắt Đầu

Hãy tìm Issues được gắn thẻ `good first issue` hoặc `help wanted` để bắt đầu!

## ❓ Cần Giúp Đỡ?

- Mở Discussion mới tại [GitHub Discussions](../../discussions)
- Tạo Issue với tag `question`
- Liên hệ qua email

---

**Cảm ơn vì đóng góp cho dự án!** 🎉

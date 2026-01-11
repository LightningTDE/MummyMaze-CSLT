<h1 style="text-align:center;">Mummy Maze Ultimate</h1>

<p style="text-align:center;">
  <strong>Phiên bản làm lại của Mummy Maze Deluxe với Python 3 & Pygame-CE</strong>
</p>

<p style="text-align:center;">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-ff3f3f?logo=python&labelColor=1e1e1e" />
  <img alt="Pygame" src="https://img.shields.io/badge/Pygame--CE-2.5.0-3eb489?logo=pygame&labelColor=1e1e1e" />
  <img alt="License" src="https://img.shields.io/badge/License-MIT-ff66aa?labelColor=1e1e1e" />
</p>

---

## 📖 Giới thiệu

* **Dự án:** Mummy Maze Ultimate (Mã dự án: `finalist`)
* **Môn học:** Cơ sở lập trình cho Trí tuệ nhân tạo
* **Nhóm thực hiện:** Nhóm 8 - 25TNT1

Dự án tái hiện tựa game chiến thuật tư duy **Mummy Maze** kinh điển, tích hợp các thuật toán tìm kiếm đường đi (BFS/DFS/A*) và thuật toán sinh mê cung ngẫu nhiên, mang lại trải nghiệm vừa quen thuộc vừa mới lạ.

---

## ⚙️ Phần 1: Hướng dẫn Cài đặt (Installation)

Dự án được cấu hình để chạy trên môi trường Python. Vui lòng thực hiện theo các bước sau để khởi chạy trò chơi.

### Yêu cầu hệ thống
* **Python:** Phiên bản 3.10 trở lên.
* **Git:** Để tải mã nguồn (hoặc tải file ZIP trực tiếp từ GitLab).

### Cách 1: Cài đặt thông thường (Khuyên dùng)

#### Bước 1: Tải mã nguồn
Mở Terminal hoặc Command Prompt và chạy lệnh:
```bash
git clone https://gitlab.com/locn7345/finalist.git
cd finalist
```

#### Bước 2: Thiết lập môi trường
```bash
python -m venv venv

# Kích hoạt trên Windows:
.\venv\Scripts\activate

# Kích hoạt trên macOS/Linux:
source venv/bin/activate
```

#### Bước 3: Cài đặt thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

#### Bước 4: Khởi chạy trò chơi
```bash
python start.py
```

### Cách 2: Dành cho người dùng uv (Advanced)
Nếu máy bạn đã cài đặt uv (trình quản lý gói Python tốc độ cao), dự án có sẵn uv.lock để đồng bộ môi trường nhanh chóng:
```bash
uv sync
uv run start.py
```

## 🎮 Phần 2: Hướng dẫn Sử dụng (User Manual)

### 1. Đăng nhập & Đăng ký (Login/Register)
Khi mở game, màn hình đăng nhập sẽ hiện ra. Hệ thống yêu cầu tài khoản để lưu trữ tiến độ chơi và bảng xếp hạng.

* **Đăng ký (Register):**
  * Nhập **User** (Tên đăng nhập) và **Pass** (Mật khẩu).
  * Nhấn nút **REGISTER**.
  * *Lưu ý:* Mật khẩu phải có độ dài tối thiểu 4 ký tự. Tên đăng nhập không được trùng với người khác và phải có tối thiểu 3 kí tự.

* **Đăng nhập (Login):**
  * Nhập thông tin tài khoản đã đăng ký.
  * Nhấn **LOGIN** để vào game.

### 2. Màn hình chính (Main Menu)
Sau khi đăng nhập thành công, bạn có các lựa chọn:
* **CLASSIC MODE:** Bắt đầu chơi game theo cốt truyện (Các màn chơi đi từ dễ đến khó).
* **LEADERBOARD:** Xem bảng xếp hạng thành tích của các người chơi khác (xếp hạng theo tổng thời gian hoàn thành).
* **CONTINUE:** Nhấn vào để tiếp tục tiến trình chơi đã được lưu lại (Load Game) thay vì phải chơi lại từ đầu.
* **LOG OUT:** Đăng xuất để đổi tài khoản khác.

### 3. Luật chơi & Cách chơi (Gameplay)

#### Mục tiêu
Điều khiển nhà thám hiểm đi đến ô **Cầu thang (Lối ra)** để qua màn kế tiếp mà không bị kẻ thù bắt giữ.

#### Điều khiển
* **Di chuyển:** Sử dụng các phím mũi tên **Lên / Xuống / Trái / Phải** (hoặc các nút tương ứng trên màn hình) để di chuyển nhân vật.
* **Đứng yên:** Nhấn phím **Space** (Dấu cách) để bỏ qua lượt đi (đứng im chờ quái di chuyển).

#### Cơ chế Kẻ thù & Vật phẩm
* **Kẻ thù (Xác ướp, Bọ cạp):**
  * Mỗi khi bạn đi 1 bước, kẻ thù cũng sẽ di chuyển theo quy luật tìm đường ngắn nhất đến bạn.
  * Nếu bị kẻ thù bắt được -> **GAME OVER**.
  * *Mẹo:* Bạn có thể dụ 2 con xác ướp va vào nhau, một con sẽ bị tiêu diệt giúp màn chơi dễ hơn.

* **Biểu tượng Ankh (Sự sống):**
  * Dùng để báo hiệu khả năng giải mê cung.
  * **Màu vàng:** Vẫn còn đường thắng.
  * **Màu đỏ:** Bạn đã đi vào thế bí (chết chắc dù đi hướng nào). Hãy dùng tính năng Undo hoặc Reset.

* **Vật phẩm:**
  * **Chìa khóa (Key):** Đóng vai trò như công tắc. Khi người chơi hoặc quái đi vào ô chìa khóa, các cổng/hàng rào màu tương ứng sẽ đóng hoặc mở.
  * **Bẫy:** Trò chơi kết thúc ngay lập tức nếu người chơi dẫm trúng bẫy.

### 4. Các tính năng hỗ trợ (In-game Tools)
Giao diện bên trái màn hình cung cấp bộ công cụ hỗ trợ người chơi:

* ↩️ **UNDO MOVE:** Đi sai một nước? Nhấn nút này để quay lại nước đi trước đó (Hối cờ).
* 🔄 **RESET MAZE:** Chơi lại màn hiện tại từ đầu (nếu lỡ đi vào ngõ cụt).
* 🗺️ **WORLD MAP:** Xem sơ đồ kim tự tháp để biết mình đang ở tầng nào.
* 🤖 **SHOWING SOLUTION:** (Tính năng AI) Tự động giải màn chơi nếu bạn bị bí đường. Hệ thống sẽ hiển thị từng bước đi để thắng.

### 5. Cài đặt (Options)
Nhấn vào nút **OPTIONS** để mở bảng cài đặt:
* **MUSIC:** Tăng/Giảm âm lượng nhạc nền.
* **SFX:** Tăng/Giảm âm lượng hiệu ứng âm thanh (tiếng bước chân, tiếng quái...).
* **ANKH:** Bật/Tắt hiển thị tính năng Ankh của trò chơi
* **QUIT TO MENU:** Thoát ra màn hình chính.
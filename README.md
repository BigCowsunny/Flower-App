# Flower APP

เว็บแอป Streamlit ภาษาไทยสำหรับจำแนกดอกไม้ด้วย EfficientNetB0 และแสดงชื่อวิทยาศาสตร์กับข้อมูลประกอบทางพุทธศาสนา

## เริ่มต้นใช้งานบน Windows

ต้องมี Python 3.12 แบบ 64-bit จากนั้นเปิด PowerShell ที่โฟลเดอร์นี้:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

เปิดแอปด้วย `run_app.bat` หรือรัน:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address localhost --server.port 8501
```

แล้วเปิด http://localhost:8501 ในเบราว์เซอร์

ไฟล์ EfficientNetB0 และ class mapping ที่จำเป็นอยู่ใน `models/` หากย้ายไฟล์โมเดล ให้แก้ `model_root` ใน `config/settings.json` รายละเอียดเพิ่มเติมอยู่ใน [README ภาษาไทย](README_TH.md)

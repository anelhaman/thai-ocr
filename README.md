# thai-ocr

คำสั่ง `thai-ocr` สำหรับอ่านข้อความจาก PDF และภาพภาษาไทย/อังกฤษ **แบบออฟไลน์ ใช้แค่ CPU**
ห่อ (wrap) โมเดล [OpenThai2.0-OCR-Text](https://huggingface.co/iapp/OpenThai2.0-OCR-Text) ของ iApp Technology ให้เรียกจาก terminal ได้

> A small command-line wrapper around iApp's open-weights **OpenThai2.0-OCR-Text** model: offline Thai + English printed-text OCR for PDFs and images, CPU only.

**ไม่ใช่ผลงานทางการของ iApp และไม่มีส่วนเกี่ยวข้องกับ iApp** — repo นี้มีแค่สคริปต์ห่อ ตัวโมเดลและ runtime ไม่ได้อยู่ใน repo
`install.sh` จะโหลดจาก Hugging Face เอง (ปัก revision ไว้ + ตรวจ SHA-256) ซึ่งโมเดลใช้สัญญาอนุญาต Apache-2.0 ของ iApp

## ติดตั้ง

ต้องมี [`uv`](https://docs.astral.sh/uv/) หรือ Python 3.11–3.13 (ทดสอบบน macOS Apple silicon เท่านั้น; Linux ยังไม่ได้ทดสอบ)

```bash
git clone https://github.com/anelhaman/thai-ocr.git
cd thai-ocr
./install.sh
```

`install.sh` โหลดโมเดล (~4 MB) ตรวจ checksum และสร้าง `./venv` ในโฟลเดอร์นี้ ไม่ใช้ sudo
จากนั้นทำให้เรียกได้จากทุกที่ (เลือกอย่างใดอย่างหนึ่ง):

```bash
sudo ln -sf "$PWD/bin/thai-ocr" /usr/local/bin/thai-ocr
# หรือไม่ใช้ sudo
mkdir -p ~/.local/bin && ln -sf "$PWD/bin/thai-ocr" ~/.local/bin/thai-ocr
```

## ใช้งาน

```bash
thai-ocr เอกสาร.pdf                       # พิมพ์ข้อความออกจอ
thai-ocr a.pdf b.png -o out/              # เขียน out/a.txt, out/b.txt
thai-ocr a.pdf -o out/ --json             # เพิ่ม .json: ทุกบรรทัดพร้อมกล่องและ confidence
thai-ocr a.pdf --pages 2-4 --headers      # เฉพาะบางหน้า และใส่หัว "page N"
thai-ocr a.pdf --fix-baht                 # แก้ ฿ ที่ถูกอ่านเป็น B/8 (ดูด้านล่าง)
thai-ocr a.pdf -q > out.txt               # ไม่แสดง progress ใช้กับ pipe
```

ตัวเลือก: `--dpi` (ค่าเริ่มต้น 200, ความละเอียดตอนแปลงหน้า PDF เป็นภาพ), `--threads` (ค่าเริ่มต้น min(4, จำนวนคอร์)), `-h`
ใช้ได้กับ `.pdf`, `.png`, `.jpg/.jpeg`, `.webp`, `.bmp`, `.tif/.tiff` โปรแกรม OCR **ทุกหน้า** ด้วยภาพ ไม่ได้ดึง text layer ในไฟล์ PDF

## ข้อจำกัดที่เจอจากการลองใช้จริง

ผมลองกับใบเสร็จ PDF 1 หน้า (Meta Ads) และภาพทดสอบที่เรนเดอร์เอง 4 บรรทัด เท่านั้น ตัวเลขด้านล่างจึงเป็นแค่ข้อสังเกต ไม่ใช่ benchmark

- **สัญลักษณ์ ฿ มักถูกอ่านผิด** เป็น `B` หรือ `8` — `฿114.92` กลายเป็น `8114.92` ซึ่งดูเหมือนเงินคนละจำนวน
  `--fix-baht` เป็น heuristic: `B` นำหน้าจำนวนเงิน (ทศนิยม 2 ตำแหน่ง) จะแก้เป็น ฿ เสมอ ส่วน `8` จะแก้เฉพาะเมื่อเลขที่เหลือโผล่เป็นเลขเดี่ยวที่อื่นในหน้าเดียวกัน
  รายการที่แก้จะแสดงที่ stderr **อย่าเชื่อเลขการเงินโดยไม่ตรวจยอดรวมเอง**
- ผลเป็น **ข้อความล้วนตามลำดับแถว** ไม่ใช่ตาราง/Markdown ข้อความซ้าย-ขวาในแถวเดียวกันอาจถูกต่อเป็นบรรทัดเดียว ถ้าต้องการตาราง ดู [OpenThai2.0-OCR-Markdown](https://huggingface.co/iapp/OpenThai2.0-OCR-Markdown) (ต้องใช้ GPU NVIDIA หรือ Transformers backend, ไม่รวมใน repo นี้)
- อักขระที่คล้ายกันอาจสลับ เช่น `ปี`→`บี`, `OCR`→`0CR`, ไม้โทหาย บนภาพทดสอบฟอนต์แปลก
- บน Mac ใช้ ONNX Runtime (ไม่มี OpenVINO) เวลาจริงจึงต่างจากตัวเลขของผู้พัฒนาโมเดล ใบเสร็จ 1 หน้าใช้ ~0.2 วินาที
- ลายมือและภาพถ่ายคำสั้นๆ ไม่ใช่จุดแข็งของโมเดล (ตามที่ผู้พัฒนาระบุเอง)

ตัวเลขความแม่นยำและความเร็วของโมเดล (เช่น 99.5 บนเอกสารงบประมาณ) เป็นการวัดของ iApp เอง ดูที่ [model card](https://huggingface.co/iapp/OpenThai2.0-OCR-Text)

---

## English

```bash
git clone https://github.com/anelhaman/thai-ocr.git && cd thai-ocr && ./install.sh
thai-ocr scan.pdf                    # text to stdout
thai-ocr a.pdf b.png -o out/ --json  # files + per-line boxes/confidence
thai-ocr a.pdf --fix-baht            # heuristic repair of ฿ misread as B/8
```

- Needs `uv` or Python 3.11–3.13. Tested on macOS (Apple silicon) only.
- `install.sh` downloads the model at a **pinned Hugging Face revision**, verifies SHA-256, and builds `./venv`. It never uses sudo. The model ships Python runtime code that this tool imports, which is why the revision is pinned: review the new `runtime/*.py` before bumping `HF_REV`.
- Every PDF page is rasterised (`--dpi`, default 200) and OCR'd; an embedded text layer is ignored.
- Output is plain text in reading order, not tables or Markdown.
- Observed on a one-page receipt and one synthetic image only: the baht sign is often misread (`฿114.92` → `8114.92`), so check totals yourself. Benchmarks on the model card are iApp's own measurements, not reproduced here.

## License

MIT for the code in this repository (see `LICENSE`). The model and its runtime, **OpenThai2.0-OCR-Text** © iApp Technology, are Apache-2.0 and are downloaded separately.

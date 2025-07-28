import streamlit as st
from PIL import Image, ExifTags
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="이미지 ➜ PDF 변환기", layout="centered")
st.title("📄 이미지 묶어 PDF로 저장하기")

# ------------------------------ 1) 파일 업로드 ------------------------------
uploaded_files = st.file_uploader(
    "이미지를 한꺼번에 올려 주세요 (JPEG‧PNG‧WEBP‧BMP‧TIFF 등)",
    type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
    accept_multiple_files=True,
)

# ------------------------------ 2) 정렬 기준 선택 ------------------------------
order = st.radio(
    "정렬 기준을 선택하세요",
    ["파일 이름 (오름차순)", "파일 생성일 (EXIF DateTimeOriginal, 오름차순)"],
)

def _get_exif_datetime(img: Image.Image):
    try:
        tags = {ExifTags.TAGS[k]: v for k, v in (img._getexif() or {}).items() if k in ExifTags.TAGS}
        dt_str = tags.get("DateTimeOriginal") or tags.get("DateTime")
        return datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S") if dt_str else None
    except Exception:
        return None

def _sort_files(files, mode):
    if mode == "파일 이름 (오름차순)":
        return sorted(files, key=lambda f: f.name.lower())
    info = [(f, _get_exif_datetime(Image.open(f))) for f in files]
    # EXIF 시간 없으면 마지막으로 보내고, 업로드 순서 유지
    return [f for f, _ in sorted(info, key=lambda x: (x[1] is None, x[1] or datetime.max))]

# ------------------------------ 3) PDF 이름 입력 ------------------------------
today_base = datetime.now().strftime("%Y%m%d") + "001"
pdf_base_name = st.text_input(
    "💾 저장할 PDF 이름을 입력하세요 (확장자 제외)",
    value=today_base,
    key="pdf_name_input",
)
pdf_base_name = pdf_base_name.strip() or today_base         # 비어 있으면 기본값 사용
if not pdf_base_name.lower().endswith(".pdf"):
    pdf_filename = f"{pdf_base_name}.pdf"
else:
    pdf_filename = pdf_base_name

# ------------------------------ 4) 미리보기 & 변환 ------------------------------
if uploaded_files:
    sorted_files = _sort_files(uploaded_files, order)
    st.subheader("📑 변환 미리보기")
    for i, f in enumerate(sorted_files, 1):
        st.write(f"**{i}. {f.name}**")
        st.image(f, use_container_width=True)

    if st.button("👉 PDF 만들기"):
        images = []
        for f in sorted_files:
            img = Image.open(f)
            if img.mode != "RGB":
                img = img.convert("RGB")
            images.append(img)

        if images:
            pdf_bytes = BytesIO()
            images[0].save(pdf_bytes, format="PDF", save_all=True, append_images=images[1:])
            pdf_bytes.seek(0)
            st.success(f"✅ '{pdf_filename}' 생성 완료!")

            st.download_button(
                "📥 PDF 다운로드",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf",
            )
else:
    st.info("왼쪽 상단의 *파일 선택* 버튼을 눌러 이미지를 먼저 업로드해 주세요.")

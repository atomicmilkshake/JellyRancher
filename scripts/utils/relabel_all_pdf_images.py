import fitz  # PyMuPDF
from pathlib import Path
import os
import shutil

def restore_and_relabel_all_images(pdf_path, images_dir):
    """
    Re-extract all images from PDF with complete labeling.
    """
    # Create new output directory
    images_path = Path(images_dir + "_labeled")
    if images_path.exists():
        print(f"Clearing existing labeled directory...")
        for file in images_path.glob("*"):
            file.unlink()
    else:
        images_path.mkdir(parents=True, exist_ok=True)

    # Open PDF and extract
    pdf_document = fitz.open(pdf_path)

    # Complete labeling scheme for ALL 23 images
    image_labels = {
        (1, 1): "Page1_HeaderLogo_Grace_Clinic",
        (1, 2): "Page1_Procedure_Header_Image",
        (2, 1): "Page2_HeaderLogo_Grace_Clinic",
        (2, 2): "Endoscopy_01_Hiatal_Hernia_Main",
        (2, 3): "Endoscopy_01_Hiatal_Hernia_Thumbnail",
        (2, 4): "Endoscopy_02_Gastric_Tumor_Incisura_Main",
        (2, 5): "Endoscopy_02_Gastric_Tumor_Incisura_Thumbnail",
        (2, 6): "Endoscopy_03_Normal_Mucosa_Site1_Main",
        (2, 7): "Endoscopy_03_Normal_Mucosa_Site1_Thumbnail",
        (2, 8): "Endoscopy_04_Normal_Mucosa_Site2_Main",
        (2, 9): "Endoscopy_04_Normal_Mucosa_Site2_Thumbnail",
        (2, 10): "Endoscopy_05_Normal_Mucosa_Site3_Main",
        (2, 11): "Endoscopy_05_Normal_Mucosa_Site3_Thumbnail",
        (2, 12): "Endoscopy_06_Normal_Mucosa_Site4_Main",
        (2, 13): "Endoscopy_06_Normal_Mucosa_Site4_Thumbnail",
        (2, 14): "Endoscopy_07_Normal_Mucosa_Site5_Main",
        (2, 15): "Endoscopy_07_Normal_Mucosa_Site5_Thumbnail",
        (2, 16): "Endoscopy_08_Normal_Mucosa_Site6_Main",
        (2, 17): "Endoscopy_08_Normal_Mucosa_Site6_Thumbnail",
        (2, 18): "Endoscopy_09_Normal_Mucosa_Site7_Main",
        (2, 19): "Endoscopy_09_Normal_Mucosa_Site7_Thumbnail",
        (3, 1): "Page3_HeaderLogo_Grace_Clinic",
        (3, 2): "Page3_Signature_or_Footer_Image"
    }

    image_count = 0

    # Extract and label all images
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # Get label
            page_img_key = (page_num + 1, img_index + 1)
            if page_img_key in image_labels:
                label = image_labels[page_img_key]
            else:
                label = f"Page{page_num + 1}_Image{img_index + 1}_Unknown"

            # Save with descriptive name
            image_filename = f"{label}.{image_ext}"
            image_filepath = images_path / image_filename

            with open(image_filepath, "wb") as img_file:
                img_file.write(image_bytes)

            image_count += 1
            print(f"Extracted: {image_filename} ({len(image_bytes)} bytes)")

    pdf_document.close()
    print(f"\n✓ Complete! {image_count} images extracted and labeled.")
    print(f"✓ Images saved to: {images_path}")

    # Print summary
    print("\n=== IMAGE SUMMARY ===")
    print("Clinical Endoscopy Images:")
    print("  • 1 Hiatal Hernia view (with thumbnail)")
    print("  • 1 Gastric Tumor at Incisura (with thumbnail)")
    print("  • 7 Normal Stomach Mucosa sites (each with thumbnail)")
    print("Document Elements:")
    print("  • 3 Header logos")
    print("  • 1 Footer/signature image")
    print(f"Total: {image_count} images")

if __name__ == "__main__":
    pdf_file = r"F:\OneDrive\DOWNLOADS\Scan - EGD - Nov 7, 2025.pdf"
    images_dir = r"F:\OneDrive\DOWNLOADS\Scan - EGD - Nov 7, 2025_images"

    restore_and_relabel_all_images(pdf_file, images_dir)
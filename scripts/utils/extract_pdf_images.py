import fitz  # PyMuPDF
import os
from pathlib import Path

def extract_images_from_pdf(pdf_path, output_dir):
    """
    Extract all images from a PDF file and save them to the output directory.
    """
    # Open the PDF
    pdf_document = fitz.open(pdf_path)

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    image_count = 0

    # Iterate through each page
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)

        # Get images on the page
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # Save the image
            image_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
            image_filepath = output_path / image_filename

            with open(image_filepath, "wb") as img_file:
                img_file.write(image_bytes)

            image_count += 1
            print(f"Extracted: {image_filename}")

    pdf_document.close()
    print(f"\nExtraction complete! {image_count} images extracted to {output_dir}")

if __name__ == "__main__":
    # PDF file path
    pdf_file = r"F:\OneDrive\DOWNLOADS\Scan - EGD - Nov 7, 2025.pdf"

    # Output directory (same as PDF directory with _images suffix)
    pdf_path_obj = Path(pdf_file)
    output_directory = pdf_path_obj.parent / f"{pdf_path_obj.stem}_images"

    extract_images_from_pdf(pdf_file, str(output_directory))
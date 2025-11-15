import fitz  # PyMuPDF
from pathlib import Path
import re

def extract_text_and_images_info(pdf_path):
    """
    Extract text and image information from PDF to correlate images with their labels.
    """
    pdf_document = fitz.open(pdf_path)

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        print(f"\n=== Page {page_num + 1} ===")

        # Extract text
        text = page.get_text()
        print("Text content:")
        print(text[:500] + "..." if len(text) > 500 else text)

        # Get images on the page
        image_list = page.get_images(full=True)
        print(f"Images on page: {len(image_list)}")

        for img_index, img in enumerate(image_list):
            xref = img[0]
            # Get image position (bbox)
            img_rect = page.get_image_bbox(img)
            print(f"  Image {img_index + 1}: bbox = {img_rect}")

    pdf_document.close()

def find_figure_captions(pdf_path):
    """
    Search for figure captions in the PDF text.
    """
    pdf_document = fitz.open(pdf_path)
    captions = []

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text()

        # Look for patterns like "Figure X", "Fig. X", etc.
        figure_patterns = [
            r'Figure\s+(\d+)[:\.\s]*(.*?)(?=\n|$)',
            r'Fig\.\s*(\d+)[:\.\s]*(.*?)(?=\n|$)',
            r'FIGURE\s+(\d+)[:\.\s]*(.*?)(?=\n|$)',
            r'FIG\.\s*(\d+)[:\.\s]*(.*?)(?=\n|$)'
        ]

        for pattern in figure_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                fig_num, caption = match
                captions.append({
                    'page': page_num + 1,
                    'figure': int(fig_num),
                    'caption': caption.strip(),
                    'full_text': f"Figure {fig_num}: {caption.strip()}"
                })

    pdf_document.close()
    return captions

if __name__ == "__main__":
    pdf_file = r"F:\OneDrive\DOWNLOADS\Scan - EGD - Nov 7, 2025.pdf"

    print("Analyzing PDF for figure captions...")
    captions = find_figure_captions(pdf_file)

    print(f"\nFound {len(captions)} figure captions:")
    for cap in captions:
        print(f"Page {cap['page']}: {cap['full_text']}")

    print("\nDetailed page analysis:")
    extract_text_and_images_info(pdf_file)
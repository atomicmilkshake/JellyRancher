import fitz  # PyMuPDF
from pathlib import Path
import os
import re

def analyze_pdf_images(pdf_path, images_dir):
    """
    Analyze PDF and rename extracted images based on context and findings.
    """
    pdf_document = fitz.open(pdf_path)

    # Define labels based on the medical report content
    image_labels = {
        1: {  # Page 1
            0: "Patient_Header_Logo",  # Small logo
            1: "Procedure_Header_Image"  # Another header image
        },
        2: {  # Page 2 - Endoscopy images
            0: "Header_Logo_Page2",
            1: "Hiatal_Hernia_View",
            2: "Hiatal_Hernia_Thumbnail",
            3: "Gastric_Tumor_Incisura",
            4: "Gastric_Tumor_Thumbnail",
            5: "Normal_Stomach_Mucosa_1",
            6: "Normal_Stomach_Mucosa_1_Thumbnail",
            7: "Normal_Stomach_Mucosa_2",
            8: "Normal_Stomach_Mucosa_2_Thumbnail",
            9: "Normal_Stomach_Mucosa_3",
            10: "Normal_Stomach_Mucosa_3_Thumbnail",
            11: "Normal_Stomach_Mucosa_4",
            12: "Normal_Stomach_Mucosa_4_Thumbnail",
            13: "Normal_Stomach_Mucosa_5",
            14: "Normal_Stomach_Mucosa_5_Thumbnail",
            15: "Normal_Stomach_Mucosa_6",
            16: "Normal_Stomach_Mucosa_6_Thumbnail",
            17: "Normal_Stomach_Mucosa_7",
            18: "Normal_Stomach_Mucosa_7_Thumbnail"
        },
        3: {  # Page 3
            0: "Header_Logo_Page3",
            1: "Diagnosis_Codes_Image"
        }
    }

    renamed_count = 0

    # Rename existing images
    for page_num in range(1, 4):  # Pages 1-3
        if page_num in image_labels:
            for img_index in range(len(image_labels[page_num])):
                old_filename = f"page_{page_num}_img_{img_index + 1}.jpeg"
                old_path = Path(images_dir) / old_filename

                if old_path.exists():
                    new_label = image_labels[page_num].get(img_index, f"Unknown_Image_{img_index + 1}")
                    new_filename = f"page_{page_num}_{new_label}.jpeg"
                    new_path = Path(images_dir) / new_filename

                    os.rename(old_path, new_path)
                    print(f"Renamed: {old_filename} -> {new_filename}")
                    renamed_count += 1

    print(f"\nRenaming complete! {renamed_count} images renamed.")

    # Print summary of findings for context
    print("\n=== MEDICAL FINDINGS SUMMARY ===")
    print("This appears to be an Upper GI Endoscopy report with the following key findings:")
    print("• Small hiatal hernia")
    print("• Likely malignant gastric tumor at the incisura (biopsied and tattooed)")
    print("• Normal mucosa found throughout the stomach (multiple biopsy sites)")
    print("• Recommendation for colonoscopy and surgical referral")

    pdf_document.close()

if __name__ == "__main__":
    pdf_file = r"F:\OneDrive\DOWNLOADS\Scan - EGD - Nov 7, 2025.pdf"
    images_dir = r"F:\OneDrive\DOWNLOADS\Scan - EGD - Nov 7, 2025_images"

    analyze_pdf_images(pdf_file, images_dir)
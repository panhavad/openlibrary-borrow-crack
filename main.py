import json
import base64
import os
from datetime import datetime
from PIL import Image
from tqdm import tqdm
from PyPDF2 import PdfMerger
import shutil


def extract_images_from_har(filename):
    # Open the HAR file and load its contents as JSON data
    with open(filename, 'r') as f:
        har_data = json.load(f)

    # Create a subfolder to store the images
    folder_name = main_output_dir + "/" + \
        datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    os.mkdir(folder_name)

    # Initialize counters for the number of images and their total size
    num_images = 0
    total_size = 0

    # Loop through all the entries in the HAR file
    for entry in tqdm(har_data['log']['entries'], desc="Extracting images"):
        # Check if the entry is for an image (by checking the content type)
        if 'image' in entry['response']['content']['mimeType']:
            # Get the image data and decode it from base64
            image_data = entry['response']['content']['text']
            image_data = base64.b64decode(image_data)

            # Check the size of the image
            if len(image_data) < 20 * 1024:  # 20kb in bytes
                # Delete the image file if it exists
                filename = 'image{}.jpg'.format(
                    entry['startedDateTime'].replace(':', '_'))
                if os.path.exists(filename):
                    os.remove(filename)
            else:
                # Save the image data to a file
                with open(os.path.join(folder_name, 'image{}.jpg'.format(entry['startedDateTime'].replace(':', '_'))), 'wb') as img_file:
                    img_file.write(image_data)
                num_images += 1
                total_size += len(image_data)

    # Return the folder name, number of images, and total size
    return folder_name, num_images, total_size


def create_pdf_from_images(folder_name):
    tmp_dir = folder_name + "/tmp"
    # Check whether the specified path exists or not
    if (os.path.exists(tmp_dir)):
        shutil.rmtree(tmp_dir)
    os.mkdir(tmp_dir)
    # Get the list of image files
    image_files = sorted(
        [f for f in os.listdir(folder_name) if f.endswith('.jpg')])

    # Create a list of PDFs
    pdf_files = []
    i = 0
    pbar = tqdm(total=len(image_files))
    pbar.set_description("Creating PDF")
    while i < len(image_files):
        pdf_file = os.path.join(
            tmp_dir, '{}-{}.pdf'.format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), i))
        with Image.open(os.path.join(folder_name, image_files[i])) as img:
            img.save(pdf_file, "PDF", resolution=100.0, save_all=True)
            for image_file in image_files[i+1:i+50]:
                with Image.open(os.path.join(folder_name, image_file)) as img:
                    img.save(pdf_file, "PDF", resolution=100.0,
                             save_all=True, append=True)
                pbar.update(1)
        pdf_files.append(pdf_file)
        i += 50

    # Merge the PDFs
    merged_pdf_file = os.path.join(folder_name, '{}.pdf'.format(
        datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
    merger = PdfMerger()
    for pdf_file in pdf_files:
        merger.append(pdf_file)
        pbar.update(1)
    merger.write(merged_pdf_file)
    merger.close()
    pbar.close()

    # Delete the temporary PDFs
    shutil.rmtree(tmp_dir)

    # Get the file size of the merged PDF file
    merged_pdf_file_size = os.path.getsize(merged_pdf_file)

    return merged_pdf_file, merged_pdf_file_size


if __name__ == '__main__':
    main_output_dir = "output"
    # Check whether the specified path exists or not
    if not os.path.exists(main_output_dir):
        os.mkdir(main_output_dir)

    har_file_name = input("Enter the filename of the HAR file: ")
    folder_name, num_images, total_size = extract_images_from_har(
        har_file_name)
    create_pdf_from_images(folder_name)
